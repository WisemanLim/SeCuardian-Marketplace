import axios from "axios";

export interface HealthStatus {
  status: string;
  env: string;
  mode: string;
}

// /health 는 /api 프리픽스 밖(app/main.py 루트) — client.ts(baseURL=/api) 대신 직접 호출.
export async function getHealth(): Promise<HealthStatus> {
  const { data } = await axios.get<HealthStatus>("/health");
  return data;
}
