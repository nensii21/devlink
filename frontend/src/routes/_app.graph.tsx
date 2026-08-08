import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Panel,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";
import { Card } from "@/components/shared/primitives";
import { Loader2 } from "lucide-react";
import { isBackendConfigured } from "@/api";

export const Route = createFileRoute("/_app/graph")({
  head: () => ({
    meta: [
      { title: "Dependency Graph — DevLink" },
      { name: "description", content: "Interactive Project Dependency Graph." },
    ],
  }),
  component: GraphView,
});

/** A node as the backend sends it, before we lay it out. */
interface GraphNodeData {
  label: string;
  type: string;
}

interface GraphNode {
  id: string;
  position?: { x: number; y: number };
  data?: GraphNodeData;
  type?: string;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/** A node after layout, which is what React Flow requires: position is set. */
type GraphFlowNode = Node<GraphNode["data"], GraphNode["type"]>;

const NODE_COLOURS: Record<string, string> = {
  project: "#3b82f6",
  user: "#10b981",
  skill: "#f59e0b",
  default: "#6366f1",
};

const fetchGraph = async (): Promise<GraphResponse> => {
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
  const response = await fetch(`${apiBaseUrl}/api/graph/dependencies`);
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }
  return (await response.json()) as GraphResponse;
};

const MOCK_DATA = {
  nodes: [
    {
      id: "proj_1",
      data: { label: "Project Alpha", type: "project" },
      position: { x: 250, y: 50 },
      type: "default",
    },
    {
      id: "skill_1",
      data: { label: "React", type: "skill" },
      position: { x: 100, y: 150 },
      type: "default",
    },
    {
      id: "skill_2",
      data: { label: "Python", type: "skill" },
      position: { x: 400, y: 150 },
      type: "default",
    },
    {
      id: "user_1",
      data: { label: "Alice", type: "user" },
      position: { x: 250, y: 250 },
      type: "default",
    },
  ],
  edges: [
    { id: "e1", source: "proj_1", target: "skill_1", label: "requires" },
    { id: "e2", source: "proj_1", target: "skill_2", label: "requires" },
    { id: "e3", source: "user_1", target: "proj_1", label: "member" },
    { id: "e4", source: "user_1", target: "skill_1", label: "knows" },
  ],
};

function GraphView() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dependency-graph"],
    queryFn: () => {
      if (isBackendConfigured()) {
        return fetchGraph();
      }
      return Promise.resolve(MOCK_DATA);
    },
  });

  // Lay out anything the backend sent without coordinates on a circle, so a
  // position-free response still renders instead of stacking every node at the
  // origin.
  const initialNodes = useMemo<GraphFlowNode[]>(() => {
    if (!data?.nodes) return [];

    return data.nodes.map((n: GraphNode, i: number) => {
      if (n.position) return n as GraphFlowNode;
      // Simple layout if no position provided by backend
      const radius = 300;
      const angle = (i / data.nodes.length) * 2 * Math.PI;

      return {
        ...n,
        position: { x: 400 + radius * Math.cos(angle), y: 300 + radius * Math.sin(angle) },
        style: {
          background: NODE_COLOURS[n.data?.type ?? ""] ?? NODE_COLOURS.default,
          color: "#fff",
          border: "none",
          borderRadius: "8px",
          padding: "10px",
          fontWeight: "bold",
        },
      } as GraphFlowNode;
    });
  }, [data]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState(data?.edges || []);

  // Update state when data changes
  useMemo(() => {
    if (initialNodes.length > 0) {
      setNodes(initialNodes as Node[]);
      setEdges(data?.edges || []);
    }
  }, [initialNodes, data?.edges, setNodes, setEdges]);

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center text-red-500">
        Failed to load dependency graph.
      </div>
    );
  }

  return (
    <Card className="h-[calc(100vh-8rem)] overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-right"
      >
        <MiniMap
          nodeStrokeColor={(n: any) => {
            if (n.data?.type === "project") return "#3b82f6";
            if (n.data?.type === "user") return "#10b981";
            if (n.data?.type === "skill") return "#f59e0b";
            return "#6366f1";
          }}
          nodeColor={(n: any) => {
            if (n.data?.type === "project") return "#3b82f6";
            if (n.data?.type === "user") return "#10b981";
            if (n.data?.type === "skill") return "#f59e0b";
            return "#6366f1";
          }}
        />
        <Controls />
        <Background color="#aaa" gap={16} />

        <Panel
          position="top-left"
          className="bg-surface/80 p-4 rounded-md border border-border backdrop-blur-sm"
        >
          <h3 className="font-semibold text-[14px] mb-2">Legend</h3>
          <div className="flex flex-col gap-2 text-[12px]">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-sm"></div> Project
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-emerald-500 rounded-sm"></div> User
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-amber-500 rounded-sm"></div> Skill
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-indigo-500 rounded-sm"></div> Organization
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </Card>
  );
}
