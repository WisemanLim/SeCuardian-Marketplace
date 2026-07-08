import { useEffect, useState } from "react";
import {
  GuardrailsDomain, GuardrailsTestResult, AgentGuardrailConfig,
  listDomains, testText, getAgentConfig, setAgentConfig, setDomainFilter,
} from "../../api/guardrails";
import { AgentConfig, listAgentConfigs } from "../../api/agentConfig";
import { getAuth } from "../../store/auth";
import { useLocale } from "../../hooks/useLocale";

const DECISION_COLOR: Record<string, string> = {
  allow: "text-green-600", warn: "text-amber-500", redact: "text-amber-500",
  sanitize: "text-amber-500", block: "text-red-500", escalate: "text-red-600",
};

// 상태 배지 — functional(원본 regex 실판정) / heuristic(생성 regex·예시 휴리스틱) / catalog_only(규칙 없음)
function statusBadge(status: string): { cls: string; label: string } {
  if (status === "functional") return { cls: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400", label: "실판정" };
  if (status === "heuristic") return { cls: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400", label: "휴리스틱" };
  return { cls: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400", label: "규칙 없음" };
}

export default function GuardrailsPage() {
  const { t } = useLocale();
  const user = getAuth();
  const isAdmin = user?.role === "supervisor" || user?.role === "admin";

  const [domains, setDomains] = useState<GuardrailsDomain[]>([]);
  const [testInput, setTestInput] = useState("");
  const [result, setResult] = useState<GuardrailsTestResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [agentDomains, setAgentDomains] = useState<AgentGuardrailConfig[]>([]);

  function reloadDomains() {
    listDomains().then(setDomains).catch(() => {});
  }
  useEffect(() => {
    reloadDomains();
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
      setResult(await testText(testInput)); // domains 미지정 → 백엔드가 global(필수)+필터적용 도메인 평가
    } finally {
      setBusy(false);
    }
  }

  async function toggleFilter(d: GuardrailsDomain, enabled: boolean) {
    setError("");
    // 낙관적 업데이트 — 즉시 체크 반영, 실패 시 원복 + 오류 표면화(무음 실패 방지)
    setDomains((prev) => prev.map((x) => x.domain_key === d.domain_key ? { ...x, filter_enabled: enabled ? 1 : 0 } : x));
    try {
      await setDomainFilter(d.domain_key, enabled);
      reloadDomains();
    } catch (e) {
      setDomains((prev) => prev.map((x) => x.domain_key === d.domain_key ? { ...x, filter_enabled: enabled ? 0 : 1 } : x));
      const msg = (e as { response?: { status?: number; data?: { detail?: string } } })?.response;
      setError(msg?.data?.detail || (msg?.status === 404 ? "필터 API 미탑재 — 백엔드 재시작 필요" : "필터 적용 실패"));
    }
  }

  // 전체 선택/해제 — 필수(global) 외 모든 도메인 필터적용 일괄 토글(§7.8.7)
  async function toggleAllFilters(enabled: boolean) {
    setError("");
    const targets = domains.filter((d) => !d.is_required);
    setDomains((prev) => prev.map((x) => x.is_required ? x : { ...x, filter_enabled: enabled ? 1 : 0 }));
    try {
      await Promise.all(targets.map((d) => setDomainFilter(d.domain_key, enabled)));
      reloadDomains();
    } catch (e) {
      reloadDomains();
      const msg = (e as { response?: { status?: number; data?: { detail?: string } } })?.response;
      setError(msg?.data?.detail || (msg?.status === 404 ? "필터 API 미탑재 — 백엔드 재시작 필요" : "일괄 필터 적용 실패"));
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

  const activeCount = domains.filter((d) => d.filter_enabled || d.is_required).length;

  return (
    <div className="page space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{t("nav.guardrails") ?? "가드레일"}</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          도메인 규칙셋을 요청/응답에 강제하는 거버넌스. <code className="font-mono">global</code>(PII/신용정보)은 무조건 필수,
          업종 도메인은 <b>필터적용</b> 토글로 테스트 적용 여부를 반영합니다.
        </p>
      </div>

      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">도메인 카탈로그</h3>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-gray-400">필터적용 {activeCount} / {domains.length} 도메인</span>
            {isAdmin && (() => {
              const targets = domains.filter((d) => !d.is_required);
              const allOn = targets.length > 0 && targets.every((d) => d.filter_enabled);
              return (
                <label className="inline-flex items-center gap-1 cursor-pointer" title="전체 필터적용/해제">
                  <input type="checkbox" checked={allOn}
                    onChange={(e) => toggleAllFilters(e.target.checked)} />
                  <span className="text-[10px] text-gray-500">전체</span>
                </label>
              );
            })()}
          </div>
        </div>
        {error && <p role="alert" className="mb-2 text-xs text-red-500">{error}</p>}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {domains.map((d) => {
            const b = statusBadge(d.status);
            const on = !!d.filter_enabled || !!d.is_required;
            return (
              <div key={d.domain_key} className={`p-2.5 rounded border text-xs ${
                on ? "border-blue-300 dark:border-blue-700 bg-blue-50/40 dark:bg-blue-900/10"
                   : "border-gray-200 dark:border-gray-700"}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-gray-700 dark:text-gray-200 truncate" title={d.domain_key}>{d.display_name}</p>
                  {d.is_required ? (
                    <span className="shrink-0 border-2 border-red-500 text-red-500 text-[9px] font-black px-1 rounded-sm uppercase leading-none">필수</span>
                  ) : isAdmin ? (
                    <label className="shrink-0 inline-flex items-center gap-1 cursor-pointer" title="필터적용">
                      <input type="checkbox" checked={!!d.filter_enabled}
                        onChange={(e) => toggleFilter(d, e.target.checked)} />
                      <span className="text-[10px] text-gray-500">적용</span>
                    </label>
                  ) : (
                    <span className={`shrink-0 inline-block w-2 h-2 rounded-full ${d.filter_enabled ? "bg-blue-500" : "bg-gray-300 dark:bg-gray-600"}`} />
                  )}
                </div>
                <div className="flex items-center gap-1.5 mt-1">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] ${b.cls}`}>{b.label}</span>
                  <span className="text-[10px] text-gray-400">
                    실판정 {d.real_rule_count ?? 0} · 휴리스틱 {d.heuristic_rule_count ?? 0} / {d.rule_count}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">테스트 (필수 + 필터적용 도메인 동시 판정)</h3>
        <textarea placeholder="PII/신용정보·업종 위반 문구 등을 입력해 판정을 시험하세요."
          rows={3} value={testInput} onChange={(e) => setTestInput(e.target.value)}
          className="w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
        <button disabled={busy} onClick={handleTest}
          className="mt-2 text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
          판정 시험
        </button>
        {result && (
          <div className="mt-3 p-2 rounded bg-gray-50 dark:bg-gray-800 text-xs space-y-1">
            <p>
              결정: <span className={`font-semibold ${DECISION_COLOR[result.decision] ?? ""}`}>{result.decision}</span>
              {" · "}riskScore: {result.riskScore}
              {" · "}평가 도메인: {result.evaluatedDomains.join(", ")}
              {result.source && <span className="ml-1 text-gray-400">[{result.source}]</span>}
            </p>
            {result.perDomain?.length > 0 && (
              <div className="mt-1 space-y-0.5">
                {result.perDomain.map((pd) => (
                  <p key={pd.domain} className="text-gray-500">
                    · {pd.domain}: <span className={DECISION_COLOR[pd.decision] ?? ""}>{pd.decision}</span>
                    {pd.matchedCount > 0 && ` (${pd.matchedCount}건: ${pd.matchedRules.slice(0, 4).join(", ")}${pd.matchedRules.length > 4 ? "…" : ""})`}
                  </p>
                ))}
              </div>
            )}
            {result.decision !== "allow" && (
              <p className="mt-1 text-gray-500">마스킹 결과: {result.redactedText}</p>
            )}
          </div>
        )}
      </section>

      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">에이전트별 도메인 토글(게이트 강제)</h3>
        <select value={selectedAgent} onChange={(e) => loadAgentConfig(e.target.value)}
          className="text-sm px-2 py-1.5 mb-2 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
          <option value="">에이전트 선택</option>
          {agents.map((a) => <option key={a.agent_key} value={a.agent_key}>{a.agent_name}</option>)}
        </select>
        {selectedAgent && (
          <div className="space-y-1.5">
            {domains.filter((d) => d.status !== "catalog_only").map((d) => (
              <label key={d.domain_key} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={isEnabled(d.domain_key)}
                  onChange={(e) => toggleDomain(d.domain_key, e.target.checked)} />
                {d.display_name}
                <span className="text-[10px] text-gray-400">({statusBadge(d.status).label})</span>
              </label>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
