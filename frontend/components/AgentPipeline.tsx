'use client';

interface PipelineStep {
  name: string;
  status: 'pending' | 'running' | 'done' | 'error';
  detail?: string;
}

const statusStyle: Record<string, { dot: string; text: string; line: string }> = {
  pending: { dot: 'bg-gray-600', text: 'text-[var(--text-secondary)]', line: 'bg-gray-700' },
  running: { dot: 'bg-brand-500 animate-pulse-dot', text: 'text-brand-400', line: 'bg-brand-500/50' },
  done: { dot: 'bg-green-500', text: 'text-green-400', line: 'bg-green-500' },
  error: { dot: 'bg-red-500', text: 'text-red-400', line: 'bg-red-500' },
};

export default function AgentPipeline({ steps }: { steps: PipelineStep[] }) {
  return (
    <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-6">
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-5">
        Agent Pipeline
      </h3>
      <div className="flex items-start gap-0">
        {steps.map((step, i) => {
          const s = statusStyle[step.status];
          return (
            <div key={step.name} className="flex items-start flex-1 min-w-0">
              <div className="flex flex-col items-center">
                <div className={`w-4 h-4 rounded-full ${s.dot} ring-2 ring-offset-2 ring-offset-[var(--bg-card)] ${
                  step.status === 'running' ? 'ring-brand-500/40' : 'ring-transparent'
                }`} />
                <div className="mt-2 text-center">
                  <div className={`text-xs font-medium ${s.text}`}>{step.name}</div>
                  {step.detail && (
                    <div className="text-xs text-[var(--text-secondary)] mt-0.5 max-w-[100px] truncate">
                      {step.detail}
                    </div>
                  )}
                </div>
              </div>
              {i < steps.length - 1 && (
                <div className={`h-0.5 flex-1 mt-2 mx-2 rounded ${s.line}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
