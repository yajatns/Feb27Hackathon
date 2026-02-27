'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import StatsCards from '@/components/StatsCards';
import ActivityFeed from '@/components/ActivityFeed';
import { api, PipelineStatus, HireRequest } from '@/lib/api';

export default function Dashboard() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [hires, setHires] = useState<HireRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, h] = await Promise.allSettled([api.getStatus(), api.listHires(5)]);
        if (s.status === 'fulfilled') setStatus(s.value);
        if (h.status === 'fulfilled') setHires(h.value);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const stats = [
    { label: 'Total Hires', value: hires.length || 0, sub: 'all time', color: 'text-brand-400' },
    { label: 'Active Agents', value: status?.agents.filter((a) => a.status === 'active').length ?? 4, sub: 'Maya, Sam, Compliance, Alex', color: 'text-green-400' },
    { label: 'Policy Updates', value: 12, sub: 'via Senso', color: 'text-yellow-400' },
    { label: 'Compliance Score', value: '96%', sub: 'last 30 days', color: 'text-emerald-400' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">AlexSaaS</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Back Office Dashboard</p>
        </div>
        <Link
          href="/hire"
          className="px-4 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition"
        >
          + New Hire
        </Link>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-[var(--bg-card)] border border-[var(--border)] animate-pulse" />
          ))}
        </div>
      ) : (
        <StatsCards stats={stats} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity */}
        <ActivityFeed agents={status?.agents || []} />

        {/* Recent Hires */}
        <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-6">
          <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
            Recent Hires
          </h3>
          {hires.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">No hire requests yet.</p>
          ) : (
            <div className="space-y-3">
              {hires.map((h) => (
                <Link key={h.id} href={`/hire/${h.id}`}
                  className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-primary)] rounded px-2 -mx-2 transition cursor-pointer">
                  <div>
                    <div className="text-sm font-medium text-[var(--text-primary)]">{h.employee_name}</div>
                    <div className="text-xs text-[var(--text-secondary)]">{h.role} · ${h.salary.toLocaleString()} · {h.tasks.length} agents</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      h.status === 'completed' ? 'bg-green-500/15 text-green-400' :
                      h.status === 'processing' ? 'bg-blue-500/15 text-blue-400' :
                      'bg-yellow-500/15 text-yellow-400'
                    }`}>
                      {h.status}
                    </span>
                    <span className="text-xs text-[var(--text-secondary)]">→</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
