'use client';

import GraphViewer from '@/components/GraphViewer';

export default function GraphPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Reasoning Graph</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Neo4j-powered visualization of agent decisions, delegations, and learned policies.
        </p>
      </div>
      <GraphViewer />
    </div>
  );
}
