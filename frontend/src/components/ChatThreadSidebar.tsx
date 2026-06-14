"use client";

import { useCallback, useEffect, useState } from "react";
import { useThread } from "@/context/thread-context";

export type ChatThread = {
  id: string;
  name?: string | null;
  agentId?: string;
  updatedAt?: string;
  createdAt?: string;
};

const AGENT_ID = "finteam_main";

function formatTime(iso?: string) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function ChatThreadSidebar() {
  const { threadId, setThreadId, newThread } = useThread();
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`/api/copilotkit/threads?agentId=${AGENT_ID}`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error(`加载失败 (${res.status})`);
      const data = (await res.json()) as { threads?: ChatThread[] };
      setThreads(data.threads ?? []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载历史对话失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 15000);
    const onFocus = () => refresh();
    window.addEventListener("focus", onFocus);
    window.addEventListener("finteam:task-completed", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("finteam:task-completed", refresh);
    };
  }, [refresh, threadId]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-zinc-500">CopilotKit 会话线程（SQLite 本地库）</p>
        <button
          type="button"
          onClick={() => {
            newThread();
            void refresh();
          }}
          className="rounded-md bg-emerald-600 px-2 py-1 text-[10px] font-medium text-white hover:bg-emerald-700"
        >
          新对话
        </button>
      </div>

      {loading && <p className="text-xs text-zinc-400">加载中…</p>}
      {error && <p className="text-xs text-red-500">{error}</p>}
      {!loading && !error && threads.length === 0 && (
        <p className="text-xs text-zinc-400">暂无历史对话，发送消息后将出现在此</p>
      )}

      <ul className="max-h-[28vh] space-y-2 overflow-y-auto lg:max-h-[50vh]">
        {threads.map((thread) => (
          <li key={thread.id}>
            <button
              type="button"
              onClick={() => setThreadId(thread.id)}
              className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                thread.id === threadId
                  ? "border-emerald-300 bg-emerald-50"
                  : "border-zinc-100 hover:border-emerald-200 hover:bg-emerald-50/50"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm font-medium text-zinc-800">
                  {thread.name || `对话 ${thread.id.slice(0, 8)}`}
                </span>
                {thread.id === threadId && (
                  <span className="shrink-0 text-[10px] text-emerald-700">当前</span>
                )}
              </div>
              <p className="mt-1 text-[10px] text-zinc-400">
                {formatTime(thread.updatedAt)}
              </p>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
