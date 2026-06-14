import Link from "next/link";
import { notFound } from "next/navigation";
import { TeamGroupChat, type TeamFeedMessage } from "@/components/TeamGroupChat";
import { fetchTask } from "@/lib/api";

export const dynamic = "force-dynamic";

type ArtifactRef = {
  agent_id?: string;
  artifact_type?: string;
  artifact_id?: string;
};

export default async function TaskReplayPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let task;
  try {
    task = await fetchTask(id);
  } catch {
    notFound();
  }

  const teamFeed = (task.team_feed ?? []) as TeamFeedMessage[];
  const progress = task.phase === "done" ? 100 : 0;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-8">
      <header className="space-y-1">
        <Link
          href="/"
          className="text-xs text-emerald-600 hover:underline"
        >
          ← 返回对话
        </Link>
        <h1 className="text-2xl font-semibold text-zinc-900">研判回放</h1>
        <p className="text-sm text-zinc-600">
          {task.symbol_name || task.symbol || "未识别标的"}
          {task.intent ? ` · ${task.intent}` : ""}
        </p>
        {task.user_query && (
          <p className="text-sm text-zinc-500">用户问题：{task.user_query}</p>
        )}
        <p className="text-[10px] text-zinc-400">task_id: {task.task_id}</p>
      </header>

      <div className="flex flex-col gap-4 lg:flex-row">
        <TeamGroupChat feed={teamFeed} progress={progress} phase={task.phase} />
        {task.final_report?.content && (
          <section className="min-w-0 flex-1 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-zinc-900">终裁报告</h2>
            <pre className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-zinc-700">
              {task.final_report.content}
            </pre>
          </section>
        )}
      </div>

      {task.artifact_chain && task.artifact_chain.length > 0 && (
        <section className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-zinc-900">Artifact 链</h2>
          <p className="mt-1 text-xs text-zinc-500">
            共 {task.artifact_chain.length} 个子 Agent 输出，task_id 全链路可追踪
          </p>
          <ul className="mt-3 space-y-2">
            {task.artifact_chain.map((art, i) => {
              const item = art as ArtifactRef;
              return (
              <li
                key={item.artifact_id ?? i}
                className="rounded-lg bg-zinc-50 px-3 py-2 text-xs text-zinc-600"
              >
                <span className="font-medium text-zinc-800">{item.agent_id}</span>
                {" · "}
                {item.artifact_type}
                {item.artifact_id && (
                  <span className="ml-2 text-zinc-400">{item.artifact_id.slice(0, 8)}…</span>
                )}
              </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
