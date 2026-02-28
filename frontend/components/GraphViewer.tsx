'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { api, GraphNode, GraphEdge } from '@/lib/api';

const nodeColors: Record<string, string> = {
  Agent: '#6366f1',
  HireRequest: '#22c55e',
  Decision: '#eab308',
  PolicyUpdate: '#f97316',
  Tool: '#06b6d4',
  default: '#8888a0',
};

const edgeColors: Record<string, string> = {
  DELEGATED: '#6366f1',
  COMPLETED: '#22c55e',
  LEARNED: '#eab308',
  USED_TOOL: '#06b6d4',
  default: '#4a4a5a',
};

interface SelectedNode {
  node: GraphNode;
}

export default function GraphViewer({ defaultFilter = '' }: { defaultFilter?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<SelectedNode | null>(null);
  const [filter, setFilter] = useState(defaultFilter);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [autoFiltered, setAutoFiltered] = useState(false);

  // Auto-filter by latest hire if no filter provided
  useEffect(() => {
    if (!filter && !autoFiltered) {
      api.listHires(1).then(hires => {
        if (hires.length > 0) {
          setFilter(hires[0].id);
          setAutoFiltered(true);
        }
      }).catch(() => {});
    }
  }, [filter, autoFiltered]);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getGraph(filter || undefined);
      setGraphData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph');
      // Use demo data as fallback
      setGraphData({
        nodes: [
          { id: 'alex', label: 'Alex (Orchestrator)', type: 'Agent', properties: { role: 'orchestrator' } },
          { id: 'maya', label: 'Maya (HR)', type: 'Agent', properties: { role: 'hr' } },
          { id: 'sam', label: 'Sam (Finance)', type: 'Agent', properties: { role: 'finance' } },
          { id: 'compliance', label: 'Compliance', type: 'Agent', properties: { role: 'compliance' } },
          { id: 'hire-1', label: 'Hire: Sarah Chen', type: 'HireRequest', properties: { role: 'Senior Engineer', status: 'approved' } },
          { id: 'decision-1', label: 'Salary Approved', type: 'Decision', properties: { amount: '$150K' } },
          { id: 'policy-1', label: 'Remote Work Policy', type: 'PolicyUpdate', properties: { source: 'Senso' } },
        ],
        edges: [
          { source: 'alex', target: 'maya', type: 'DELEGATED', properties: {} },
          { source: 'alex', target: 'sam', type: 'DELEGATED', properties: {} },
          { source: 'alex', target: 'compliance', type: 'DELEGATED', properties: {} },
          { source: 'maya', target: 'hire-1', type: 'COMPLETED', properties: {} },
          { source: 'sam', target: 'decision-1', type: 'COMPLETED', properties: {} },
          { source: 'compliance', target: 'policy-1', type: 'LEARNED', properties: {} },
        ],
      });
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  useEffect(() => {
    if (!containerRef.current || !graphData.nodes.length) return;

    let cancelled = false;

    (async () => {
      const vis = await import('vis-network/standalone');
      if (cancelled) return;

      // Assign hierarchy levels: Orchestrator=0, Agents=1, Actions/Tools=2, everything else=3
      const agentNames = new Set(['Orchestrator', 'Maya', 'Sam', 'Compliance', 'Alex', 'Aria']);
      const getLevel = (n: GraphNode) => {
        if (n.label === 'Orchestrator') return 0;
        if (n.type === 'Agent' && agentNames.has(n.label)) return 1;
        if (n.type === 'Action' || n.type === 'Tool') return 2;
        return 3;
      };

      const nodes = new vis.DataSet(
        graphData.nodes.map((n) => ({
          id: n.id,
          label: n.label.length > 30 ? n.label.substring(0, 30) + '…' : n.label,
          level: getLevel(n),
          color: {
            background: nodeColors[n.type] || nodeColors.default,
            border: nodeColors[n.type] || nodeColors.default,
            highlight: { background: '#fff', border: nodeColors[n.type] || nodeColors.default },
          },
          font: { color: '#e4e4ef', size: n.type === 'Agent' ? 14 : 11, ...(n.type === 'Agent' ? { bold: { color: '#e4e4ef' } } : {}) },
          shape: n.type === 'Agent' ? 'dot' : n.type === 'HireRequest' ? 'diamond' : 'box',
          size: n.label === 'Orchestrator' ? 35 : n.type === 'Agent' ? 28 : 15,
          title: `${n.type}: ${n.label}\n${Object.entries(n.properties).map(([k,v]) => `${k}: ${String(v).substring(0,80)}`).join('\n')}`,
          borderWidth: n.type === 'Agent' ? 3 : 1,
        }))
      );

      const edges = new vis.DataSet(
        graphData.edges.map((e, i) => ({
          id: `e-${i}`,
          from: e.source,
          to: e.target,
          color: { color: edgeColors[e.type] || edgeColors.default, highlight: '#fff' },
          arrows: 'to',
          label: e.type,
          font: { color: '#8888a0', size: 9, strokeWidth: 0 },
          smooth: { enabled: true, type: 'curvedCW', roundness: 0.2 },
        }))
      );

      const network = new vis.Network(
        containerRef.current!,
        { nodes, edges },
        {
          layout: {
            hierarchical: {
              enabled: true,
              direction: 'UD',
              sortMethod: 'hubsize',
              levelSeparation: 120,
              nodeSpacing: 180,
              treeSpacing: 200,
              blockShifting: true,
              edgeMinimization: true,
            },
          },
          physics: {
            enabled: true,
            hierarchicalRepulsion: {
              centralGravity: 0.0,
              springLength: 150,
              springConstant: 0.01,
              nodeDistance: 200,
            },
            stabilization: { iterations: 150 },
          },
          interaction: { hover: true, tooltipDelay: 200, navigationButtons: true, keyboard: true },
        }
      );

      network.on('click', (params: { nodes: string[] }) => {
        if (params.nodes.length) {
          const node = graphData.nodes.find((n) => n.id === params.nodes[0]);
          if (node) setSelected({ node });
        } else {
          setSelected(null);
        }
      });

      networkRef.current = network;
    })();

    return () => { cancelled = true; };
  }, [graphData]);

  return (
    <div className="flex gap-4 h-[calc(100vh-12rem)]">
      <div className="flex-1 flex flex-col gap-4">
        {/* Filter bar */}
        <div className="flex gap-3">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter by hire request ID..."
            className="flex-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500"
          />
          <button
            onClick={loadGraph}
            className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition"
          >
            Refresh
          </button>
        </div>

        {/* Legend */}
        <div className="flex gap-4 text-xs">
          {Object.entries(edgeColors).filter(([k]) => k !== 'default').map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5">
              <div className="w-4 h-0.5 rounded" style={{ background: color }} />
              <span className="text-[var(--text-secondary)]">{type}</span>
            </div>
          ))}
        </div>

        {/* Graph */}
        <div className="flex-1 rounded-xl bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-card)]/80 z-10">
              <div className="text-sm text-[var(--text-secondary)]">Loading graph...</div>
            </div>
          )}
          {error && !graphData.nodes.length && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-sm text-red-400">{error}</div>
            </div>
          )}
          <div ref={containerRef} className="w-full h-full" />
        </div>
      </div>

      {/* Sidebar */}
      {selected && (
        <div className="w-72 rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-5 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{ background: nodeColors[selected.node.type] || nodeColors.default, color: '#fff' }}
            >
              {selected.node.type}
            </span>
            <button
              onClick={() => setSelected(null)}
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm"
            >
              x
            </button>
          </div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{selected.node.label}</h3>
          <div className="space-y-2">
            {Object.entries(selected.node.properties).map(([key, val]) => (
              <div key={key}>
                <div className="text-xs text-[var(--text-secondary)]">{key}</div>
                <div className="text-sm text-[var(--text-primary)]">{String(val)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
