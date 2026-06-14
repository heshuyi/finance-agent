"use client";

type Claim = { statement?: string; verified?: boolean };
type Artifact = {
  claims?: Claim[];
  metadata?: { thesis?: string; risks?: string[] };
};

type DebateState = {
  intent?: string;
  planned_agents?: string[];
  artifacts?: Record<string, Artifact>;
  final_report?: {
    debate?: {
      pro_buy?: Artifact;
      anti_buy?: Artifact;
      pro_sell?: Artifact;
      anti_sell?: Artifact;
    };
  };
};

const DEBATE_SLOTS = [
  { key: "pro_buy", label: "支持买入", tone: "border-emerald-200 bg-emerald-50" },
  { key: "anti_buy", label: "不建议买入", tone: "border-rose-200 bg-rose-50" },
  { key: "pro_sell", label: "建议卖出", tone: "border-amber-200 bg-amber-50" },
  { key: "anti_sell", label: "建议持有", tone: "border-sky-200 bg-sky-50" },
] as const;

function pickArtifact(state: DebateState, key: string): Artifact | undefined {
  return (
    state.final_report?.debate?.[key as keyof NonNullable<DebateState["final_report"]>["debate"]] ??
    state.artifacts?.[key]
  );
}

export function DebatePanel({ state }: { state: DebateState }) {
  const planned = new Set(state.planned_agents ?? []);
  const activeSlots = DEBATE_SLOTS.filter((s) => planned.has(s.key));
  if (activeSlots.length === 0) return null;

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <h2 className="text-sm font-semibold text-zinc-900">多空辩论</h2>
      <p className="mt-1 text-xs text-zinc-500">
        {state.intent === "sell_analysis" ? "卖出 vs 持有" : "买入 vs 不买入"}
      </p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {activeSlots.map(({ key, label, tone }) => {
          const art = pickArtifact(state, key);
          const thesis = art?.metadata?.thesis;
          const claims = art?.claims ?? [];
          return (
            <article key={key} className={`rounded-lg border p-3 ${tone}`}>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-700">
                {label}
              </h3>
              {thesis && <p className="mt-2 text-sm font-medium text-zinc-800">{thesis}</p>}
              <ul className="mt-2 space-y-1">
                {claims.slice(0, 3).map((c, i) => (
                  <li key={i} className="text-xs text-zinc-600">
                    {c.statement}
                  </li>
                ))}
              </ul>
              {!art && <p className="mt-2 text-xs text-zinc-400">等待子 Agent 输出…</p>}
            </article>
          );
        })}
      </div>
    </section>
  );
}
