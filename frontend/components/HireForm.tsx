'use client';

import { useState } from 'react';
import { api, HireRequestCreate, HireRequest, connectStream } from '@/lib/api';
import AgentPipeline from './AgentPipeline';

const AGENTS = ['Maya (HR)', 'Sam (Finance)', 'Compliance', 'Alex (IT)'];

export default function HireForm() {
  const [form, setForm] = useState<HireRequestCreate>({
    employee_name: '',
    role: '',
    department: 'Engineering',
    salary: 120000,
    location: 'San Francisco, CA',
    start_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<HireRequest | null>(null);
  const [error, setError] = useState('');
  const [pipelineSteps, setPipelineSteps] = useState<{ name: string; status: 'pending' | 'running' | 'done' | 'error'; detail?: string }[]>(
    AGENTS.map((name) => ({ name, status: 'pending' }))
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setResult(null);
    setPipelineSteps(AGENTS.map((name) => ({ name, status: 'pending' as const })));

    // Connect WebSocket for real-time updates
    let stepIndex = 0;
    const ws = connectStream((msg) => {
      if (msg.type === 'agent_start' || msg.type === 'agent_progress') {
        setPipelineSteps((prev) =>
          prev.map((s, i) => {
            if (i === stepIndex) return { ...s, status: 'running', detail: String(msg.data.task || '') };
            if (i < stepIndex) return { ...s, status: 'done' };
            return s;
          })
        );
      }
      if (msg.type === 'agent_complete') {
        setPipelineSteps((prev) =>
          prev.map((s, i) => (i === stepIndex ? { ...s, status: 'done' } : s))
        );
        stepIndex++;
      }
    });

    try {
      // Simulate pipeline progress for demo
      for (let i = 0; i < AGENTS.length; i++) {
        setPipelineSteps((prev) =>
          prev.map((s, j) => {
            if (j === i) return { ...s, status: 'running' };
            if (j < i) return { ...s, status: 'done' };
            return s;
          })
        );
        await new Promise((r) => setTimeout(r, 800));
      }
      setPipelineSteps((prev) => prev.map((s) => ({ ...s, status: 'done' })));

      const hire = await api.hire(form);
      setResult(hire);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit hire request');
      setPipelineSteps((prev) =>
        prev.map((s) => (s.status === 'running' ? { ...s, status: 'error' } : s))
      );
    } finally {
      setSubmitting(false);
      ws.close();
    }
  };

  const update = (field: keyof HireRequestCreate, value: string | number) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="max-w-2xl space-y-6">
      <form onSubmit={handleSubmit} className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-6 space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Employee Name</label>
            <input
              required
              value={form.employee_name}
              onChange={(e) => update('employee_name', e.target.value)}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500 transition"
              placeholder="Sarah Chen"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Role</label>
            <input
              required
              value={form.role}
              onChange={(e) => update('role', e.target.value)}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500 transition"
              placeholder="Senior Engineer"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Department</label>
            <select
              value={form.department}
              onChange={(e) => update('department', e.target.value)}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500 transition"
            >
              {['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations'].map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Salary ($)</label>
            <input
              required
              type="number"
              value={form.salary}
              onChange={(e) => update('salary', Number(e.target.value))}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500 transition"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Location</label>
            <input
              required
              value={form.location}
              onChange={(e) => update('location', e.target.value)}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500 transition"
              placeholder="San Francisco, CA"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Start Date</label>
            <input
              required
              type="date"
              value={form.start_date}
              onChange={(e) => update('start_date', e.target.value)}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500 transition"
            />
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? 'Processing...' : 'Submit Hire Request'}
        </button>
      </form>

      {/* Pipeline Progress */}
      {submitting && <AgentPipeline steps={pipelineSteps} />}

      {/* Result — Pipeline Log */}
      {result && (
        <div className="space-y-4">
          {/* Final Verdict */}
          <div className={`rounded-xl border p-5 ${
            result.reasoning_summary?.includes('🚨') || result.reasoning_summary?.includes('BLOCK')
              ? 'bg-red-500/10 border-red-500/30'
              : result.reasoning_summary?.includes('⚠️') || result.reasoning_summary?.includes('WARNING')
              ? 'bg-yellow-500/10 border-yellow-500/30'
              : 'bg-green-500/10 border-green-500/30'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{
                result.reasoning_summary?.includes('🚨') || result.reasoning_summary?.includes('BLOCK') ? '🚨' :
                result.reasoning_summary?.includes('⚠️') ? '⚠️' : '✅'
              }</span>
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                Orchestrator Decision — {result.employee_name} as {result.role}
              </span>
            </div>
            <div className="text-sm text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed">
              {result.reasoning_summary}
            </div>
          </div>

          {/* Agent Pipeline Log */}
          <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
            <div className="px-5 py-3 border-b border-[var(--border)]">
              <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
                Agent Pipeline Log — {result.tasks.length} agents invoked
              </span>
            </div>
            <div className="divide-y divide-[var(--border)]">
              {result.tasks.map((t) => {
                const emoji = t.agent_name === 'Maya' ? '👩‍💼' : t.agent_name === 'Sam' ? '📊' : t.agent_name === 'Compliance' ? '⚖️' : t.agent_name === 'Alex' ? '💻' : t.agent_name === 'Aria' ? '🔗' : '🤖';
                const hasFlag = t.output_data?.includes('🚨') || t.output_data?.includes('CRITICAL') || t.output_data?.includes('WARNING');
                return (
                  <details key={t.id} className="group" open={hasFlag}>
                    <summary className="flex items-center gap-3 px-5 py-3 cursor-pointer hover:bg-[var(--bg-primary)] transition">
                      <span className="text-lg">{emoji}</span>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-[var(--text-primary)]">{t.agent_name}</span>
                        <span className="text-xs text-[var(--text-secondary)] ml-2">
                          {t.tool_used ? `🔧 ${t.tool_used}` : '🧠 reasoning only'}
                        </span>
                      </div>
                      <span className={`w-2 h-2 rounded-full ${
                        t.status === 'completed' ? (hasFlag ? 'bg-yellow-500' : 'bg-green-500') : 'bg-red-500'
                      }`} />
                    </summary>
                    <div className="px-5 pb-4 pl-12">
                      {t.output_data && (
                        <div className="text-xs text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed bg-[var(--bg-primary)] rounded-lg p-3 border border-[var(--border)]">
                          {t.output_data}
                        </div>
                      )}
                    </div>
                  </details>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
