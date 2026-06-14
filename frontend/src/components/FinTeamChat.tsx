"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { useCoAgentStateRender } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { AgentStatusPanel } from "./AgentStatusPanel";

export function FinTeamChat() {
  useCoAgentStateRender({
    name: "finteam_main",
    render: ({ state }) => <AgentStatusPanel state={state} />,
  });

  return (
    <div className="flex min-h-[70vh] flex-col gap-4 lg:flex-row">
      <div className="flex-1 rounded-xl border border-zinc-200 bg-white shadow-sm">
        <CopilotChat
          className="h-[70vh]"
          labels={{
            title: "FinTeam Agent",
            initial:
              "你好，我是 FinTeam 主 Agent。\n\n你可以问我：\n- 分析贵州茅台是否值得买入\n- 查询某标的 PE 走势\n- 核实一条财经新闻真伪\n\n（M0：子 Agent 流水线将在 M1 通过 A2A 自动执行）",
            placeholder: "输入投研问题，例如：分析茅台（600519）是否值得买入",
          }}
        />
      </div>
    </div>
  );
}
