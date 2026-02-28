'use client';

import { Suspense, useState } from 'react';
import GraphViewer from '@/components/GraphViewer';
import PipelineView from '@/components/PipelineView';

function GraphContent() {
  const [tab, setTab] = useState<'pipeline' | 'graph'>('pipeline');

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Agent Reasoning</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          See how agents reasoned, which tools they used, and what they decided.
        </p>
      </div>

      <div className="flex gap-1 bg-[var(--bg-secondary)] rounded-lg p-1 w-fit">
        <button
          onClick={() => setTab('pipeline')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
            tab === 'pipeline' ? 'bg-brand-600 text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          📋 Pipeline View
        </button>
        <button
          onClick={() => setTab('graph')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
            tab === 'graph' ? 'bg-brand-600 text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          🕸️ Neo4j Graph
        </button>
      </div>

      {tab === 'pipeline' ? <PipelineView /> : <GraphViewer />}
    </div>
  );
}

export default function GraphPage() {
  return (
    <Suspense fallback={<div className="text-sm text-[var(--text-secondary)]">Loading...</div>}>
      <GraphContent />
    </Suspense>
  );
}
