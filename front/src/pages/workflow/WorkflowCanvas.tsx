import { useCallback, useMemo } from "react";
import {
  ReactFlow, Background, Controls, MiniMap, applyNodeChanges,
  type Node, type Edge, type NodeChange, type EdgeChange, type Connection, MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { WorkflowNode, WorkflowEdge } from "../../api/workflow";

const NODE_COLOR: Record<string, string> = {
  trigger: "#16a34a", agent: "#2563eb", llm: "#7c3aed", condition: "#d97706",
  hitl: "#dc2626", transform: "#0891b2", notify: "#4b5563", http: "#059669",
};

function edgeId(e: WorkflowEdge): string {
  return `${e.source}->${e.target}->${e.when ?? ""}`;
}

interface Props {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  /** impl/27(§7.2.5) — 지정 시 편집형(드래그 이동·연결·삭제). 미지정 시 기존 읽기전용 시각화. */
  onChange?: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
}

/** DAG 를 계층(BFS 깊이)별로 배치해 좌→우 흐름으로 시각화(좌표 미지정 노드의 폴백 레이아웃).
 *  impl/27: onChange 지정 시 드래그 이동·연결·삭제 가능한 편집형 캔버스로 승격.
 *  KWCAG 2.2: 캔버스는 마우스 중심이라 접근성 대상이 아니며, a11y 폼 편집기(WorkflowPage
 *  DefinitionEditor)가 동일 nodes/edges 상태를 공유하는 대체편집기로 계속 병행된다. */
export default function WorkflowCanvas({ nodes, edges, onChange }: Readonly<Props>) {
  const editable = !!onChange;

  const rfNodes: Node[] = useMemo(() => {
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
        position: n.position ?? { x: d * 200, y: row * 90 },
        data: { label: `${n.id}\n(${n.type})` },
        style: {
          borderLeft: `4px solid ${NODE_COLOR[n.type] ?? "#6b7280"}`,
          borderRadius: 6, fontSize: 11, padding: 6, whiteSpace: "pre-line",
          width: 150, background: "var(--rf-node-bg, #fff)",
        },
      };
    });
  }, [nodes, edges]);

  const rfEdges: Edge[] = useMemo(() => edges.map((e) => ({
    id: edgeId(e),
    source: e.source,
    target: e.target,
    label: e.when,
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
  })), [edges]);

  const handleNodesChange = useCallback((changes: NodeChange[]) => {
    if (!onChange) return;
    const removed = new Set(changes.filter((c) => c.type === "remove").map((c) => c.id));
    if (removed.size > 0) {
      onChange(
        nodes.filter((n) => !removed.has(n.id)),
        edges.filter((e) => !removed.has(e.source) && !removed.has(e.target)),
      );
      return;
    }
    const next = applyNodeChanges(changes, rfNodes);
    const posById = new Map(next.map((n) => [n.id, n.position]));
    onChange(nodes.map((n) => (posById.has(n.id) ? { ...n, position: posById.get(n.id) } : n)), edges);
  }, [nodes, edges, onChange, rfNodes]);

  const handleEdgesChange = useCallback((changes: EdgeChange[]) => {
    if (!onChange) return;
    const removed = new Set(changes.filter((c) => c.type === "remove").map((c) => c.id));
    if (removed.size === 0) return;
    onChange(nodes, edges.filter((e) => !removed.has(edgeId(e))));
  }, [nodes, edges, onChange]);

  const handleConnect = useCallback((conn: Connection) => {
    if (!onChange || !conn.source || !conn.target) return;
    onChange(nodes, [...edges, { source: conn.source, target: conn.target }]);
  }, [nodes, edges, onChange]);

  return (
    <div style={{ height: 320 }} className="rounded border border-gray-200 dark:border-gray-700"
      aria-label={editable ? "워크플로우 DAG 편집 캔버스(마우스 드래그 전용 — 키보드 사용자는 위 폼 편집기 이용)" : "워크플로우 DAG 시각화"}>
      <ReactFlow
        nodes={rfNodes} edges={rfEdges} fitView proOptions={{ hideAttribution: true }}
        nodesDraggable={editable} nodesConnectable={editable} elementsSelectable={editable}
        deleteKeyCode={editable ? ["Backspace", "Delete"] : []}
        onNodesChange={editable ? handleNodesChange : undefined}
        onEdgesChange={editable ? handleEdgesChange : undefined}
        onConnect={editable ? handleConnect : undefined}
      >
        <Background />
        <Controls showInteractive={editable} />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  );
}
