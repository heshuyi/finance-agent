import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

const agentUrl = process.env.AGENT_URL ?? "http://127.0.0.1:8000/agent";

const runtime = new CopilotRuntime({
  agents: {
    finteam_main: new HttpAgent({ url: agentUrl }),
  },
});

const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
  runtime,
  serviceAdapter: new ExperimentalEmptyAdapter(),
  endpoint: "/api/copilotkit",
});

export const POST = async (req: NextRequest) => handleRequest(req);
