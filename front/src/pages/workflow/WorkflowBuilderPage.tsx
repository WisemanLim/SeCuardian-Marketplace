import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import {
  ReactFlow, ReactFlowProvider, Background, Controls, MiniMap, Handle, Position,
  applyNodeChanges, applyEdgeChanges, useReactFlow, MarkerType,
  type Node, type Edge, type NodeChange, type EdgeChange, type Connection, type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Workflow, WorkflowNode, WorkflowEdge, WorkflowComponent,
  getWorkflow, createWorkflow, updateWorkflow, listComponents,
} from "../../api/workflow";

/** impl/32(PRD §7.2.8) — Flowise/Dify 준용 풀스크린 워크플로우 빌더.
 *  팔레트(좌) → 캔버스 drag & drop(중앙) → 인스펙터(우) 3분할. React Flow(MIT) 자체 구현 —
 *  Flowise/Dify 코드 복제 없음(UX 패턴만 참조, 상용/추가조건 라이선스 구성요소 제외).
 *
 *  상태 설계: React Flow v12 는 노드 측정(measured)이 컨트롤드 상태에 반영되기 전까지
 *  visibility:hidden 을 유지한다 — 매 렌더 도메인 상태에서 rfNodes 를 재생성하면 measured 가
 *  소실되어 노드가 영구히 보이지 않는다(버그 수정 2026-07-09). 따라서 **RF Node[]/Edge[] 를
 *  단일 진실 상태로 보유**하고(applyNodeChanges 가 dimensions 변경을 그대로 흡수),
 *  도메인 모델(WorkflowNode/Edge)로는 저장·로드 시점에만 변환한다.
 *
 *  KWCAG 2.2: 캔버스는 마우스 중심 — 팔레트 클릭 삽입 + 인스펙터 표준 폼 + 기존
 *  WorkflowPage a11y 폼 편집기 병행으로 키보드 사용자 경로 유지(§7.2.5 원칙 승계). */

type NodeType = WorkflowNode["type"];
type BuilderData = { nodeType: NodeType; config: Record<string, unknown> };
type RfNode = Node<BuilderData, "secmp">;

const NODE_META: Record<NodeType, { label: string; desc: string; color: string; defaultConfig: Record<string, unknown> }> = {
  trigger: { label: "트리거", desc: "워크플로우 시작점(입력 수신)", color: "#16a34a", defaultConfig: {} },
  agent: { label: "에이전트", desc: "내장/시스템/Addon 에이전트 API 호출", color: "#2563eb", defaultConfig: { agent_key: "" } },
  llm: { label: "LLM", desc: "프롬프트로 LLM 호출(Ollama 폴백)", color: "#7c3aed", defaultConfig: { prompt: "" } },
  condition: { label: "조건", desc: "분기 판단(true/false 엣지)", color: "#d97706", defaultConfig: { left: "", op: "truthy", right: "" } },
  hitl: { label: "HITL 승인", desc: "사람 승인 대기(승인/거부)", color: "#dc2626", defaultConfig: {} },
  transform: { label: "변환", desc: "컨텍스트 템플릿으로 출력 구성", color: "#0891b2", defaultConfig: { output: {} } },
  notify: { label: "알림", desc: "메시지 기록(종료 노드로 사용)", color: "#4b5563", defaultConfig: { message: "" } },
  http: { label: "HTTP", desc: "외부 URL 직접 호출", color: "#059669", defaultConfig: { method: "GET", url: "" } },
};
const NODE_TYPE_KEYS = Object.keys(NODE_META) as NodeType[];
const CONDITION_OPS = ["truthy", "==", "!=", ">", "<", "contains"] as const;
const HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"] as const;
const DND_MIME = "application/secmp-workflow-node";
const CATEGORY_LABEL: Record<string, string> = { builtin: "내장", system: "시스템", addon: "Addon" };

interface DragPayload {
  type: NodeType;
  config?: Record<string, unknown>;
}

