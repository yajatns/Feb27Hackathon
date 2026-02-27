'use client';

import QueryChat from '@/components/QueryChat';

export default function QueryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Query</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Ask natural language questions. Uses Senso policies + LLM reasoning to answer.
        </p>
      </div>
      <QueryChat />
    </div>
  );
}
