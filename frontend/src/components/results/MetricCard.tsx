import { useState } from 'react';
import type { Step } from '../../types/api';
import { formatValue } from '../../utils/format';
import { StepDetail } from './StepDetail';

export function MetricCard({ label, step }: { label: string; step: Step }) {
  const [open, setOpen] = useState(false);
  const currency = /^[A-Z]{3}$/.test(step.unit);
  return (
    <div className="card group relative overflow-hidden p-3.5 transition hover:-translate-y-0.5 hover:border-accent-300 hover:shadow-lift">
      <span
        className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-accent-600 via-accent-400 to-transparent opacity-70"
        aria-hidden
      />
      <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500">{label}</div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span
          key={String(step.value)}
          className="animate-value-pulse font-mono text-xl font-semibold tabular-nums text-slate-900"
        >
          {formatValue(step.value, step.unit)}
        </span>
        {!currency && <span className="text-xs text-slate-500">{step.unit}</span>}
      </div>
      <button
        type="button"
        className="mt-1 text-xs font-medium text-accent-600 hover:underline"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? 'Hide calculation' : 'Show calculation'}
      </button>
      {open && (
        <div className="mt-2">
          <StepDetail step={step} stacked />
        </div>
      )}
    </div>
  );
}
