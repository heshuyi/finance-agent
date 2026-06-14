"use client";

import type { ReactNode } from "react";

const PHASE_LABELS: Record<string, string> = {
  planning: "任务规划",
  data: "数据获取",
  verify: "交叉核查",
  auth: "真伪验证",
  debate_r1: "多空辩论 · 开篇",
  debate_r2: "多空辩论 · 多方反驳",
  debate_r3: "多空辩论 · 空方反驳",
  judgment: "终裁仲裁",
};

const ROLE_AVATAR: Record<string, string> = {
  system: "bg-zinc-500",
  staff: "bg-sky-500",
  bull: "bg-emerald-500",
  bear: "bg-rose-500",
  judge: "bg-amber-500",
};

export type TeamFeedMessage = {
  id: string;
  agent_id: string;
  display_name: string;
  role: string;
  phase: string;
  round?: number;
  content: string;
  created_at: string;
};

type TeamGroupChatProps = {
  feed?: TeamFeedMessage[];
  progress?: number;
  phase?: string;
};

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function renderSimpleMarkdown(text: string): ReactNode[] {
  const lines = text.split("\n");
  return lines.map((line, li) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    const nodes = parts.map((part, pi) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={pi} className="font-semibold text-zinc-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return <span key={pi}>{part}</span>;
    });
    return (
      <span key={li} className="block">
        {nodes}
      </span>
    );
  });
}

export function TeamGroupChat({ feed = [], progress, phase }: TeamGroupChatProps) {
  let lastPhase = "";

  return (
    <aside className="flex h-[70vh] w-full flex-col rounded-xl border border-zinc-200 bg-zinc-50 shadow-sm lg:w-96 lg:shrink-0">
      <header className="border-b border-zinc-200 bg-white px-4 py-3">
        <h2 className="text-sm font-semibold text-zinc-900">投研群</h2>
        <p className="mt-0.5 text-xs text-zinc-500">
          取数 → 核查 → 验真 → 三轮辩论 → 仲裁
        </p>
        {typeof progress === "number" && (
          <div className="mt-2">
            <div className="flex items-center justify-between text-[10px] text-zinc-400">
              <span>{phase ? PHASE_LABELS[phase] ?? phase : "进行中"}</span>
              <span>{progress}%</span>
            </div>
            <div className="mt-1 h-1 overflow-hidden rounded-full bg-zinc-200">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all"
                style={{ width: `${Math.min(100, progress)}%` }}
              />
            </div>
          </div>
        )}
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-3 py-4">
        {feed.length === 0 && (
          <p className="text-center text-xs text-zinc-400">
            发起买入/卖出研判后，团队协作消息将在此显示
          </p>
        )}
        {feed.map((msg) => {
          const showDivider = msg.phase !== lastPhase;
          lastPhase = msg.phase;
          const avatarClass = ROLE_AVATAR[msg.role] ?? ROLE_AVATAR.staff;

          return (
            <div key={msg.id}>
              {showDivider && PHASE_LABELS[msg.phase] && (
                <div className="my-3 flex items-center gap-2">
                  <div className="h-px flex-1 bg-zinc-200" />
                  <span className="text-[10px] text-zinc-400">
                    —— {PHASE_LABELS[msg.phase]} ——
                  </span>
                  <div className="h-px flex-1 bg-zinc-200" />
                </div>
              )}
              <article className="flex gap-2">
                <div
                  className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-xs font-bold text-white ${avatarClass}`}
                  aria-hidden
                >
                  {msg.display_name.slice(0, 1)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs font-medium text-zinc-800">
                      {msg.display_name}
                    </span>
                    <time className="text-[10px] text-zinc-400">
                      {formatTime(msg.created_at)}
                    </time>
                  </div>
                  <div className="mt-1 rounded-lg rounded-tl-none bg-white px-3 py-2 text-sm leading-relaxed text-zinc-700 shadow-sm">
                    {renderSimpleMarkdown(msg.content)}
                  </div>
                </div>
              </article>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
