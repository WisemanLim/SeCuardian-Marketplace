import client from "./client";

export interface WorkflowNode {
  id: string;
  type: "trigger" | "agent" | "llm" | "condition" | "hitl" | "transform" | "notify";
  config?: Record<string, unknown>;
}
export interface WorkflowEdge {
  source: string;
  target: string;
  when?: string;
}
export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: number;
  tenant_id: string;
  name: string;
  description: string;
  definition_json: WorkflowDefinition;
  trigger_type: string;
  trigger_config_json: Record<string, unknown>;
  enabled: boolean;
  version: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRun {
  id: number;
  tenant_id: string;
  workflow_id: number;
  status: "pending" | "running" | "waiting_hitl" | "completed" | "failed" | "cancelled";
  trigger_source: string;
  input_json: string;
  output_json: string;
  error: string;
  waiting_node_id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowNodeRun {
  id: number;
  run_id: number;
  node_id: string;
  node_type: string;
  status: string;
  attempts: number;
  input_json: string;
  output_json: string;
  error: string;
}

export async function listWorkflows(): Promise<Workflow[]> {
  const { data } = await client.get<{ workflows: Workflow[] }>("/workflows");
  return data.workflows ?? [];
}

export async function getWorkflow(id: number): Promise<Workflow> {
  const { data } = await client.get<Workflow>(`/workflows/${id}`);
  return data;
}

export async function createWorkflow(body: {
  name: string;
  description?: string;
  definition_json: WorkflowDefinition;
  trigger_type?: string;
  enabled?: boolean;
}): Promise<Workflow> {
  const { data } = await client.post<Workflow>("/workflows", body);
  return data;
}

export async function runWorkflow(
  workflowId: number,
  input: Record<string, unknown> = {},
): Promise<WorkflowRun> {
  const { data } = await client.post<WorkflowRun>(`/workflows/${workflowId}/run`, {
    input,
    trigger_source: "manual",
  });
  return data;
}

export async function getRun(runId: number): Promise<WorkflowRun> {
  const { data } = await client.get<WorkflowRun>(`/workflow-runs/${runId}`);
  return data;
}

export async function getRunNodes(runId: number): Promise<WorkflowNodeRun[]> {
  const { data } = await client.get<{ nodes: WorkflowNodeRun[] }>(`/workflow-runs/${runId}/nodes`);
  return data.nodes ?? [];
}

export async function approveHitl(
  runId: number,
  approved: boolean,
  payload: Record<string, unknown> = {},
): Promise<WorkflowRun> {
  const { data } = await client.post<WorkflowRun>(`/workflow-runs/${runId}/hitl`, { approved, payload });
  return data;
}

export async function cancelRun(runId: number): Promise<WorkflowRun> {
  const { data } = await client.post<WorkflowRun>(`/workflow-runs/${runId}/cancel`);
  return data;
}

export const NODE_TYPES = ["trigger", "agent", "llm", "condition", "hitl", "transform", "notify"] as const;
