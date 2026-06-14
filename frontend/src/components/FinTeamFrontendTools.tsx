"use client";

import { useFrontendTool } from "@copilotkit/react-core";
import {
  fetchAnalysisContextTool,
  fetchFilingsTool,
  fetchFinancialsTool,
  fetchMarketTool,
  fetchNewsTool,
  formatToolResult,
  type ToolApiResponse,
} from "@/lib/tools-api";

type ToolArgs = {
  symbol: string;
  symbol_name?: string;
  limit?: number;
};

export function FinTeamFrontendTools() {
  useFrontendTool({
    name: "get_market_quote",
    description: "获取 A 股行情事实（供 AI 分析，返回结构化上下文而非原始 API）",
    parameters: [
      { name: "symbol", type: "string", description: "A 股 6 位代码，如 600519", required: true },
      { name: "symbol_name", type: "string", description: "标的名称，如 贵州茅台", required: false },
    ],
    handler: async ({ symbol, symbol_name }: ToolArgs) => {
      const res = await fetchMarketTool(symbol, symbol_name ?? "");
      return formatToolResult(res);
    },
  });

  useFrontendTool({
    name: "get_financials",
    description: "获取 A 股基本面指标事实（供 AI 分析估值与财务）",
    parameters: [
      { name: "symbol", type: "string", description: "A 股 6 位代码", required: true },
      { name: "symbol_name", type: "string", description: "标的名称", required: false },
    ],
    handler: async ({ symbol, symbol_name }: ToolArgs) => {
      const res = await fetchFinancialsTool(symbol, symbol_name ?? "");
      return formatToolResult(res);
    },
  });

  useFrontendTool({
    name: "get_stock_news",
    description: "获取标的近期新闻事实（供 AI 事件与情绪分析）",
    parameters: [
      { name: "symbol", type: "string", description: "A 股 6 位代码", required: true },
      { name: "symbol_name", type: "string", description: "标的名称", required: false },
      { name: "limit", type: "number", description: "返回条数，默认 5", required: false },
    ],
    handler: async ({ symbol, symbol_name, limit }: ToolArgs) => {
      const res = await fetchNewsTool(symbol, symbol_name ?? "", limit ?? 5);
      return formatToolResult(res);
    },
  });

  useFrontendTool({
    name: "get_stock_filings",
    description: "获取标的近期法定信息披露（巨潮资讯公开接口，供 AI 事件分析）",
    parameters: [
      { name: "symbol", type: "string", description: "A 股 6 位代码", required: true },
      { name: "symbol_name", type: "string", description: "标的名称", required: false },
      { name: "limit", type: "number", description: "返回条数，默认 5", required: false },
    ],
    handler: async ({ symbol, symbol_name, limit }: ToolArgs) => {
      const res = await fetchFilingsTool(symbol, symbol_name ?? "", limit ?? 5);
      return formatToolResult(res);
    },
  });

  useFrontendTool({
    name: "get_research_context",
    description: "一次性获取标的完整投研数据上下文（行情+财报+新闻+公告），供 AI 综合分析",
    parameters: [
      { name: "symbol", type: "string", description: "A 股 6 位代码", required: true },
      { name: "symbol_name", type: "string", description: "标的名称", required: false },
      { name: "limit", type: "number", description: "资讯/公告条数，默认 5", required: false },
    ],
    handler: async ({ symbol, symbol_name, limit }: ToolArgs) => {
      const res = await fetchAnalysisContextTool(symbol, symbol_name ?? "", limit ?? 5);
      return res.ai_context ?? formatToolResult(res as ToolApiResponse);
    },
  });

  return null;
}
