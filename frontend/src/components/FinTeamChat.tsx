"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { useCoAgentStateRender } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { AgentStatusPanel } from "./AgentStatusPanel";
import { AuthenticityHitl } from "./AuthenticityHitl";
import { DebatePanel } from "./DebatePanel";
import { FinalReportPanel } from "./FinalReportPanel";

export function FinTeamChat() {
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
      <AuthenticityHitl />
      <div className="flex min-h-[70vh] flex-col gap-4 lg:flex-row">
        <div className="flex-1 rounded-xl border border-zinc-200 bg-white shadow-sm">
          <CopilotChat
            className="h-[70vh]"
            labels={{
              title: "FinTeam Agent",
              initial:
                "你好，我是 FinTeam 主 Agent。\n\n你可以问我：\n- 分析贵州茅台是否值得买入\n- 分析持仓茅台是否该卖出\n- 核实一条财经新闻真伪\n\n（M2：验真存疑时将暂停等待你确认）",
              placeholder: "输入投研问题，例如：分析茅台（600519）是否值得买入",
            }}
          />
        </div>
      </div>
    </>
  );
}
