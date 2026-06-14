"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { useCoAgentStateRender } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { useThread } from "@/context/thread-context";
import { AgentStatusPanel } from "./AgentStatusPanel";
import { AuthenticityHitl } from "./AuthenticityHitl";
import { DebatePanel } from "./DebatePanel";
import { FinalReportPanel } from "./FinalReportPanel";
import { FinTeamFrontendTools } from "./FinTeamFrontendTools";

export function FinTeamChat() {
  const { threadId, ready } = useThread();

  useCoAgentStateRender({
    name: "finteam_main",
    render: ({ state }) => (
      <div className="flex w-full flex-col gap-4 lg:w-96 lg:shrink-0">
        <AgentStatusPanel state={state} />
        <DebatePanel state={state} />
        <FinalReportPanel report={state.final_report} />
      </div>
    ),
  });

  return (
    <>
      <FinTeamFrontendTools />
      <AuthenticityHitl />
      <div className="flex min-h-[70vh] flex-col gap-4 lg:flex-row">
        <div className="flex-1 rounded-xl border border-zinc-200 bg-white shadow-sm">
          {ready ? (
            <CopilotChat
              key={threadId}
              className="h-[70vh]"
              labels={{
                title: "FinTeam Agent",
                initial:
                  "你好，我是 FinTeam 主 Agent（个人投研辅助，不构成投资建议）。\n\n你可以问我：\n- 分析贵州茅台是否值得买入\n- 查一下 600519 最新行情\n- 600519 最近有什么法定公告\n\n行情来自 AKShare 等公开数据；资讯建议配置 FINNHUB_API_KEY；公告来自巨潮法定披露平台。",
                placeholder: "输入投研问题，例如：分析茅台（600519）是否值得买入",
              }}
            />
          ) : (
            <div className="flex h-[70vh] items-center justify-center text-sm text-zinc-400">
              初始化会话…
            </div>
          )}
        </div>
      </div>
    </>
  );
}
