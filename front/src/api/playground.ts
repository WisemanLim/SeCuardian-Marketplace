import client from "./client";

export interface PlaygroundCitation {
  chunk_id: number;
  document_id: number;
  text: string;
  rrf_score: number;
}

export interface PlaygroundRun {
  id: number;
  tenant_id: string;
  prompt: string;
  system_prompt: string;
  model: string;
  rag_collection_id: number | null;
  response_text: string;
  provider: "ollama" | "degraded" | "";
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  citations_json: string;
  created_by: string;
  created_at: string;
}

export async function runPlayground(body: {
  prompt: string;
  system?: string;
  model?: string;
  rag_collection_id?: number | null;
  top_k?: number;
}): Promise<PlaygroundRun> {
  const { data } = await client.post<PlaygroundRun>("/playground/run", body);
  return data;
}

export async function listRuns(limit = 50): Promise<PlaygroundRun[]> {
  const { data } = await client.get<{ runs: PlaygroundRun[] }>("/playground/runs", { params: { limit } });
  return data.runs ?? [];
}
