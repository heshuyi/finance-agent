import {
  AbstractAgent,
  BaseEvent,
  EventType,
  Message,
  RunAgentInput,
  compactEvents,
} from "@ag-ui/client";
import {
  AgentRunnerConnectRequest,
  AgentRunnerIsRunningRequest,
  AgentRunnerRunRequest,
  AgentRunnerStopRequest,
  InMemoryAgentRunner,
  type InMemoryThread,
} from "@copilotkit/runtime/v2";
import { finalizeRunEvents } from "@copilotkit/shared";
import { Observable, ReplaySubject } from "rxjs";

import {
  clearAllChatThreads,
  loadThreadRuns,
  listThreadSummaries,
  persistHistoricRun,
  type PersistedRun,
} from "./chat-db";

type HistoricRun = PersistedRun;

type ThreadStore = {
  threadId: string;
  subject: ReplaySubject<BaseEvent> | null;
  isRunning: boolean;
  currentRunId: string | null;
  historicRuns: HistoricRun[];
  agent: AbstractAgent | null;
  runSubject: ReplaySubject<BaseEvent> | null;
  stopRequested: boolean;
  currentEvents: BaseEvent[] | null;
  hydrated: boolean;
};

const THREAD_STORE = new Map<string, ThreadStore>();

function createStore(threadId: string): ThreadStore {
  const store: ThreadStore = {
    threadId,
    subject: null,
    isRunning: false,
    currentRunId: null,
    historicRuns: [],
    agent: null,
    runSubject: null,
    stopRequested: false,
    currentEvents: null,
    hydrated: false,
  };
  THREAD_STORE.set(threadId, store);
  return store;
}

function ensureStore(threadId: string): ThreadStore {
  let store = THREAD_STORE.get(threadId);
  if (!store) {
    store = createStore(threadId);
  }
  if (!store.hydrated) {
    store.historicRuns = loadThreadRuns(threadId);
    store.hydrated = true;
  }
  return store;
}

function pushHistoricRun(store: ThreadStore, run: HistoricRun): void {
  store.historicRuns.push(run);
  persistHistoricRun(run);
}

/**
 * SQLite 持久化的 CopilotKit AgentRunner。
 * 继承 InMemoryAgentRunner 以通过 CopilotKit threads API 的 instanceof 检查。
 */
export class SqliteAgentRunner extends InMemoryAgentRunner {
  run(request: AgentRunnerRunRequest): Observable<BaseEvent> {
    const store = ensureStore(request.threadId);

    if (store.isRunning) {
      throw new Error("Thread already running");
    }

    store.isRunning = true;
    store.currentRunId = request.input.runId;
    store.agent = request.agent;
    store.stopRequested = false;

    const seenMessageIds = new Set<string>();
    const currentRunEvents: BaseEvent[] = [];
    store.currentEvents = currentRunEvents;

    const historicMessageIds = new Set<string>();
    for (const run of store.historicRuns) {
      for (const event of run.events) {
        if ("messageId" in event && typeof event.messageId === "string") {
          historicMessageIds.add(event.messageId);
        }
        if (event.type === EventType.RUN_STARTED) {
          const messages = (event as { input?: { messages?: Message[] } }).input?.messages ?? [];
          for (const message of messages) {
            historicMessageIds.add(message.id);
          }
        }
      }
    }

    const nextSubject = new ReplaySubject<BaseEvent>(Infinity);
    const prevSubject = store.subject;
    store.subject = nextSubject;
    const runSubject = new ReplaySubject<BaseEvent>(Infinity);
    store.runSubject = runSubject;

    const runAgent = async () => {
      const parentRunId =
        store.historicRuns[store.historicRuns.length - 1]?.runId ?? null;

      try {
        await request.agent.runAgent(request.input, {
          onEvent: ({ event }) => {
            let processedEvent = event;
            if (event.type === EventType.RUN_STARTED) {
              const runStartedEvent = event as BaseEvent & {
                input?: RunAgentInput;
              };
              if (!runStartedEvent.input) {
                const sanitizedMessages = request.input.messages
                  ? request.input.messages.filter(
                      (message) => !historicMessageIds.has(message.id),
                    )
                  : undefined;
                const updatedInput = {
                  ...request.input,
                  ...(sanitizedMessages !== undefined
                    ? { messages: sanitizedMessages }
                    : {}),
                };
                processedEvent = {
                  ...runStartedEvent,
                  input: updatedInput,
                } as BaseEvent;
              }
            }
            runSubject.next(processedEvent);
            nextSubject.next(processedEvent);
            currentRunEvents.push(processedEvent);
          },
          onNewMessage: ({ message }) => {
            if (!seenMessageIds.has(message.id)) {
              seenMessageIds.add(message.id);
            }
          },
          onRunStartedEvent: () => {
            if (request.input.messages) {
              for (const message of request.input.messages) {
                if (!seenMessageIds.has(message.id)) {
                  seenMessageIds.add(message.id);
                }
              }
            }
          },
        });

        const appendedEvents = finalizeRunEvents(currentRunEvents, {
          stopRequested: store.stopRequested,
        });
        for (const event of appendedEvents) {
          runSubject.next(event);
          nextSubject.next(event);
        }

        if (store.currentRunId) {
          const compactedEvents = compactEvents(currentRunEvents);
          pushHistoricRun(store, {
            threadId: request.threadId,
            runId: store.currentRunId,
            agentId: request.agent.agentId ?? "default",
            parentRunId,
            events: compactedEvents,
            messages: Array.isArray(request.agent.messages)
              ? [...request.agent.messages]
              : [],
            createdAt: Date.now(),
          });
        }

        this.resetRunningStore(store);
        runSubject.complete();
        nextSubject.complete();
      } catch (error) {
        const interruptionMessage =
          error instanceof Error ? error.message : String(error);
        const appendedEvents = finalizeRunEvents(currentRunEvents, {
          stopRequested: store.stopRequested,
          interruptionMessage,
        });
        for (const event of appendedEvents) {
          runSubject.next(event);
          nextSubject.next(event);
        }

        if (store.currentRunId && currentRunEvents.length > 0) {
          const compactedEvents = compactEvents(currentRunEvents);
          pushHistoricRun(store, {
            threadId: request.threadId,
            runId: store.currentRunId,
            agentId: request.agent.agentId ?? "default",
            parentRunId,
            events: compactedEvents,
            messages: Array.isArray(request.agent.messages)
              ? [...request.agent.messages]
              : [],
            createdAt: Date.now(),
          });
        }

        this.resetRunningStore(store);
        runSubject.complete();
        nextSubject.complete();
      }
    };

    if (prevSubject) {
      prevSubject.subscribe({
        next: (e) => nextSubject.next(e),
        error: (err) => nextSubject.error(err),
        complete: () => {},
      });
    }

    void runAgent();
    return runSubject.asObservable();
  }

