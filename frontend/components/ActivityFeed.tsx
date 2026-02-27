'use client';

import { AgentStatus } from '@/lib/api';

const statusColors: Record<string, string> = {
  active: 'bg-green-500',
  idle: 'bg-yellow-500',
  working: 'bg-blue-500',
  completed: 'bg-green-500',
  error: 'bg-red-500',
};

export default function ActivityFeed({ agents }: { agents: AgentStatus[] }) {
  if (!agents.length) {
    return (
      <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-6">
        <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
          Recent Activity
        </h3>
        <p className="text-sm text-[var(--text-secondary)]">No recent activity. Submit a hire request to see agents in action.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-6">
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
        Agent Activity
      </h3>
      <div className="space-y-3">
        {agents.map((a) => (
          <div key={a.name} className="flex items-center gap-3 py-2">
            <span className={`w-2 h-2 rounded-full ${statusColors[a.status] || 'bg-gray-500'}`} />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-[var(--text-primary)]">{a.name}</div>
              <div className="text-xs text-[var(--text-secondary)] truncate">
                {a.current_task || a.status}
              </div>
            </div>
            {a.last_active && (
              <div className="text-xs text-[var(--text-secondary)]">
                {new Date(a.last_active).toLocaleTimeString()}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
