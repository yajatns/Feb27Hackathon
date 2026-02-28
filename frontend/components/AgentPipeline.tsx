'use client';

interface PipelineStep {
  name: string;
  status: 'pending' | 'running' | 'done' | 'error';
  detail?: string;
}

const agentInfo: Record<string, { emoji: string; tool: string }> = {
  'Maya (HR)': { emoji: '👩‍💼', tool: 'Senso' },
  'Sam (Finance)': { emoji: '📊', tool: 'Tavily' },
  'Compliance': { emoji: '⚖️', tool: 'Tavily + Senso' },
  'Alex (IT)': { emoji: '💻', tool: 'Yutori' },
  'Aria (Integrations)': { emoji: '🔗', tool: 'Airbyte' },
};

export default function AgentPipeline({ steps }: { steps: PipelineStep[] }) {
  return (
    <div className="rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🤖</span>
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Orchestrator is coordinating agents...</h3>
      </div>
      <div className="space-y-3">
        {steps.map((step) => {
          const info = agentInfo[step.name] || { emoji: '🤖', tool: '' };
          return (
            <div key={step.name} className={`flex items-center gap-3 rounded-lg px-4 py-3 border transition-all ${
              step.status === 'running' ? 'bg-brand-600/10 border-brand-500/30 shadow-sm shadow-brand-500/10' :
              step.status === 'done' ? 'bg-green-500/5 border-green-500/20' :
              step.status === 'error' ? 'bg-red-500/5 border-red-500/20' :
              'bg-[var(--bg-primary)] border-[var(--border)] opacity-50'
            }`}>
              <span className="text-xl w-8 text-center">{info.emoji}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${
                    step.status === 'running' ? 'text-brand-400' :
                    step.status === 'done' ? 'text-green-400' :
                    step.status === 'error' ? 'text-red-400' :
                    'text-[var(--text-secondary)]'
                  }`}>{step.name}</span>
                  {info.tool && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[var(--text-secondary)]">
                      via {info.tool}
                    </span>
                  )}
                </div>
                {step.detail && (
                  <div className={`text-xs mt-0.5 ${
                    step.status === 'running' ? 'text-brand-300' : 'text-[var(--text-secondary)]'
                  }`}>
                    {step.status === 'running' && <span className="inline-block animate-pulse mr-1">⚡</span>}
                    {step.detail}
                  </div>
                )}
              </div>
              <div className="shrink-0">
                {step.status === 'pending' && <span className="text-xs text-[var(--text-secondary)]">Waiting</span>}
                {step.status === 'running' && <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse inline-block" />}
                {step.status === 'done' && <span className="text-green-400 text-sm">✓</span>}
                {step.status === 'error' && <span className="text-red-400 text-sm">✗</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