  connect(request: AgentRunnerConnectRequest): Observable<BaseEvent> {
    const store = ensureStore(request.threadId);
    const connectionSubject = new ReplaySubject<BaseEvent>(Infinity);

    const allHistoricEvents: BaseEvent[] = [];
    for (const run of store.historicRuns) {
      allHistoricEvents.push(...run.events);
    }
    const compactedEvents = compactEvents(allHistoricEvents);
    const emittedMessageIds = new Set<string>();

    for (const event of compactedEvents) {
      connectionSubject.next(event);
      if ("messageId" in event && typeof event.messageId === "string") {
        emittedMessageIds.add(event.messageId);
      }
    }

    if (store.subject && (store.isRunning || store.stopRequested)) {
      store.subject.subscribe({
        next: (event) => {
          if (
            "messageId" in event &&
            typeof event.messageId === "string" &&
            emittedMessageIds.has(event.messageId)
          ) {
            return;
          }
          connectionSubject.next(event);
        },
        complete: () => connectionSubject.complete(),
        error: (err) => connectionSubject.error(err),
      });
    } else {
      connectionSubject.complete();
    }

    return connectionSubject.asObservable();
  }

  isRunning(request: AgentRunnerIsRunningRequest): Promise<boolean> {
    const store = THREAD_STORE.get(request.threadId);
    return Promise.resolve(store?.isRunning ?? false);
  }

  stop(request: AgentRunnerStopRequest): Promise<boolean | undefined> {
    const store = THREAD_STORE.get(request.threadId);
    if (!store || !store.isRunning) {
      return Promise.resolve(false);
    }
    if (store.stopRequested) {
      return Promise.resolve(false);
    }

    store.stopRequested = true;
    store.isRunning = false;
    const agent = store.agent;
    if (!agent) {
      store.stopRequested = false;
      store.isRunning = false;
      return Promise.resolve(false);
    }

    try {
      agent.abortRun();
      return Promise.resolve(true);
    } catch (error) {
      console.error("Failed to abort agent run", error);
      store.stopRequested = false;
      store.isRunning = true;
      return Promise.resolve(false);
    }
  }

  listThreads(): InMemoryThread[] {
    return listThreadSummaries().map((row) => ({
      id: row.id,
      name: row.name,
      agentId: row.agentId,
      organizationId: "",
      createdById: "",
      archived: false,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    }));
  }

  getThreadMessages(threadId: string): Message[] {
    const store = ensureStore(threadId);
    if (store.historicRuns.length === 0) {
      return [];
    }
    return store.historicRuns[store.historicRuns.length - 1].messages;
  }

  getThreadEvents(threadId: string): BaseEvent[] {
    const store = ensureStore(threadId);
    if (store.historicRuns.length === 0) {
      return [];
    }
    const all: BaseEvent[] = [];
    for (const run of store.historicRuns) {
      all.push(...run.events);
    }
    return compactEvents(all);
  }

  getThreadState(threadId: string): Record<string, unknown> | null {
    const events = this.getThreadEvents(threadId);
    for (let i = events.length - 1; i >= 0; i--) {
      const event = events[i];
      if (event.type === EventType.STATE_SNAPSHOT) {
        const snapshot = (event as { snapshot?: unknown }).snapshot;
        if (snapshot && typeof snapshot === "object") {
          return snapshot as Record<string, unknown>;
        }
        return null;
      }
    }
    return null;
  }

  clearThreads(): void {
    THREAD_STORE.clear();
    clearAllChatThreads();
  }

  private resetRunningStore(store: ThreadStore): void {
    store.currentEvents = null;
    store.currentRunId = null;
    store.agent = null;
    store.runSubject = null;
    store.stopRequested = false;
    store.isRunning = false;
  }
}
