import client from "./client";

export interface DashboardSummary {
  server: { status: string; env: string; guardrails_enabled: boolean; vector_backend: string };
  agents: { total: number; enabled: number; addons_active: number };
  marketplace: { assets: number; installed: number };
  workflow: { total: number; runs: number; waiting_hitl: number };
  rag: { collections: number };
  playground: { runs: number; tokens: number };
  guardrails: { decisions: number; blocked: number };
}

export interface ActivityItem {
  kind: "workflow" | "playground" | "guardrails";
  ts: string | null;
  detail: string;
}

export async function getSummary(): Promise<DashboardSummary> {
  const { data } = await client.get<DashboardSummary>("/dashboard/summary");
  return data;
}

export async function getActivity(limit = 10): Promise<ActivityItem[]> {
  const { data } = await client.get<{ activity: ActivityItem[] }>("/dashboard/activity", { params: { limit } });
  return data.activity ?? [];
}
