"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { ThreadProvider, useThread } from "@/context/thread-context";

function CopilotKitWithThread({ children }: { children: React.ReactNode }) {
  const { threadId } = useThread();
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="finteam_main"
      threadId={threadId}
      useSingleEndpoint={false}
    >
      {children}
    </CopilotKit>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThreadProvider>
      <CopilotKitWithThread>{children}</CopilotKitWithThread>
    </ThreadProvider>
  );
}
