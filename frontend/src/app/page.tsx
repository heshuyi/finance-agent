import { FinTeamChat } from "@/components/FinTeamChat";

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-emerald-600">
          M0 · LangGraph + AG-UI
        </p>
        <h1 className="text-2xl font-semibold text-zinc-900">FinTeam Agent</h1>
        <p className="text-sm text-zinc-600">
          虚拟投研团队：取数 → 核查 → 验真 → 多空辩论 → 主 Agent 终裁
        </p>
      </header>
      <FinTeamChat />
    </div>
  );
}
