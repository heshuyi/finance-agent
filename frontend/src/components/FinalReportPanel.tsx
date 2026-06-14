"use client";

type FinalReport = {
  symbol?: string;
  intent?: string;
  content?: string;
  disclaimer?: string;
  task_id?: string;
};

export function FinalReportPanel({ report }: { report?: FinalReport | null }) {
  if (!report?.content) return null;

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold text-zinc-900">终裁报告</h2>
        {report.symbol && (
          <span className="text-xs text-zinc-500">{report.symbol}</span>
        )}
      </div>
      <div className="prose prose-sm mt-3 max-w-none whitespace-pre-wrap text-sm text-zinc-800">
        {report.content}
      </div>
      {report.disclaimer && (
        <p className="mt-4 border-t border-zinc-100 pt-3 text-[11px] text-zinc-400">
          {report.disclaimer}
        </p>
      )}
    </section>
  );
}
