"use client";

import { useLangGraphInterrupt } from "@copilotkit/react-core";

type InterruptPayload = {
  reason?: string;
  suspicious_items?: string[];
  options?: string[];
};

export function AuthenticityHitl() {
  useLangGraphInterrupt({
    enabled: ({ eventValue }) => {
      const v = eventValue as InterruptPayload;
      return Array.isArray(v?.options) && v.options.includes("continue");
    },
    render: ({ event, resolve }) => {
      const value = (event.value ?? {}) as InterruptPayload;
      const items = value.suspicious_items ?? [];

      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div
            role="dialog"
            aria-labelledby="auth-hitl-title"
            className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-xl"
          >
            <h2 id="auth-hitl-title" className="text-lg font-semibold text-zinc-900">
              验真存疑确认
            </h2>
            <p className="mt-2 text-sm text-zinc-600">
              {value.reason ?? "发现未完全验真的信息，是否继续后续分析？"}
            </p>
            {items.length > 0 && (
              <ul className="mt-3 max-h-40 space-y-1 overflow-y-auto rounded-lg bg-amber-50 p-3 text-xs text-amber-900">
                {items.map((item, i) => (
                  <li key={i}>• {item}</li>
                ))}
              </ul>
            )}
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
                onClick={() => resolve("abort")}
              >
                终止分析
              </button>
              <button
                type="button"
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                onClick={() => resolve("continue")}
              >
                继续分析
              </button>
            </div>
          </div>
        </div>
      );
    },
  });

  return null;
}
