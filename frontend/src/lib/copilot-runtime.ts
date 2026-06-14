import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  InMemoryAgentRunner,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";

const agentUrl = process.env.AGENT_URL ?? "http://127.0.0.1:8000/agent";

export const copilotRuntime = new CopilotRuntime({
  agents: {
    finteam_main: new HttpAgent({ url: agentUrl }),
  },
  runner: new InMemoryAgentRunner(),
});

export const copilotHandler = createCopilotRuntimeHandler({
  runtime: copilotRuntime,
  basePath: "/api/copilotkit",
  cors: true,
});
