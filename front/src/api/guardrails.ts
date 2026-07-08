import client from "./client";

export interface GuardrailsDomain {
  domain_key: string;
  display_name: string;
  status: "functional" | "catalog_only";
  rule_count: number;
}

export interface AgentGuardrailConfig {
  agent_key: string;
  domain_key: string;
  enabled: boolean;
  io_scope: "input" | "output" | "both";
}

export interface GuardrailsTestResult {
  decision: "allow" | "warn" | "redact" | "sanitize" | "block" | "escalate";
  riskScore: number;
  matchedRules: string[];
  categories: string[];
  normalizedText: string;
  redactedText: string;
  decisionId: string;
  evaluatedDomains: string[];
}

export async function listDomains(): Promise<GuardrailsDomain[]> {
  const { data } = await client.get<{ domains: GuardrailsDomain[] }>("/guardrails/domains");
  return data.domains ?? [];
}

export async function getAgentConfig(agentKey: string): Promise<AgentGuardrailConfig[]> {
  const { data } = await client.get<{ domains: AgentGuardrailConfig[] }>(`/guardrails/agents/${agentKey}/config`);
  return data.domains ?? [];
}

export async function setAgentConfig(
  agentKey: string,
  domainKey: string,
  enabled: boolean,
  ioScope: "input" | "output" | "both" = "both",
): Promise<AgentGuardrailConfig> {
  const { data } = await client.put<AgentGuardrailConfig>(`/guardrails/agents/${agentKey}/config`, {
    domain_key: domainKey, enabled, io_scope: ioScope,
  });
  return data;
}

export async function testText(text: string, domain = "global", agentKey?: string): Promise<GuardrailsTestResult> {
  const { data } = await client.post<GuardrailsTestResult>("/guardrails/test", {
    text, domain, agent_key: agentKey,
  });
  return data;
}
