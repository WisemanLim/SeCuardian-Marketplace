import { useEffect, useState } from "react";
import {
  Workflow, WorkflowNode, WorkflowEdge, WorkflowRun, WorkflowNodeRun,
  NODE_TYPES, listWorkflows, createWorkflow, runWorkflow, getRun, getRunNodes,
  approveHitl, cancelRun,
} from "../../api/workflow";
import { useLocale } from "../../hooks/useLocale";
import WorkflowCanvas from "./WorkflowCanvas";

const RUN_STATUS_COLOR: Record<string, string> = {
  pending: "text-gray-500", running: "text-blue-500", waiting_hitl: "text-amber-500",
  completed: "text-green-600", failed: "text-red-500", cancelled: "text-gray-400",
};

function newNodeId(nodes: WorkflowNode[]): string {
  let i = nodes.length + 1;
  const ids = new Set(nodes.map((n) => n.id));
  while (ids.has(`n${i}`)) i++;
  return `n${i}`;
}

/** a11y 폼 기반 노드/엣지 편집기 — PRD §7.11 1차 우선(캔버스는 로드맵 확장). */
function DefinitionEditor({
  nodes, edges, onChange,
}: {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  onChange: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
}) {
  function addNode() {
    const id = newNodeId(nodes);
    onChange([...nodes, { id, type: "transform", config: {} }], edges);
  }
  function updateNode(idx: number, patch: Partial<WorkflowNode>) {
    const next = nodes.slice();
    next[idx] = { ...next[idx], ...patch };
    onChange(next, edges);
  }
  function updateNodeConfig(idx: number, raw: string) {
    try {
      updateNode(idx, { config: JSON.parse(raw || "{}") });
    } catch {
      // 유효 JSON 아니면 입력은 반영하지 않음(다음 valid 입력 대기)
    }
  }
  function removeNode(idx: number) {
    const id = nodes[idx].id;
    onChange(
      nodes.filter((_, i) => i !== idx),
      edges.filter((e) => e.source !== id && e.target !== id),
    );
  }
  function addEdge() {
    if (nodes.length < 2) return;
    onChange(nodes, [...edges, { source: nodes[0].id, target: nodes[1].id }]);
  }
  function updateEdge(idx: number, patch: Partial<WorkflowEdge>) {
    const next = edges.slice();
    next[idx] = { ...next[idx], ...patch };
    onChange(nodes, next);
  }
  function removeEdge(idx: number) {
    onChange(nodes, edges.filter((_, i) => i !== idx));
  }

  return (
    <div className="space-y-4">
      <section aria-labelledby="nodes-heading">
        <div className="flex items-center justify-between mb-2">
          <h3 id="nodes-heading" className="text-sm font-semibold text-gray-700 dark:text-gray-300">노드</h3>
          <button type="button" onClick={addNode}
            className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700">
            + 노드 추가
          </button>
        </div>
        <div className="space-y-2">
          {nodes.map((n, idx) => (
            <div key={idx} className="flex items-start gap-2 p-2 rounded border border-gray-200 dark:border-gray-700">
              <div className="flex-1 grid grid-cols-2 gap-2">
                <label className="text-xs text-gray-500">
                  ID
                  <input
                    aria-label={`노드 ${idx + 1} ID`}
                    value={n.id}
                    onChange={(e) => updateNode(idx, { id: e.target.value })}
                    className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
                  />
                </label>
                <label className="text-xs text-gray-500">
                  타입
                  <select
                    aria-label={`노드 ${idx + 1} 타입`}
                    value={n.type}
                    onChange={(e) => updateNode(idx, { type: e.target.value as WorkflowNode["type"] })}
                    className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
                  >
                    {NODE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </label>
                <label className="text-xs text-gray-500 col-span-2">
                  config (JSON)
                  <textarea
                    aria-label={`노드 ${idx + 1} 설정 JSON`}
                    defaultValue={JSON.stringify(n.config ?? {}, null, 0)}
                    onChange={(e) => updateNodeConfig(idx, e.target.value)}
                    rows={2}
                    className="mt-0.5 w-full text-xs font-mono px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800"
                  />
                </label>
              </div>
              <button type="button" onClick={() => removeNode(idx)} aria-label={`노드 ${idx + 1} 삭제`}
                className="text-xs px-2 py-1 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20">삭제</button>
            </div>
          ))}
          {nodes.length === 0 && <p className="text-xs text-gray-400">노드가 없습니다. "+ 노드 추가"로 시작하세요.</p>}
        </div>
      </section>

      <section aria-labelledby="edges-heading">
        <div className="flex items-center justify-between mb-2">
          <h3 id="edges-heading" className="text-sm font-semibold text-gray-700 dark:text-gray-300">엣지</h3>
          <button type="button" onClick={addEdge} disabled={nodes.length < 2}
            className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
            + 엣지 추가
          </button>
        </div>
        <div className="space-y-2">
          {edges.map((e, idx) => (
            <div key={idx} className="flex items-center gap-2 p-2 rounded border border-gray-200 dark:border-gray-700">
              <label className="text-xs text-gray-500 flex-1">
                source
                <select aria-label={`엣지 ${idx + 1} source`} value={e.source}
                  onChange={(ev) => updateEdge(idx, { source: ev.target.value })}
                  className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
                  {nodes.map((n) => <option key={n.id} value={n.id}>{n.id}</option>)}
                </select>
              </label>
              <label className="text-xs text-gray-500 flex-1">
                target
                <select aria-label={`엣지 ${idx + 1} target`} value={e.target}
                  onChange={(ev) => updateEdge(idx, { target: ev.target.value })}
                  className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
                  {nodes.map((n) => <option key={n.id} value={n.id}>{n.id}</option>)}
                </select>
              </label>
              <label className="text-xs text-gray-500 flex-1">
                when (조건 분기, 선택)
                <input aria-label={`엣지 ${idx + 1} when`} value={e.when ?? ""}
                  placeholder="true | false"
                  onChange={(ev) => updateEdge(idx, { when: ev.target.value || undefined })}
                  className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
              </label>
              <button type="button" onClick={() => removeEdge(idx)} aria-label={`엣지 ${idx + 1} 삭제`}
                className="text-xs px-2 py-1 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20">삭제</button>
            </div>
          ))}
          {edges.length === 0 && <p className="text-xs text-gray-400">엣지가 없습니다.</p>}
        </div>
      </section>
    </div>
  );
}

function RunPanel({ run, onRefresh }: { run: WorkflowRun; onRefresh: () => void }) {
  const [nodes, setNodes] = useState<WorkflowNodeRun[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getRunNodes(run.id).then(setNodes).catch(() => {});
  }, [run.id, run.status]);

  async function decide(approved: boolean) {
    setBusy(true);
    try {
      await approveHitl(run.id, approved);
      onRefresh();
    } finally {
      setBusy(false);
    }
  }
  async function doCancel() {
    setBusy(true);
    try {
      await cancelRun(run.id);
      onRefresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 p-3 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40">
      <div className="flex items-center justify-between">
        <p className="text-sm">
          Run #{run.id} — <span className={`font-semibold ${RUN_STATUS_COLOR[run.status] ?? ""}`}>{run.status}</span>
          {run.waiting_node_id && <span className="text-xs text-gray-400 ml-2">대기 노드: {run.waiting_node_id}</span>}
        </p>
        <div className="flex gap-2">
          {run.status === "waiting_hitl" && (
            <>
              <button disabled={busy} onClick={() => decide(true)}
                className="text-xs px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-40">승인</button>
              <button disabled={busy} onClick={() => decide(false)}
                className="text-xs px-2 py-1 rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-40">거부</button>
            </>
          )}
          {["pending", "running", "waiting_hitl"].includes(run.status) && (
            <button disabled={busy} onClick={doCancel}
              className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-40">취소</button>
          )}
        </div>
      </div>
      {run.error && <p className="text-xs text-red-500 mt-1">{run.error}</p>}
      <table className="w-full text-xs mt-2">
        <thead className="text-gray-400">
          <tr><th className="text-left font-normal py-1">노드</th><th className="text-left font-normal">타입</th><th className="text-left font-normal">상태</th><th className="text-left font-normal">시도</th></tr>
        </thead>
        <tbody>
          {nodes.map((n) => (
            <tr key={n.id} className="border-t border-gray-200 dark:border-gray-800">
              <td className="py-1">{n.node_id}</td><td>{n.node_type}</td>
              <td className={RUN_STATUS_COLOR[n.status] ?? ""}>{n.status}</td><td>{n.attempts}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function WorkflowPage() {
  const { t } = useLocale();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [nodes, setNodes] = useState<WorkflowNode[]>([{ id: "trigger1", type: "trigger" }]);
  const [edges, setEdges] = useState<WorkflowEdge[]>([]);
  const [runInput, setRunInput] = useState<Record<number, string>>({});
  const [activeRuns, setActiveRuns] = useState<Record<number, WorkflowRun>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    listWorkflows().then(setWorkflows).catch(() => {});
  }
  useEffect(load, []);

  async function handleCreate() {
    setError("");
    if (!name.trim()) { setError("이름을 입력하세요."); return; }
    setBusy(true);
    try {
      await createWorkflow({ name, definition_json: { nodes, edges } });
      setShowCreate(false);
      setName(""); setNodes([{ id: "trigger1", type: "trigger" }]); setEdges([]);
      load();
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "생성 실패");
    } finally {
      setBusy(false);
    }
  }

  async function handleRun(wf: Workflow) {
    let input: Record<string, unknown> = {};
    const raw = runInput[wf.id];
    if (raw) {
      try { input = JSON.parse(raw); } catch { /* invalid JSON -> {} */ }
    }
    const run = await runWorkflow(wf.id, input);
    setActiveRuns((m) => ({ ...m, [wf.id]: run }));
  }

  async function refreshRun(wfId: number, runId: number) {
    const run = await getRun(runId);
    setActiveRuns((m) => ({ ...m, [wfId]: run }));
  }

  return (
    <div className="page">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{t("nav.workflow") ?? "워크플로우"}</h1>
          <p className="text-xs text-gray-500 mt-0.5">에이전트·LLM·조건·HITL 노드를 DAG로 조합해 자동화합니다.</p>
        </div>
        <button onClick={() => setShowCreate((v) => !v)}
          className="text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700">
          {showCreate ? "닫기" : "+ 새 워크플로우"}
        </button>
      </div>

      {showCreate && (
        <div className="mb-6 p-4 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <label className="block text-xs text-gray-500 mb-2">
            이름
            <input value={name} onChange={(e) => setName(e.target.value)}
              className="mt-0.5 w-full text-sm px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          <DefinitionEditor nodes={nodes} edges={edges} onChange={(n, e) => { setNodes(n); setEdges(e); }} />
          {nodes.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-gray-500 mb-1">DAG 미리보기 (React Flow)</p>
              <WorkflowCanvas nodes={nodes} edges={edges} />
            </div>
          )}
          {error && <p role="alert" className="text-xs text-red-500 mt-2">{error}</p>}
          <button disabled={busy} onClick={handleCreate}
            className="mt-3 text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
            저장
          </button>
        </div>
      )}

      <div className="space-y-3">
        {workflows.map((wf) => (
          <div key={wf.id} className="p-3 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100">{wf.name}</p>
                <p className="text-xs text-gray-400">
                  {wf.definition_json.nodes.length}노드 · {wf.definition_json.edges.length}엣지 · v{wf.version}
                  {!wf.enabled && <span className="ml-1 text-amber-500">(비활성)</span>}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  aria-label={`${wf.name} 실행 입력 JSON`}
                  placeholder='{"key":"value"}'
                  value={runInput[wf.id] ?? ""}
                  onChange={(e) => setRunInput((m) => ({ ...m, [wf.id]: e.target.value }))}
                  className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800 w-40"
                />
                <button onClick={() => handleRun(wf)} disabled={!wf.enabled}
                  className="text-xs px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-40">
                  실행
                </button>
              </div>
            </div>
            {activeRuns[wf.id] && (
              <RunPanel run={activeRuns[wf.id]} onRefresh={() => refreshRun(wf.id, activeRuns[wf.id].id)} />
            )}
          </div>
        ))}
        {workflows.length === 0 && !showCreate && (
          <p className="text-sm text-gray-400">등록된 워크플로우가 없습니다.</p>
        )}
      </div>
    </div>
  );
}
