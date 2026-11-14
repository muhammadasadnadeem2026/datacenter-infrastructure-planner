import { useState } from 'react';
import type { Step } from '../../types/api';
import { formatWithUnit } from '../../utils/format';
import { StepDetail } from './StepDetail';

export function StepRow({ step }: { step: Step }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="py-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-slate-700">{step.label}</span>
        <span className="flex items-baseline gap-2">
          <span className="whitespace-nowrap font-mono text-sm tabular-nums text-slate-900">
            {formatWithUnit(step.value, step.unit)}
          </span>
          <button
            type="button"
            className="whitespace-nowrap text-xs text-accent-600 hover:underline"
            aria-expanded={open}
            onClick={() => setOpen((o) => !o)}
          >
            {open ? 'Hide' : 'Show calculation'}
          </button>
        </span>
      </div>
      {open && (
        <div className="mt-1.5">
          <StepDetail step={step} />
        </div>
      )}
    </li>
  );
}
