import client from "./client";

export interface GuardrailsDomain {
  domain_key: string;
  display_name: string;
  status: "functional" | "heuristic" | "catalog_only";
  rule_count: number;
  regex_rule_count: number;
  real_rule_count?: number;
  heuristic_rule_count?: number;
  is_required: number;
  filter_enabled: number;
}

export interface GuardrailsPerDomain {
  domain: string;
  decision: string;
  riskScore: number;
  matchedRules: string[];
  matchedCount: number;
  llmMatched?: string[];
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
  perDomain: GuardrailsPerDomain[];
  source?: string;
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

export async function testText(
  text: string, domains?: string[], agentKey?: string,
): Promise<GuardrailsTestResult> {
  const { data } = await client.post<GuardrailsTestResult>("/guardrails/test", {
    text, domains, agent_key: agentKey,
  });
  return data;
}

/** 도메인 카탈로그 '필터적용' 토글(§7.8.7) — 필수(global) 도메인은 해제 불가(409). */
export async function setDomainFilter(
  domainKey: string, enabled: boolean,
): Promise<{ domain_key: string; filter_enabled: boolean }> {
  const { data } = await client.put(`/guardrails/domains/${domainKey}/filter`, { enabled });
  return data;
}
