"use client";

type SubAgentStatus = {
  agent_id: string;
  status: "pending" | "working" | "completed" | "failed" | "timeout";
  message?: string | null;
};

type AgentState = {
  task_id?: string;
  symbol?: string;
  symbol_name?: string;
  intent?: string;
  phase?: string;
  progress?: number;
  sub_agent_status?: SubAgentStatus[];
  planned_agents?: string[];
  awaiting_human?: {
    reason?: string;
    options?: string[];
    suspicious_items?: string[];
  } | null;
};

const AGENT_LABELS: Record<string, string> = {
  data_collector: "数据获取",
  verification: "数据核查",
  authenticity: "真伪验证",
  pro_buy: "支持买入",
  anti_buy: "不建议买入",
  pro_sell: "建议卖出",
  anti_sell: "不建议卖出",
};

const PHASE_LABELS: Record<string, string> = {
  planning: "规划中",
  data: "取数",
  verify: "核查",
  auth: "验真",
  debate: "多空辩论",
  judgment: "终裁",
  done: "完成",
  cancelled: "已取消",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-zinc-200 text-zinc-600",
  working: "bg-blue-100 text-blue-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  timeout: "bg-amber-100 text-amber-700",
};

export function AgentStatusPanel({ state }: { state: AgentState }) {
  const progress = state.progress ?? 0;
  const phase = state.phase ?? "planning";

  return (
    <aside className="flex w-full flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm lg:w-80">
      <div>
        <h2 className="text-sm font-semibold text-zinc-900">任务状态</h2>
        <p className="mt-1 text-xs text-zinc-500">
          {state.symbol_name || state.symbol || "未识别标的"}
          {state.intent ? ` · ${state.intent}` : ""}
        </p>
      </div>

      <div>
        <div className="mb-1 flex justify-between text-xs text-zinc-600">
          <span>{PHASE_LABELS[phase] ?? phase}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-zinc-100">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-500">
          子 Agent
        </h3>
        {(state.sub_agent_status ?? []).map((row) => {
          const active = (state.planned_agents ?? []).includes(row.agent_id);
          return (
            <div
              key={row.agent_id}
              className={`rounded-lg border px-3 py-2 ${active ? "border-zinc-200" : "border-transparent opacity-40"}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-zinc-800">
                  {AGENT_LABELS[row.agent_id] ?? row.agent_id}
                </span>
                <span
                  className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${STATUS_COLORS[row.status]}`}
                >
                  {row.status}
                </span>
              </div>
              {row.message && (
                <p className="mt-1 text-xs text-zinc-500">{row.message}</p>
              )}
            </div>
          );
        })}
      </div>

      {state.awaiting_human && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          <p className="text-xs font-medium text-amber-800">等待人工确认</p>
          <p className="mt-1 text-xs text-amber-700">{state.awaiting_human.reason}</p>
        </div>
      )}

      {state.task_id && (
        <p className="break-all text-[10px] text-zinc-400">task: {state.task_id}</p>
      )}
    </aside>
  );
}
