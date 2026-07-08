import { useMemo } from "react";
import { ReactFlow, Background, Controls, MiniMap, type Node, type Edge, MarkerType } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { WorkflowNode, WorkflowEdge } from "../../api/workflow";

const NODE_COLOR: Record<string, string> = {
  trigger: "#16a34a", agent: "#2563eb", llm: "#7c3aed", condition: "#d97706",
  hitl: "#dc2626", transform: "#0891b2", notify: "#4b5563",
};

/** DAG 를 계층(BFS 깊이)별로 배치해 좌→우 흐름으로 시각화. React Flow 캔버스(E3 확장).
 *  a11y 폼 편집기(WorkflowPage)가 1차 편집 수단이고, 이 캔버스는 읽기 전용 시각화(미리보기). */
export default function WorkflowCanvas({ nodes, edges }: { nodes: WorkflowNode[]; edges: WorkflowEdge[] }) {
  const { rfNodes, rfEdges } = useMemo(() => {
    // 깊이 계산(위상): source 없는 노드 depth 0, 이후 최장경로
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
    const rfNodes: Node[] = nodes.map((n) => {
      const d = depth[n.id] ?? 0;
      const row = perDepth[d] ?? 0;
      perDepth[d] = row + 1;
      return {
        id: n.id,
        position: { x: d * 200, y: row * 90 },
        data: { label: `${n.id}\n(${n.type})` },
        style: {
          borderLeft: `4px solid ${NODE_COLOR[n.type] ?? "#6b7280"}`,
          borderRadius: 6, fontSize: 11, padding: 6, whiteSpace: "pre-line",
          width: 150, background: "var(--rf-node-bg, #fff)",
        },
      };
    });
    const rfEdges: Edge[] = edges.map((e, i) => ({
      id: `e${i}`,
      source: e.source,
      target: e.target,
      label: e.when,
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed },
    }));
    return { rfNodes, rfEdges };
  }, [nodes, edges]);

  return (
    <div style={{ height: 320 }} className="rounded border border-gray-200 dark:border-gray-700" aria-label="워크플로우 DAG 시각화">
      <ReactFlow nodes={rfNodes} edges={rfEdges} fitView proOptions={{ hideAttribution: true }}
        nodesDraggable={false} nodesConnectable={false} elementsSelectable={false}>
        <Background />
        <Controls showInteractive={false} />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  );
}
