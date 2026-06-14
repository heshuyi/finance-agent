const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type ToolApiResponse<T = Record<string, unknown>> = {
  ok: boolean;
  data: T;
  source: string;
  fetched_at?: string;
  from_cache: boolean;
  errors: Array<{ code: string; message: string; source: string }>;
  ai_context?: string;
};

async function callTool<T>(
  path: string,
  params: Record<string, string | number>,
): Promise<ToolApiResponse<T>> {
  const qs = new URLSearchParams(
    Object.entries(params).map(([k, v]) => [k, String(v)]),
  );
  const res = await fetch(`${API_BASE}/tools/${path}?${qs}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Tool ${path} 请求失败 (${res.status})`);
  }
  return res.json();
}

export function fetchMarketTool(symbol: string, symbolName = "") {
  return callTool<Record<string, unknown>>("market", { symbol, symbol_name: symbolName });
}

export function fetchFinancialsTool(symbol: string, symbolName = "") {
  return callTool<Record<string, unknown>>("financials", { symbol, symbol_name: symbolName });
}

export function fetchNewsTool(symbol: string, symbolName = "", limit = 5) {
  return callTool<Record<string, unknown>>("news", { symbol, symbol_name: symbolName, limit });
}

export function fetchFilingsTool(symbol: string, symbolName = "", limit = 5) {
  return callTool<Record<string, unknown>>("filings", { symbol, symbol_name: symbolName, limit });
}

export function fetchAnalysisContextTool(symbol: string, symbolName = "", limit = 5) {
  return callTool<{ ai_context?: string }>("context", { symbol, symbol_name: symbolName, limit });
}

export function fetchValuationTool(symbol: string, symbolName = "", days = 365) {
  return callTool<Record<string, unknown>>("valuation", {
    symbol,
    symbol_name: symbolName,
    days,
  });
}

export function fetchIndicatorsTool(symbol: string, symbolName = "") {
  return callTool<Record<string, unknown>>("indicators", { symbol, symbol_name: symbolName });
}

export function fetchPeersTool(symbol: string, symbolName = "", limit = 3) {
  return callTool<Record<string, unknown>>("peers", { symbol, symbol_name: symbolName, limit });
}

/** 返回给 CopilotKit Agent 的分析上下文，不是给用户看的原始 JSON */
export function formatToolResult(res: ToolApiResponse<Record<string, unknown>>): string {
  if (res.ai_context) {
    return res.ai_context;
  }
  if (!res.ok) {
    return `数据获取失败: ${res.errors.map((e) => e.message).join("; ")}`;
  }
  const cache = res.from_cache ? "（本地缓存）" : "";
  return `${res.source}${cache} 数据已获取，请结合返回字段分析。`;
}
