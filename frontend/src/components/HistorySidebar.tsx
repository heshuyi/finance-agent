"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchTasks, type TaskSummary } from "@/lib/api";

const INTENT_LABELS: Record<string, string> = {
  buy_analysis: "买入研判",
  sell_analysis: "卖出研判",
  verify_only: "验真",
  data_query: "数据查询",
  general: "通用",
};

const PHASE_LABELS: Record<string, string> = {
  done: "完成",
  cancelled: "已取消",
};

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

export function HistorySidebar() {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchTasks(30)
      .then((data) => {
        if (!cancelled) setTasks(data.tasks);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <aside className="w-full rounded-xl border border-zinc-200 bg-white p-4 shadow-sm lg:w-72 lg:shrink-0">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-zinc-900">历史研判</h2>
        <span className="text-[10px] text-zinc-400">M3</span>
      </div>
      <p className="mt-1 text-xs text-zinc-500">完整研判结束后自动入库</p>

      {loading && <p className="mt-4 text-xs text-zinc-400">加载中…</p>}
      {error && <p className="mt-4 text-xs text-red-500">{error}</p>}

      {!loading && !error && tasks.length === 0 && (
        <p className="mt-4 text-xs text-zinc-400">暂无历史记录</p>
      )}

      <ul className="mt-3 max-h-[60vh] space-y-2 overflow-y-auto">
        {tasks.map((task) => (
          <li key={task.task_id}>
            <Link
              href={`/tasks/${task.task_id}`}
              className="block rounded-lg border border-zinc-100 px-3 py-2 transition hover:border-emerald-200 hover:bg-emerald-50/50"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm font-medium text-zinc-800">
                  {task.symbol_name || task.symbol || "未识别标的"}
                </span>
                <span className="shrink-0 text-[10px] text-zinc-400">
                  {PHASE_LABELS[task.phase ?? ""] ?? task.phase}
                </span>
              </div>
              <p className="mt-0.5 text-[10px] text-emerald-700">
                {INTENT_LABELS[task.intent ?? ""] ?? task.intent}
              </p>
              {task.user_query && (
                <p className="mt-1 line-clamp-2 text-xs text-zinc-500">
                  {task.user_query}
                </p>
              )}
              <p className="mt-1 text-[10px] text-zinc-400">
                {formatTime(task.created_at)}
              </p>
            </Link>
          </li>
        ))}
      </ul>
    </aside>
  );
}
