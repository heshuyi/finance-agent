const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type TaskSummary = {
  task_id: string;
  symbol?: string;
  symbol_name?: string;
  intent?: string;
  phase?: string;
  user_query?: string;
  summary?: string;
  created_at?: string;
  updated_at?: string;
};

export type TeamFeedMessage = {
  id: string;
  agent_id: string;
  display_name: string;
  role: string;
  phase: string;
  round?: number;
  content: string;
  created_at: string;
};

export type TaskDetail = TaskSummary & {
  final_report?: {
    content?: string;
    disclaimer?: string;
    intent?: string;
    debate?: Record<string, unknown>;
    arbitration?: Record<string, unknown>;
  } | null;
  artifacts?: Record<string, unknown>;
  artifact_chain?: unknown[];
  sub_agent_status?: Array<{
    agent_id: string;
    status: string;
    message?: string | null;
  }>;
  human_decision?: string | null;
  errors?: unknown[];
  team_feed?: TeamFeedMessage[];
  debate_transcript?: Record<string, unknown>;
};

export async function fetchTasks(limit = 20): Promise<{
  tasks: TaskSummary[];
  total: number;
}> {
  const res = await fetch(`${API_BASE}/tasks?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("加载历史任务失败");
  return res.json();
}

export async function fetchTask(taskId: string): Promise<TaskDetail> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`, { cache: "no-store" });
  if (res.status === 404) throw new Error("任务不存在");
  if (!res.ok) throw new Error("加载任务详情失败");
  return res.json();
}
