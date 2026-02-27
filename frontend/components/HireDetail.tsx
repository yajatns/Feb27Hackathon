'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api, HireRequest } from '@/lib/api';

const agentEmoji: Record<string, string> = {
  Maya: '👩‍💼', Sam: '📊', Compliance: '⚖️', Alex: '💻', Aria: '🔗',
};

export default function HireDetail() {
  const params = useParams();
  const id = params.id as string;
  const [hire, setHire] = useState<HireRequest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHire(id).then(setHire).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="text-sm text-[var(--text-secondary)]">Loading pipeline...</div>;
  if (!hire) return <div className="text-sm text-red-400">Hire request not found.</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/" className="text-xs text-brand-400 hover:text-brand-300">← Dashboard</Link>
        <span className="text-xs text-[var(--text-secondary)]">/</span>
        <span className="text-xs text-[var(--text-secondary)]">Pipeline Log</span>
      </div>

      <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">{hire.employee_name}</h1>
            <p className="text-sm text-[var(--text-secondary)]">{hire.role} · {hire.department} · ${hire.salary.toLocaleString()}</p>
            <p className="text-xs text-[var(--text-secondary)] mt-1">{hire.location} · Start: {hire.start_date}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            hire.status === 'completed' ? 'bg-green-500/15 text-green-400' :
            hire.status === 'failed' ? 'bg-red-500/15 text-red-400' :
            'bg-blue-500/15 text-blue-400 animate-pulse'
          }`}>{hire.status}</span>
        </div>
      </div>

      {hire.reasoning_summary && (
        <div className={`rounded-xl border p-5 ${
          hire.reasoning_summary.includes('🚨') || hire.reasoning_summary.includes('BLOCK')
            ? 'bg-red-500/10 border-red-500/30'
            : hire.reasoning_summary.includes('⚠️')
            ? 'bg-yellow-500/10 border-yellow-500/30'
            : 'bg-green-500/10 border-green-500/30'
        }`}>
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">🤖 Orchestrator Decision</h3>
          <div className="text-sm text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed">{hire.reasoning_summary}</div>
        </div>
      )}

      <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
        <div className="px-5 py-3 border-b border-[var(--border)]">
          <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
            Agent Pipeline — {hire.tasks.length} agents
          </span>
        </div>
        <div className="divide-y divide-[var(--border)]">
          {hire.tasks.map((t, i) => {
            const emoji = agentEmoji[t.agent_name] || '🤖';
            const hasFlag = t.output_data?.includes('🚨') || t.output_data?.includes('CRITICAL');
            return (
              <details key={t.id} open>
                <summary className="flex items-center gap-3 px-5 py-3 cursor-pointer hover:bg-[var(--bg-primary)] transition">
                  <span className="text-base w-6 text-center">{emoji}</span>
                  <span className="text-xs text-[var(--text-secondary)] w-5">{i + 1}.</span>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-[var(--text-primary)]">{t.agent_name}</span>
                    {t.tool_used && (
                      <div className="flex gap-1 mt-0.5 flex-wrap">
                        {t.tool_used.split(',').map(tool => (
                          <span key={tool.trim()} className="text-[10px] px-1.5 py-0.5 rounded bg-brand-500/15 text-brand-400">
                            🔧 {tool.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className={`w-2 h-2 rounded-full ${t.status === 'completed' ? (hasFlag ? 'bg-yellow-500' : 'bg-green-500') : 'bg-red-500'}`} />
                </summary>
                <div className="px-5 pb-4 pl-14">
                  {t.output_data && (
                    <div className="text-xs text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed bg-[var(--bg-primary)] rounded-lg p-3 border border-[var(--border)]">
                      💭 {t.output_data}
                    </div>
                  )}
                </div>
              </details>
            );
          })}
        </div>
      </div>
    </div>
  );
}
