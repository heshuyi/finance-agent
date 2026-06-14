import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";

import { SqliteAgentRunner } from "./sqlite-agent-runner";

const agentUrl = process.env.AGENT_URL ?? "http://127.0.0.1:8000/agent";

export const copilotRuntime = new CopilotRuntime({
  agents: {
    finteam_main: new HttpAgent({ url: agentUrl }),
  },
  runner: new SqliteAgentRunner(),
});

export const copilotHandler = createCopilotRuntimeHandler({
  runtime: copilotRuntime,
  basePath: "/api/copilotkit",
  cors: true,
});
