"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

type ThreadContextValue = {
  threadId: string;
  setThreadId: (id: string) => void;
  newThread: () => string;
  ready: boolean;
};

const ThreadContext = createContext<ThreadContextValue | null>(null);

function createThreadId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `thread-${Date.now()}`;
}

const BOOTSTRAP_THREAD_ID = "bootstrap";

export function ThreadProvider({ children }: { children: React.ReactNode }) {
  const [threadId, setThreadId] = useState(BOOTSTRAP_THREAD_ID);
  const ready = threadId !== BOOTSTRAP_THREAD_ID;

  useEffect(() => {
    setThreadId(createThreadId());
  }, []);

  const newThread = useCallback(() => {
    const id = createThreadId();
    setThreadId(id);
    return id;
  }, []);

  const value = useMemo(
    () => ({ threadId, setThreadId, newThread, ready }),
    [threadId, newThread, ready],
  );

  return <ThreadContext.Provider value={value}>{children}</ThreadContext.Provider>;
}

export function useThread() {
  const ctx = useContext(ThreadContext);
  if (!ctx) throw new Error("useThread must be used within ThreadProvider");
  return ctx;
}