function summarize(type: NodeType, config: Record<string, unknown>): string {
  const c = config ?? {};
  switch (type) {
    case "agent": {
      const key = String(c.agent_key ?? "");
      return c.path ? `${key} · ${String(c.method ?? "GET")} ${String(c.path)}` : key || "에이전트 미지정";
    }
    case "llm": return String(c.prompt ?? "").slice(0, 60) || "프롬프트 미지정";
    case "condition": return `${String(c.left ?? "")} ${String(c.op ?? "truthy")} ${String(c.right ?? "")}`.trim();
    case "http": return `${String(c.method ?? "GET")} ${String(c.url ?? "")}`.trim();
    case "notify": return String(c.message ?? "").slice(0, 60);
    case "transform": return "출력 템플릿";
    case "hitl": return "승인 대기";
    default: return "시작";
  }
}

/** 캔버스 커스텀 노드 — 타입별 색상 헤더 + config 요약(Flowise 노드 카드 패턴 준용). */
function BuilderNode({ id, data, selected }: NodeProps<RfNode>) {
  const meta = NODE_META[data.nodeType];
  return (
    <div className={`rounded-md bg-white dark:bg-gray-800 shadow-sm text-left w-[190px] border ${selected ? "border-blue-500 ring-2 ring-blue-300 dark:ring-blue-700" : "border-gray-200 dark:border-gray-600"}`}>
      {data.nodeType !== "trigger" && (
        <Handle type="target" position={Position.Left} style={{ background: "#9ca3af", width: 9, height: 9 }} />
      )}
      <div className="px-2 py-1 rounded-t-md text-[11px] font-semibold text-white flex items-center justify-between"
        style={{ background: meta.color }}>
        <span>{meta.label}</span>
        <span className="opacity-80 font-normal">{data.nodeType}</span>
      </div>
      <div className="px-2 py-1.5">
        <p className="text-[11px] font-medium text-gray-800 dark:text-gray-100 truncate">{id}</p>
        <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">{summarize(data.nodeType, data.config)}</p>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: meta.color, width: 9, height: 9 }} />
    </div>
  );
}

const nodeTypes = { secmp: BuilderNode };

function newNodeId(nodes: RfNode[], type: NodeType): string {
  const ids = new Set(nodes.map((n) => n.id));
  let i = 1;
  while (ids.has(`${type}${i}`)) i++;
  return `${type}${i}`;
}

function edgeStyleProps(): Partial<Edge> {
  return { animated: true, markerEnd: { type: MarkerType.ArrowClosed } };
}

/** 도메인(WorkflowNode/Edge) → RF 상태. 좌표 없는 노드는 BFS 깊이 자동배치(§7.2.5 승계). */
function toRfNodes(nodes: WorkflowNode[], edges: WorkflowEdge[]): RfNode[] {
  const depth: Record<string, number> = {};
  nodes.forEach((n) => { depth[n.id] = 0; });
  for (let i = 0; i < nodes.length; i++) {
    for (const e of edges) {
      if (depth[e.source] !== undefined && depth[e.target] !== undefined) {
        depth[e.target] = Math.max(depth[e.target], depth[e.source] + 1);
      }
    }
  }
  const perDepth: Record<number, number> = {};
  return nodes.map((n) => {
    const d = depth[n.id] ?? 0;
    const row = perDepth[d] ?? 0;
    perDepth[d] = row + 1;
    return {
      id: n.id,
      type: "secmp" as const,
      position: n.position ?? { x: 60 + d * 240, y: 60 + row * 110 },
      data: { nodeType: n.type, config: (n.config ?? {}) as Record<string, unknown> },
    };
  });
}

function toRfEdges(edges: WorkflowEdge[]): Edge[] {
  return edges.map((e) => ({
    id: `${e.source}->${e.target}`,
    source: e.source,
    target: e.target,
    label: e.when,
    data: { when: e.when },
    ...edgeStyleProps(),
  }));
}

/** RF 상태 → 도메인(저장 페이로드). position 은 definition_json.nodes[].position 으로 영속(§7.2.5). */
function toDomain(rfNodes: RfNode[], rfEdges: Edge[]): { nodes: WorkflowNode[]; edges: WorkflowEdge[] } {
  return {
    nodes: rfNodes.map((n) => ({
      id: n.id,
      type: n.data.nodeType,
      config: n.data.config,
      position: { x: Math.round(n.position.x), y: Math.round(n.position.y) },
    })),
    edges: rfEdges.map((e) => {
      const when = (e.data as { when?: string } | undefined)?.when;
      return { source: e.source, target: e.target, ...(when ? { when } : {}) };
    }),
  };
}

