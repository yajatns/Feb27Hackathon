'use client';

import HireForm from '@/components/HireForm';

export default function HirePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">New Hire Request</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Submit a hire request. The AI agent pipeline (Maya → Sam → Compliance → Alex) will process it automatically.
        </p>
      </div>
      <HireForm />
    </div>
  );
}
