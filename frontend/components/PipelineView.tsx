'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, HireRequest } from '@/lib/api';

const agentMeta: Record<string, { emoji: string; color: string; tool: string }> = {
  Maya: { emoji: '👩‍💼', color: '#6366f1', tool: 'Senso (Policy KB)' },
  Sam: { emoji: '📊', color: '#22c55e', tool: 'Tavily (Market Research)' },
  Compliance: { emoji: '⚖️', color: '#eab308', tool: 'Tavily + Senso' },
  Alex: { emoji: '💻', color: '#06b6d4', tool: 'Yutori (Portal Automation)' },
  Aria: { emoji: '🔗', color: '#f97316', tool: 'Airbyte (600+ Connectors)' },
};

export default function PipelineView() {
  const searchParams = useSearchParams();
  const hireParam = searchParams.get('hire');
  const [hires, setHires] = useState<HireRequest[]>([]);
  const [selected, setSelected] = useState<HireRequest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listHires(10).then((h) => {
      setHires(h);
      const target = hireParam ? h.find(x => x.id === hireParam) : null;
      setSelected(target || h[0] || null);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [hireParam]);

  if (loading) return <div className="text-sm text-[var(--text-secondary)]">Loading pipelines...</div>;
  if (!hires.length) return <div className="text-sm text-[var(--text-secondary)]">No hire requests yet. Submit one from the Hire page.</div>;

  return (
    <div className="flex gap-6 h-[calc(100vh-12rem)]">
      {/* Hire list sidebar */}
      <div className="w-64 shrink-0 space-y-2 overflow-y-auto">
        <div className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-3">
          Select a Hire Request
        </div>
        {hires.map((h) => {
          const isRejected = h.reasoning_summary?.includes('🚨') || h.reasoning_summary?.includes('BLOCK') || h.reasoning_summary?.includes('REJECT');
          return (
            <button
              key={h.id}
              onClick={() => setSelected(h)}
              className={`w-full text-left px-3 py-2.5 rounded-lg border transition text-sm ${
                selected?.id === h.id
                  ? 'bg-brand-600/15 border-brand-500/30 text-brand-400'
                  : 'bg-[var(--bg-card)] border-[var(--border)] text-[var(--text-secondary)] hover:border-brand-500/20'
              }`}
            >
              <div className="font-medium text-[var(--text-primary)]">{h.employee_name}</div>
              <div className="text-xs mt-0.5">{h.role} · ${h.salary.toLocaleString()}</div>
              <div className="flex items-center gap-1.5 mt-1">
                <span className={`w-1.5 h-1.5 rounded-full ${isRejected ? 'bg-red-500' : 'bg-green-500'}`} />
                <span className="text-[10px]">{isRejected ? 'Flagged' : 'Approved'}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Pipeline view */}
      {selected && (
        <div className="flex-1 overflow-y-auto space-y-4">
          {/* Header */}
          <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-[var(--text-primary)]">{selected.employee_name}</h2>
                <p className="text-sm text-[var(--text-secondary)]">
                  {selected.role} · {selected.department} · ${selected.salary.toLocaleString()} · {selected.location}
                </p>
              </div>
              <span className="text-xs text-[var(--text-secondary)]">{new Date(selected.created_at).toLocaleString()}</span>
            </div>
          </div>

          {/* Flow: Orchestrator → Agents */}
          <div className="relative">
            {/* Orchestrator */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-brand-600 flex items-center justify-center text-white text-lg font-bold shrink-0">🤖</div>
              <div>
                <div className="text-sm font-semibold text-[var(--text-primary)]">Orchestrator</div>
                <div className="text-xs text-[var(--text-secondary)]">Delegated to {selected.tasks.length} specialist agents</div>
              </div>
            </div>

            {/* Vertical line */}
            <div className="ml-5 border-l-2 border-[var(--border)] pl-8 space-y-4">
              {selected.tasks.map((t, i) => {
                const meta = agentMeta[t.agent_name] || { emoji: '🤖', color: '#8888a0', tool: 'Unknown' };
                const hasFlag = t.output_data?.includes('🚨') || t.output_data?.includes('CRITICAL');
                const hasWarning = t.output_data?.includes('⚠️') || t.output_data?.includes('WARNING');

                return (
                  <div key={t.id} className="relative">
                    {/* Dot on the line */}
                    <div
                      className="absolute -left-[41px] top-3 w-3 h-3 rounded-full border-2 border-[var(--bg-primary)]"
                      style={{ backgroundColor: meta.color }}
                    />

                    <div className={`rounded-xl border p-4 ${
                      hasFlag ? 'bg-red-500/5 border-red-500/30' :
                      hasWarning ? 'bg-yellow-500/5 border-yellow-500/30' :
                      'bg-[var(--bg-card)] border-[var(--border)]'
                    }`}>
                      {/* Agent header */}
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">{meta.emoji}</span>
                        <span className="text-sm font-semibold text-[var(--text-primary)]">{t.agent_name}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-primary)] text-[var(--text-secondary)]">
                          {meta.tool}
                        </span>
                        {hasFlag && <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/15 text-red-400">🚨 FLAG</span>}
                      </div>

                      {/* Tools used */}
                      {t.tool_used && (
                        <div className="flex gap-1.5 mb-2 flex-wrap">
                          {t.tool_used.split(',').map(tool => (
                            <span key={tool.trim()} className="text-[10px] px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 font-mono">
                              🔧 {tool.trim()}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Reasoning */}
                      {t.output_data && (
                        <details open={hasFlag || i < 2}>
                          <summary className="text-xs text-[var(--text-secondary)] cursor-pointer hover:text-[var(--text-primary)] transition">
                            💭 Show reasoning
                          </summary>
                          <div className="mt-2 text-xs text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed bg-[var(--bg-primary)] rounded-lg p-3 border border-[var(--border)] max-h-48 overflow-y-auto">
                            {t.output_data}
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Final verdict */}
            <div className="ml-5 border-l-2 border-[var(--border)] pl-8 mt-4">
              <div className="relative">
                <div className="absolute -left-[41px] top-3 w-3 h-3 rounded-full border-2 border-[var(--bg-primary)] bg-white" />
                <div className={`rounded-xl border p-4 ${
                  selected.reasoning_summary?.includes('🚨') || selected.reasoning_summary?.includes('REJECT')
                    ? 'bg-red-500/10 border-red-500/30'
                    : 'bg-green-500/10 border-green-500/30'
                }`}>
                  <div className="text-sm font-semibold text-[var(--text-primary)] mb-2">
                    🏁 Final Decision
                  </div>
                  <div className="text-sm text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed">
                    {selected.reasoning_summary}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
