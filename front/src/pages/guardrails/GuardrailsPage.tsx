import { useEffect, useState } from "react";
import {
  GuardrailsDomain, GuardrailsTestResult, AgentGuardrailConfig,
  listDomains, testText, getAgentConfig, setAgentConfig,
} from "../../api/guardrails";
import { AgentConfig, listAgentConfigs } from "../../api/agentConfig";
import { useLocale } from "../../hooks/useLocale";

const DECISION_COLOR: Record<string, string> = {
  allow: "text-green-600", warn: "text-amber-500", redact: "text-amber-500",
  sanitize: "text-amber-500", block: "text-red-500", escalate: "text-red-600",
};

export default function GuardrailsPage() {
  const { t } = useLocale();
  const [domains, setDomains] = useState<GuardrailsDomain[]>([]);
  const [testInput, setTestInput] = useState("");
  const [result, setResult] = useState<GuardrailsTestResult | null>(null);
  const [busy, setBusy] = useState(false);

  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [agentDomains, setAgentDomains] = useState<AgentGuardrailConfig[]>([]);

  useEffect(() => {
    listDomains().then(setDomains).catch(() => {});
    listAgentConfigs().then(setAgents).catch(() => {});
  }, []);

  function loadAgentConfig(key: string) {
    setSelectedAgent(key);
    if (key) getAgentConfig(key).then(setAgentDomains).catch(() => {});
  }

  async function handleTest() {
    if (!testInput.trim()) return;
    setBusy(true);
    try {
      setResult(await testText(testInput, "global"));
    } finally {
      setBusy(false);
    }
  }

  async function toggleDomain(domainKey: string, enabled: boolean) {
    if (!selectedAgent) return;
    await setAgentConfig(selectedAgent, domainKey, enabled);
    loadAgentConfig(selectedAgent);
  }

  function isEnabled(domainKey: string): boolean {
    return agentDomains.find((d) => d.domain_key === domainKey)?.enabled ?? false;
  }

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{t("nav.guardrails") ?? "가드레일"}</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          도메인 규칙셋을 요청/응답에 강제하는 거버넌스. 1차 실기능 범위: <code className="font-mono">global</code>(PII/신용정보 13종).
        </p>
      </div>

      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">도메인 카탈로그</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {domains.map((d) => (
            <div key={d.domain_key} className="p-2 rounded border border-gray-200 dark:border-gray-700 text-xs">
              <p className="font-medium text-gray-700 dark:text-gray-200">{d.display_name}</p>
              <span className={`inline-block mt-1 px-1.5 py-0.5 rounded text-[10px] ${
                d.status === "functional" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                          : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"}`}>
                {d.status === "functional" ? `실판정 (${d.rule_count}종)` : "카탈로그 전용"}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">테스트 (Playground 연계)</h3>
        <textarea placeholder="PII/신용정보 등을 포함한 텍스트를 입력해 판정을 시험하세요."
          rows={3} value={testInput} onChange={(e) => setTestInput(e.target.value)}
          className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
        <button disabled={busy} onClick={handleTest}
          className="mt-2 text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
          판정 시험
        </button>
        {result && (
          <div className="mt-3 p-2 rounded bg-gray-50 dark:bg-gray-800 text-xs">
            <p>
              결정: <span className={`font-semibold ${DECISION_COLOR[result.decision] ?? ""}`}>{result.decision}</span>
              {" · "}riskScore: {result.riskScore}
            </p>
            {result.matchedRules.length > 0 && (
              <p className="mt-1 text-gray-500">매치 규칙: {result.matchedRules.join(", ")}</p>
            )}
            {result.decision !== "allow" && (
              <p className="mt-1 text-gray-500">마스킹 결과: {result.redactedText}</p>
            )}
          </div>
        )}
      </section>

      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">에이전트별 도메인 토글</h3>
        <select value={selectedAgent} onChange={(e) => loadAgentConfig(e.target.value)}
          className="text-sm px-2 py-1.5 mb-2 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
          <option value="">에이전트 선택</option>
          {agents.map((a) => <option key={a.agent_key} value={a.agent_key}>{a.agent_name}</option>)}
        </select>
        {selectedAgent && (
          <div className="space-y-1.5">
            {domains.filter((d) => d.status === "functional").map((d) => (
              <label key={d.domain_key} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={isEnabled(d.domain_key)}
                  onChange={(e) => toggleDomain(d.domain_key, e.target.checked)} />
                {d.display_name}
              </label>
            ))}
            {domains.filter((d) => d.status !== "functional").length > 0 && (
              <p className="text-xs text-gray-400 mt-1">
                카탈로그 전용 도메인은 판정기가 없어 토글할 수 없습니다(PRD §7.8.0).
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
