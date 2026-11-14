import { Link } from 'react-router-dom';
import type { Step } from '../../types/api';
import { formatWithUnit } from '../../utils/format';

/** The derivation of one engine result: formula, substitution, result, assumption, reference. */
export function StepDetail({ step, stacked = false }: { step: Step; stacked?: boolean }) {
  const layout = stacked ? 'grid-cols-1 [&_dd]:mb-1.5' : 'grid-cols-[6.5rem_minmax(0,1fr)]';
  return (
    <dl className={`grid ${layout} gap-x-3 gap-y-0.5 rounded-md bg-slate-50 p-3 text-xs`}>
      <dt className="text-slate-500">Formula</dt>
      <dd className="font-mono text-slate-800">{step.formula}</dd>
      <dt className="text-slate-500">Calculation</dt>
      <dd className="break-words font-mono text-slate-800">
        {step.substitution} = <strong>{formatWithUnit(step.value, step.unit)}</strong>
      </dd>
      {step.assumption && (
        <>
          <dt className="text-slate-500">Assumption</dt>
          <dd className="text-slate-700">{step.assumption}</dd>
        </>
      )}
      {step.reference && (
        <>
          <dt className="text-slate-500">Reference</dt>
          <dd>
            <Link className="text-accent-600 underline" to={`/references#${step.reference}`}>
              {step.reference}
            </Link>
          </dd>
        </>
      )}
    </dl>
  );
}
