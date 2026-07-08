import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { getHealth, HealthStatus } from "../../api/health";
import { listAgentConfigs, AgentConfig } from "../../api/agentConfig";
import { getSummary, getActivity, DashboardSummary, ActivityItem } from "../../api/dashboard";
import { useLocale } from "../../hooks/useLocale";

const POLL_MS = 10000;

const BUILTIN_AGENTS: { key: string; path: string; labelKey: string }[] = [
  { key: "marketplace", path: "/marketplace", labelKey: "nav.marketplace" },
  { key: "workflow", path: "/workflow", labelKey: "nav.workflow" },
  { key: "rag", path: "/rag", labelKey: "nav.rag" },
  { key: "playground", path: "/playground", labelKey: "nav.playground" },
  { key: "guardrails", path: "/guardrails", labelKey: "nav.guardrails" },
];

function StatCard({ label, value, tone = "default" }: { label: string; value: string | number; tone?: "default" | "good" | "bad" }) {
  const toneCls = tone === "good" ? "text-green-600 dark:text-green-400"
    : tone === "bad" ? "text-red-500 dark:text-red-400"
    : "text-gray-800 dark:text-gray-100";
  return (
    <div className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-xl font-semibold mt-0.5 ${toneCls}`}>{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { t } = useLocale();
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealthError(true));
    listAgentConfigs().then(setAgents).catch(() => {});
    // 실시간 위젯 — summary/activity 를 POLL_MS 주기로 폴링
    function poll() {
      getSummary().then(setSummary).catch(() => {});
      getActivity(8).then(setActivity).catch(() => {});
    }
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, []);

  const enabledCount = agents.filter((a) => a.is_enabled).length;
  const requiredCount = agents.filter((a) => a.is_required).length;
  const byGroup = agents.reduce<Record<string, number>>((acc, a) => {
    const g = a.nav_group || "기타";
    acc[g] = (acc[g] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="page space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
          {t("nav.dashboard") ?? "대시보드"}
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">플랫폼 상태와 등록된 에이전트 현황.</p>
      </div>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          label="서버 상태"
          value={healthError ? "연결 안 됨" : health?.status ?? "확인 중…"}
          tone={healthError ? "bad" : health?.status === "ok" ? "good" : "default"}
        />
        <StatCard label="환경" value={health?.env ?? "-"} />
        <StatCard label="에이전트 (전체/활성)" value={`${agents.length} / ${enabledCount}`} />
        <StatCard label="필수 에이전트" value={requiredCount} />
      </section>

      {summary && (
        <section>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            내장 에이전트 활동 <span className="text-xs font-normal text-gray-400">(10초마다 갱신)</span>
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="마켓 자산 / 설치" value={`${summary.marketplace.assets} / ${summary.marketplace.installed}`} />
            <StatCard label="워크플로우 실행 (대기)" value={`${summary.workflow.runs} (${summary.workflow.waiting_hitl})`}
              tone={summary.workflow.waiting_hitl > 0 ? "bad" : "default"} />
            <StatCard label="RAG 컬렉션 / PG 실행" value={`${summary.rag.collections} / ${summary.playground.runs}`} />
            <StatCard label="PG 토큰 누적" value={summary.playground.tokens} />
            <StatCard label="가드레일 판정 (차단)" value={`${summary.guardrails.decisions} (${summary.guardrails.blocked})`}
              tone={summary.guardrails.blocked > 0 ? "bad" : "good"} />
          </div>
        </section>
      )}

      {activity.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">최근 활동</h3>
          <ul className="space-y-1">
            {activity.map((a, i) => (
              <li key={i} className="flex items-center gap-2 text-xs">
                <span className={`px-1.5 py-0.5 rounded text-[10px] shrink-0 ${
                  a.kind === "guardrails" ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                  : a.kind === "workflow" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                  : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"}`}>{a.kind}</span>
                <span className="text-gray-700 dark:text-gray-300 truncate">{a.detail}</span>
                <span className="text-gray-400 ml-auto shrink-0">{a.ts?.slice(0, 19) ?? ""}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">내장 에이전트</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {BUILTIN_AGENTS.map((b) => {
            const cfg = agents.find((a) => a.agent_key === b.key);
            return (
              <button
                key={b.key}
                onClick={() => navigate(b.path)}
                className="text-left p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-100">{t(b.labelKey)}</span>
                  {cfg && (
                    <span className={`w-2 h-2 rounded-full shrink-0 ${cfg.is_enabled ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"}`}
                      title={cfg.is_enabled ? "활성" : "비활성"} />
                  )}
                </div>
                {cfg?.description && (
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">{cfg.description}</p>
                )}
              </button>
            );
          })}
        </div>
      </section>

      {Object.keys(byGroup).length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">그룹별 에이전트 수</h3>
          <table className="w-full text-xs">
            <tbody>
              {Object.entries(byGroup).map(([group, count]) => (
                <tr key={group} className="border-t border-gray-200 dark:border-gray-800">
                  <td className="py-1 text-gray-600 dark:text-gray-300">{group}</td>
                  <td className="py-1 text-right text-gray-800 dark:text-gray-100">{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
