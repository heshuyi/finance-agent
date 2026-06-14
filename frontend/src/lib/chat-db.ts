import fs from "node:fs";
import path from "node:path";

import Database from "better-sqlite3";
import type { BaseEvent, Message } from "@ag-ui/client";

const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS chat_threads (
    thread_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_runs (
    run_id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    parent_run_id TEXT,
    events_json TEXT NOT NULL,
    messages_json TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL,
    FOREIGN KEY (thread_id) REFERENCES chat_threads(thread_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_runs_thread ON chat_runs(thread_id, created_at_ms);
CREATE INDEX IF NOT EXISTS idx_chat_threads_updated ON chat_threads(updated_at DESC);
`;

export type PersistedRun = {
  threadId: string;
  runId: string;
  agentId: string;
  parentRunId: string | null;
  events: BaseEvent[];
  messages: Message[];
  createdAt: number;
};

export type ThreadSummaryRow = {
  id: string;
  name: string | null;
  agentId: string;
  createdAt: string;
  updatedAt: string;
};

type ChatDbGlobal = {
  db?: Database.Database;
};

const globalStore = globalThis as typeof globalThis & { __finteamChatDb?: ChatDbGlobal };

function resolveDbPath(): string {
  const raw = process.env.FINTEAM_DB_PATH;
  if (raw) {
    return path.isAbsolute(raw) ? raw : path.resolve(process.cwd(), raw);
  }
  return path.resolve(process.cwd(), "../data/finteam.db");
}

export function getChatDb(): Database.Database {
  if (!globalStore.__finteamChatDb) {
    globalStore.__finteamChatDb = {};
  }
  if (globalStore.__finteamChatDb.db) {
    return globalStore.__finteamChatDb.db;
  }

  const dbPath = resolveDbPath();
  fs.mkdirSync(path.dirname(dbPath), { recursive: true });
  const db = new Database(dbPath);
  db.pragma("foreign_keys = ON");
  db.exec(SCHEMA_SQL);
  globalStore.__finteamChatDb.db = db;
  return db;
}

function deriveThreadName(messages: Message[]): string | null {
  const user = messages.find((m) => m.role === "user");
  if (user && "content" in user && typeof user.content === "string" && user.content.trim()) {
    const text = user.content.trim();
    return text.length > 40 ? `${text.slice(0, 40)}…` : text;
  }
  return null;
}

export function persistHistoricRun(run: PersistedRun): void {
  const db = getChatDb();
  const now = new Date(run.createdAt).toISOString();
  const upsertThread = db.prepare(`
    INSERT INTO chat_threads (thread_id, agent_id, name, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(thread_id) DO UPDATE SET
      agent_id = excluded.agent_id,
      updated_at = excluded.updated_at,
      name = COALESCE(chat_threads.name, excluded.name)
  `);

  const insertRun = db.prepare(`
    INSERT INTO chat_runs (
      run_id, thread_id, agent_id, parent_run_id, events_json, messages_json, created_at_ms
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(run_id) DO UPDATE SET
      events_json = excluded.events_json,
      messages_json = excluded.messages_json
  `);

  const tx = db.transaction(() => {
    const existing = db
      .prepare("SELECT name FROM chat_threads WHERE thread_id = ?")
      .get(run.threadId) as { name: string | null } | undefined;
    const name = existing?.name ?? deriveThreadName(run.messages);
    upsertThread.run(run.threadId, run.agentId, name, now, now);
    insertRun.run(
      run.runId,
      run.threadId,
      run.agentId,
      run.parentRunId,
      JSON.stringify(run.events),
      JSON.stringify(run.messages),
      run.createdAt,
    );
  });
  tx();
}

export function loadThreadRuns(threadId: string): PersistedRun[] {
  const db = getChatDb();
  const rows = db
    .prepare(
      `SELECT run_id, thread_id, agent_id, parent_run_id, events_json, messages_json, created_at_ms
       FROM chat_runs WHERE thread_id = ? ORDER BY created_at_ms ASC`,
    )
    .all(threadId) as Array<{
    run_id: string;
    thread_id: string;
    agent_id: string;
    parent_run_id: string | null;
    events_json: string;
    messages_json: string;
    created_at_ms: number;
  }>;

  return rows.map((row) => ({
    threadId: row.thread_id,
    runId: row.run_id,
    agentId: row.agent_id,
    parentRunId: row.parent_run_id,
    events: JSON.parse(row.events_json) as BaseEvent[],
    messages: JSON.parse(row.messages_json) as Message[],
    createdAt: row.created_at_ms,
  }));
}

export function listThreadSummaries(agentId?: string): ThreadSummaryRow[] {
  const db = getChatDb();
  const rows = agentId
    ? (db
        .prepare(
          `SELECT thread_id, agent_id, name, created_at, updated_at
           FROM chat_threads WHERE agent_id = ? ORDER BY updated_at DESC`,
        )
        .all(agentId) as Array<{
        thread_id: string;
        agent_id: string;
        name: string | null;
        created_at: string;
        updated_at: string;
      }>)
    : (db
        .prepare(
          `SELECT thread_id, agent_id, name, created_at, updated_at
           FROM chat_threads ORDER BY updated_at DESC`,
        )
        .all() as Array<{
        thread_id: string;
        agent_id: string;
        name: string | null;
        created_at: string;
        updated_at: string;
      }>);

  return rows.map((row) => ({
    id: row.thread_id,
    name: row.name,
    agentId: row.agent_id,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  }));
}

export function clearAllChatThreads(): void {
  const db = getChatDb();
  db.exec("DELETE FROM chat_runs; DELETE FROM chat_threads;");
}
