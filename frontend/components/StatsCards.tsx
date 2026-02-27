'use client';

interface Stat {
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}

export default function StatsCards({ stats }: { stats: Stat[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((s) => (
        <div
          key={s.label}
          className="card-glow rounded-xl bg-[var(--bg-card)] border border-[var(--border)] p-5 transition-all"
        >
          <div className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-2">
            {s.label}
          </div>
          <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
          {s.sub && (
            <div className="text-xs text-[var(--text-secondary)] mt-1">{s.sub}</div>
          )}
        </div>
      ))}
    </div>
  );
}