/** 좌측 팔레트 — 노드 타입 + 컴포넌트(§7.2.3). HTML5 드래그 + 클릭 삽입(키보드 폴백) 병행. */
function Palette({ onInsert }: Readonly<{ onInsert: (p: DragPayload) => void }>) {
  const [components, setComponents] = useState<WorkflowComponent[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    listComponents().then(setComponents).catch(() => {});
  }, []);

  const q = query.trim().toLowerCase();
  const filtered = q
    ? components.filter((c) => c.label.toLowerCase().includes(q) || c.path.toLowerCase().includes(q))
    : components;
  const groups: Record<string, WorkflowComponent[]> = { builtin: [], system: [], addon: [] };
  for (const c of filtered) groups[c.category]?.push(c);

  function startDrag(e: React.DragEvent, payload: DragPayload) {
    e.dataTransfer.setData(DND_MIME, JSON.stringify(payload));
    e.dataTransfer.effectAllowed = "move";
  }

  return (
    <aside aria-label="노드 팔레트" className="w-60 shrink-0 border-r border-gray-200 dark:border-gray-700 overflow-y-auto bg-white dark:bg-gray-900">
      <div className="p-3">
        <h2 className="text-xs font-semibold text-gray-500 mb-2">노드</h2>
        <p className="text-[10px] text-gray-400 mb-2">캔버스로 드래그하거나 클릭해 추가</p>
        <div className="space-y-1">
          {NODE_TYPE_KEYS.map((t) => (
            <button key={t} type="button" draggable
              onDragStart={(e) => startDrag(e, { type: t })}
              onClick={() => onInsert({ type: t })}
              className="w-full text-left p-2 rounded border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 cursor-grab active:cursor-grabbing bg-white dark:bg-gray-800">
              <span className="flex items-center gap-2">
                <span aria-hidden className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: NODE_META[t].color }} />
                <span className="text-xs font-medium text-gray-800 dark:text-gray-100">{NODE_META[t].label}</span>
                <span className="text-[10px] text-gray-400">{t}</span>
              </span>
              <span className="block text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 pl-4">{NODE_META[t].desc}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="p-3 border-t border-gray-200 dark:border-gray-700">
        <h2 className="text-xs font-semibold text-gray-500 mb-2">컴포넌트(에이전트 API)</h2>
        <input aria-label="컴포넌트 검색" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="검색…"
          className="w-full text-xs px-2 py-1 mb-2 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
        {(["builtin", "system", "addon"] as const).map((cat) => groups[cat].length > 0 && (
          <div key={cat} className="mb-2">
            <p className="text-[10px] font-semibold text-gray-400 mb-1">{CATEGORY_LABEL[cat]} 에이전트</p>
            <div className="space-y-1">
              {groups[cat].map((c) => {
                const payload: DragPayload = {
                  type: "agent",
                  config: { agent_key: c.agent_key, method: c.method, path: c.path },
                };
                return (
                  <button key={`${c.agent_key}-${c.method}-${c.path}`} type="button" draggable
                    onDragStart={(e) => startDrag(e, payload)}
                    onClick={() => onInsert(payload)}
                    title={`${c.method} ${c.path}`}
                    className="w-full text-left px-2 py-1 rounded text-[11px] bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 cursor-grab active:cursor-grabbing truncate">
                    {c.label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
        {components.length === 0 && <p className="text-[11px] text-gray-400">사용 가능한 컴포넌트가 없습니다.</p>}
      </div>
    </aside>
  );
}

/** 우측 인스펙터 — 선택 노드의 타입별 구조화 폼 + JSON 폴백, 선택 엣지의 when 편집(§7.2.5 유보 해소). */
function Inspector({
  node, edge, allIds, onNodeChange, onNodeRemove, onEdgeChange, onEdgeRemove,
}: Readonly<{
  node: RfNode | null;
  edge: Edge | null;
  allIds: string[];
  onNodeChange: (id: string, patch: { id?: string; nodeType?: NodeType; config?: Record<string, unknown> }) => void;
  onNodeRemove: (id: string) => void;
  onEdgeChange: (id: string, when: string | undefined) => void;
  onEdgeRemove: (id: string) => void;
}>) {
  const [idDraft, setIdDraft] = useState(node?.id ?? "");
  useEffect(() => { setIdDraft(node?.id ?? ""); }, [node?.id]);

  if (!node && !edge) {
    return (
      <aside aria-label="속성 편집" className="w-72 shrink-0 border-l border-gray-200 dark:border-gray-700 p-3 bg-white dark:bg-gray-900">
        <p className="text-xs text-gray-400">노드/엣지를 선택하면 속성을 편집할 수 있습니다.</p>
      </aside>
    );
  }

  if (edge) {
    const when = (edge.data as { when?: string } | undefined)?.when ?? "";
    return (
      <aside aria-label="엣지 속성 편집" className="w-72 shrink-0 border-l border-gray-200 dark:border-gray-700 p-3 overflow-y-auto bg-white dark:bg-gray-900 space-y-3">
        <h2 className="text-xs font-semibold text-gray-500">엣지</h2>
        <p className="text-xs font-mono text-gray-600 dark:text-gray-300">{edge.source} → {edge.target}</p>
        <label className="block text-xs text-gray-500">
          when (조건 분기 — condition 노드의 true/false)
          <input aria-label="엣지 when" value={when} placeholder="true | false | 비움(무조건)"
            onChange={(e) => onEdgeChange(edge.id, e.target.value || undefined)}
            className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
        </label>
        <button type="button" onClick={() => onEdgeRemove(edge.id)}
          className="text-xs px-2 py-1 rounded text-red-500 border border-red-200 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20">
          엣지 삭제
        </button>
      </aside>
    );
  }

  const n = node!;
  const cfg = n.data.config ?? {};
  const setCfg = (patch: Record<string, unknown>) => onNodeChange(n.id, { config: { ...cfg, ...patch } });
  const applyId = () => {
    const next = idDraft.trim();
    if (next && next !== n.id && !allIds.includes(next)) onNodeChange(n.id, { id: next });
    else setIdDraft(n.id);
  };
  const textInput = (label: string, key: string, placeholder = "") => (
    <label className="block text-xs text-gray-500">
      {label}
      <input aria-label={`${n.id} ${label}`} value={String(cfg[key] ?? "")} placeholder={placeholder}
        onChange={(e) => setCfg({ [key]: e.target.value })}
        className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
    </label>
  );

  return (
    <aside aria-label="노드 속성 편집" className="w-72 shrink-0 border-l border-gray-200 dark:border-gray-700 p-3 overflow-y-auto bg-white dark:bg-gray-900 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold text-gray-500">노드 속성</h2>
        <span className="text-[10px] px-1.5 py-0.5 rounded text-white" style={{ background: NODE_META[n.data.nodeType].color }}>
          {NODE_META[n.data.nodeType].label}
        </span>
      </div>
      <label className="block text-xs text-gray-500">
        ID (Enter 로 적용, 엣지 자동 갱신)
        <input aria-label="노드 ID" value={idDraft}
          onChange={(e) => setIdDraft(e.target.value)}
          onBlur={applyId}
          onKeyDown={(e) => { if (e.key === "Enter") applyId(); }}
          className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
      </label>
      <label className="block text-xs text-gray-500">
        타입
        <select aria-label="노드 타입" value={n.data.nodeType}
          onChange={(e) => {
            const t = e.target.value as NodeType;
            onNodeChange(n.id, { nodeType: t, config: { ...NODE_META[t].defaultConfig } });
          }}
          className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
          {NODE_TYPE_KEYS.map((t) => <option key={t} value={t}>{NODE_META[t].label} ({t})</option>)}
        </select>
      </label>

      {n.data.nodeType === "agent" && (
        <>
          {textInput("agent_key", "agent_key", "예: rag")}
          <label className="block text-xs text-gray-500">
            method
            <select aria-label={`${n.id} method`} value={String(cfg.method ?? "GET")}
              onChange={(e) => setCfg({ method: e.target.value })}
              className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
              {HTTP_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>
          {textInput("path (비우면 스텁 호출)", "path", "/api/rag/search")}
          <p className="text-[10px] text-gray-400">팔레트의 컴포넌트를 드래그/클릭하면 자동 설정됩니다.</p>
        </>
      )}
      {n.data.nodeType === "llm" && (
        <>
          <label className="block text-xs text-gray-500">
            prompt ({"{{trigger1.input.key}}"} 템플릿 지원)
            <textarea aria-label={`${n.id} prompt`} value={String(cfg.prompt ?? "")} rows={4}
              onChange={(e) => setCfg({ prompt: e.target.value })}
              className="mt-0.5 w-full text-xs font-mono px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
          </label>
          {textInput("system (선택)", "system")}
        </>
      )}
      {n.data.nodeType === "condition" && (
        <>
          {textInput("left", "left", "{{node.output.key}}")}
          <label className="block text-xs text-gray-500">
            op
            <select aria-label={`${n.id} op`} value={String(cfg.op ?? "truthy")}
              onChange={(e) => setCfg({ op: e.target.value })}
              className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
              {CONDITION_OPS.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </label>
          {textInput("right", "right")}
          <p className="text-[10px] text-gray-400">나가는 엣지의 when 을 true/false 로 지정해 분기합니다.</p>
        </>
      )}
      {n.data.nodeType === "http" && (
        <>
          <label className="block text-xs text-gray-500">
            method
            <select aria-label={`${n.id} method`} value={String(cfg.method ?? "GET")}
              onChange={(e) => setCfg({ method: e.target.value })}
              className="mt-0.5 w-full text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800">
              {HTTP_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>
          {textInput("url", "url", "https://…")}
        </>
      )}
      {n.data.nodeType === "notify" && textInput("message", "message", "{{llm1.text}}")}
      {n.data.nodeType === "hitl" && <p className="text-[11px] text-gray-400">실행이 이 노드에서 승인 대기(waiting_hitl) 상태가 됩니다.</p>}
      {n.data.nodeType === "trigger" && <p className="text-[11px] text-gray-400">워크플로우 입력이 {"{{"}트리거ID.input{"}}"} 으로 노출됩니다.</p>}
      {n.data.nodeType === "transform" && <p className="text-[11px] text-gray-400">아래 JSON 의 output 객체가 컨텍스트 템플릿으로 해석됩니다.</p>}

      <details>
        <summary className="text-[11px] text-gray-400 cursor-pointer">고급 — config JSON 직접 편집</summary>
        <textarea key={`${n.id}-json`} aria-label={`${n.id} 설정 JSON`}
          defaultValue={JSON.stringify(cfg, null, 1)} rows={5}
          onChange={(e) => {
            try { onNodeChange(n.id, { config: JSON.parse(e.target.value || "{}") }); } catch { /* invalid → 대기 */ }
          }}
          className="mt-1 w-full text-[11px] font-mono px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800" />
      </details>

      <button type="button" onClick={() => onNodeRemove(n.id)}
        className="text-xs px-2 py-1 rounded text-red-500 border border-red-200 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20">
        노드 삭제
      </button>
    </aside>
  );
}

function BuilderInner() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { screenToFlowPosition } = useReactFlow();

  const editId = id ? Number(id) : null;
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [triggerType, setTriggerType] = useState<"manual" | "webhook">("manual");
  // RF 상태가 단일 진실 — applyNodeChanges 가 position/dimensions/select 변경을 그대로 유지한다.
  const [rfNodes, setRfNodes] = useState<RfNode[]>(() =>
    editId === null ? toRfNodes([{ id: "trigger1", type: "trigger", position: { x: 60, y: 120 } }], []) : []);
  const [rfEdges, setRfEdges] = useState<Edge[]>([]);
  const [selNodeId, setSelNodeId] = useState<string | null>(null);
  const [selEdgeId, setSelEdgeId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [savedAt, setSavedAt] = useState("");
  const [loadedVersion, setLoadedVersion] = useState<number | null>(null);
  const [webhookSecret, setWebhookSecret] = useState<{ workflowId: number; secret: string } | null>(null);

  useEffect(() => {
    if (editId === null) return;
    getWorkflow(editId)
      .then((wf: Workflow) => {
        setName(wf.name);
        setDescription(wf.description ?? "");
        setTriggerType(wf.trigger_type === "webhook" ? "webhook" : "manual");
        setRfNodes(toRfNodes(wf.definition_json.nodes ?? [], wf.definition_json.edges ?? []));
        setRfEdges(toRfEdges(wf.definition_json.edges ?? []));
        setLoadedVersion(wf.version);
      })
      .catch(() => setError("워크플로우를 불러오지 못했습니다."));
  }, [editId]);

  const handleNodesChange = useCallback((changes: NodeChange<RfNode>[]) => {
    setRfNodes((ns) => applyNodeChanges(changes, ns));
    const removed = changes.filter((c) => c.type === "remove").map((c) => c.id);
    if (removed.length > 0) {
      setRfEdges((es) => es.filter((e) => !removed.includes(e.source) && !removed.includes(e.target)));
      setSelNodeId((s) => (s && removed.includes(s) ? null : s));
    }
  }, []);

  const handleEdgesChange = useCallback((changes: EdgeChange[]) => {
    setRfEdges((es) => applyEdgeChanges(changes, es));
    const removed = changes.filter((c) => c.type === "remove").map((c) => c.id);
    if (removed.length > 0) setSelEdgeId((s) => (s && removed.includes(s) ? null : s));
  }, []);

  const handleConnect = useCallback((conn: Connection) => {
    if (!conn.source || !conn.target || conn.source === conn.target) return;
    setRfEdges((es) => (es.some((e) => e.source === conn.source && e.target === conn.target)
      ? es
      : [...es, { id: `${conn.source}->${conn.target}`, source: conn.source, target: conn.target, data: {}, ...edgeStyleProps() }]));
  }, []);

  // ---------- 팔레트 삽입(드롭 좌표 / 클릭 자동 배치) ----------
  const insertNode = useCallback((p: DragPayload, position?: { x: number; y: number }) => {
    setRfNodes((ns) => {
      const nid = newNodeId(ns, p.type);
      const pos = position ?? { x: 60 + Math.max(0, ...ns.map((n) => n.position.x)) + 240, y: 120 };
      setSelNodeId(nid);
      setSelEdgeId(null);
      return [...ns, {
        id: nid, type: "secmp" as const, position: pos,
        data: { nodeType: p.type, config: { ...(p.config ?? NODE_META[p.type].defaultConfig) } },
      }];
    });
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    const raw = e.dataTransfer.getData(DND_MIME);
    if (!raw) return;
    e.preventDefault();
    try {
      const payload = JSON.parse(raw) as DragPayload;
      insertNode(payload, screenToFlowPosition({ x: e.clientX, y: e.clientY }));
    } catch { /* 잘못된 페이로드 무시 */ }
  }, [insertNode, screenToFlowPosition]);

  const onDragOver = useCallback((e: React.DragEvent) => {
    if (e.dataTransfer.types.includes(DND_MIME)) {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
    }
  }, []);

  // ---------- 인스펙터 콜백 ----------
  const selNode = rfNodes.find((n) => n.id === selNodeId) ?? null;
  const selEdge = rfEdges.find((e) => e.id === selEdgeId) ?? null;

  const onNodeChange = useCallback((nid: string, patch: { id?: string; nodeType?: NodeType; config?: Record<string, unknown> }) => {
    setRfNodes((ns) => ns.map((n) => (n.id === nid
      ? {
          ...n,
          id: patch.id ?? n.id,
          data: {
            nodeType: patch.nodeType ?? n.data.nodeType,
            config: patch.config ?? n.data.config,
          },
        }
      : n)));
    if (patch.id && patch.id !== nid) {
      setRfEdges((es) => es.map((e) => {
        const source = e.source === nid ? patch.id! : e.source;
        const target = e.target === nid ? patch.id! : e.target;
        return { ...e, id: `${source}->${target}`, source, target };
      }));
      setSelNodeId(patch.id);
    }
  }, []);

  const onNodeRemove = useCallback((nid: string) => {
    setRfNodes((ns) => ns.filter((n) => n.id !== nid));
    setRfEdges((es) => es.filter((e) => e.source !== nid && e.target !== nid));
    setSelNodeId(null);
  }, []);

  const onEdgeChange = useCallback((eid: string, when: string | undefined) => {
    setRfEdges((es) => es.map((e) => (e.id === eid ? { ...e, label: when, data: { ...e.data, when } } : e)));
  }, []);

  const onEdgeRemove = useCallback((eid: string) => {
    setRfEdges((es) => es.filter((e) => e.id !== eid));
    setSelEdgeId(null);
  }, []);

  // ---------- 저장 ----------
  async function handleSave() {
    setError("");
    if (!name.trim()) { setError("이름을 입력하세요."); return; }
    setBusy(true);
    try {
      const definition_json = toDomain(rfNodes, rfEdges);
      if (editId !== null) {
        const wf = await updateWorkflow(editId, { name, description, definition_json });
        setLoadedVersion(wf.version);
      } else {
        const wf = await createWorkflow({ name, description, definition_json, trigger_type: triggerType });
        if (wf.webhook_secret) setWebhookSecret({ workflowId: wf.id, secret: wf.webhook_secret });
        navigate(`/workflow/builder/${wf.id}`, { replace: true });
        setLoadedVersion(wf.version);
      }
      setSavedAt(new Date().toLocaleTimeString());
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "저장 실패");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* 툴바 */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <button type="button" onClick={() => navigate("/workflow")}
          className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800">
          ← 목록
        </button>
        <input aria-label="워크플로우 이름" value={name} onChange={(e) => setName(e.target.value)}
          placeholder="워크플로우 이름"
          className="text-sm font-medium px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800 w-56" />
        <input aria-label="설명" value={description} onChange={(e) => setDescription(e.target.value)}
          placeholder="설명(선택)"
          className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800 flex-1 min-w-0" />
        <select aria-label="트리거 타입" value={triggerType} disabled={editId !== null}
          onChange={(e) => setTriggerType(e.target.value as "manual" | "webhook")}
          title={editId !== null ? "트리거 타입은 생성 시에만 지정" : undefined}
          className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 dark:bg-gray-800 disabled:opacity-50">
          <option value="manual">manual</option>
          <option value="webhook">webhook</option>
        </select>
        {loadedVersion !== null && <span className="text-[11px] text-gray-400">v{loadedVersion}</span>}
        {savedAt && <span role="status" className="text-[11px] text-green-600">저장됨 {savedAt}</span>}
        {error && <span role="alert" className="text-[11px] text-red-500">{error}</span>}
        <button type="button" disabled={busy} onClick={handleSave}
          className="ml-auto text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40">
          저장
        </button>
      </div>

      {webhookSecret && (
        <div role="alert" className="px-3 py-2 border-b border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 text-xs">
          <span className="font-semibold text-amber-700 dark:text-amber-300">webhook 시크릿(지금만 표시, 재조회 불가): </span>
          <span className="font-mono break-all">{webhookSecret.secret}</span>
          <button type="button" onClick={() => setWebhookSecret(null)} className="ml-2 underline">확인함, 닫기</button>
        </div>
      )}

      {/* 3분할 본문 */}
      <div className="flex flex-1 min-h-0">
        <Palette onInsert={(p) => insertNode(p)} />
        <div className="flex-1 min-w-0" onDrop={onDrop} onDragOver={onDragOver}
          aria-label="워크플로우 캔버스(마우스 드래그 전용 — 키보드 사용자는 팔레트 클릭 삽입과 우측 속성 폼, 또는 워크플로우 목록의 폼 편집기 이용)">
          <ReactFlow
            nodes={rfNodes} edges={rfEdges} nodeTypes={nodeTypes} fitView
            proOptions={{ hideAttribution: true }}
            deleteKeyCode={["Backspace", "Delete"]}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={handleConnect}
            onNodeClick={(_, n) => { setSelNodeId(n.id); setSelEdgeId(null); }}
            onEdgeClick={(_, e) => { setSelEdgeId(e.id); setSelNodeId(null); }}
            onPaneClick={() => { setSelNodeId(null); setSelEdgeId(null); }}
          >
            <Background />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        </div>
        <Inspector
          node={selNode} edge={selEdge} allIds={rfNodes.map((n) => n.id)}
          onNodeChange={onNodeChange} onNodeRemove={onNodeRemove}
          onEdgeChange={onEdgeChange} onEdgeRemove={onEdgeRemove}
        />
      </div>
    </div>
  );
}

export default function WorkflowBuilderPage() {
  return (
    <ReactFlowProvider>
      <BuilderInner />
    </ReactFlowProvider>
  );
}
