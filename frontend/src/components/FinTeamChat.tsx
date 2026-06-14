"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { useCoAgent } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { useThread } from "@/context/thread-context";
import { AuthenticityHitl } from "./AuthenticityHitl";
import { FinTeamFrontendTools } from "./FinTeamFrontendTools";
import { TeamGroupChat, type TeamFeedMessage } from "./TeamGroupChat";

type FinTeamState = {
  team_feed?: TeamFeedMessage[];
  progress?: number;
  phase?: string;
};

export function FinTeamChat() {
  const { threadId, ready } = useThread();
  const { state } = useCoAgent<FinTeamState>({ name: "finteam_main" });

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
                  "你好，我是 FinTeam 主 Agent（A 股个人投研辅助，不构成投资建议）。\n\n你可以问我：\n- 分析贵州茅台是否值得买入\n- 600519 近一年 PE 走势与估值分位\n- 300750 成本 180 是否减仓\n- 600519 最近有什么法定公告\n\n数据默认使用 AKShare + 巨潮 + 东财资讯（免费公开源）。",
                placeholder: "输入投研问题，例如：分析茅台（600519）是否值得买入",
              }}
            />
          ) : (
            <div className="flex h-[70vh] items-center justify-center text-sm text-zinc-400">
              初始化会话…
            </div>
          )}
        </div>
        <TeamGroupChat
          feed={state?.team_feed}
          progress={state?.progress}
          phase={state?.phase}
        />
      </div>
    </>
  );
}
