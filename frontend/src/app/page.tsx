import { FinTeamChat } from "@/components/FinTeamChat";
import { HistorySidebar } from "@/components/HistorySidebar";

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-8">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-emerald-600">
          M5 · 投研群聊
        </p>
        <h1 className="text-2xl font-semibold text-zinc-900">FinTeam Agent</h1>
        <p className="text-sm text-zinc-600">
          虚拟投研团队：取数 → 核查 → 验真 → 三轮辩论 → 仲裁 → 群聊时间线
        </p>
      </header>
      <div className="flex flex-col gap-4 lg:flex-row">
        <HistorySidebar />
        <div className="min-w-0 flex-1">
          <FinTeamChat />
        </div>
      </div>
    </div>
  );
}
