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

      {/* Result */}
      {result && (
        <div className="rounded-xl bg-[var(--bg-card)] border border-green-500/30 p-6 space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-sm font-medium text-green-400">Hire Request Processed</span>
          </div>
          <div className="text-sm text-[var(--text-primary)]">
            <strong>{result.employee_name}</strong> — {result.role}, {result.department}
          </div>
          <div className="text-sm text-[var(--text-secondary)]">
            Status: {result.status}
          </div>
          {result.reasoning_summary && (
            <div className="mt-3 p-4 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]">
              <div className="text-xs font-medium text-[var(--text-secondary)] uppercase mb-2">Reasoning Summary</div>
              <div className="text-sm text-[var(--text-primary)] whitespace-pre-wrap">{result.reasoning_summary}</div>
            </div>
          )}
          {result.tasks.length > 0 && (
            <div className="mt-3 space-y-2">
              <div className="text-xs font-medium text-[var(--text-secondary)] uppercase">Agent Tasks</div>
              {result.tasks.map((t) => (
                <div key={t.id} className="flex items-center gap-2 text-xs">
                  <span className={`w-1.5 h-1.5 rounded-full ${t.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                  <span className="text-[var(--text-primary)]">{t.agent_name}</span>
                  <span className="text-[var(--text-secondary)]">via {t.tool_used}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
