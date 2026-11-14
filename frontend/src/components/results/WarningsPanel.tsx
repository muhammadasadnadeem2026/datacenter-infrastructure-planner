import { Link } from 'react-router-dom';
import type { EngineeringWarning } from '../../types/api';
import { StatusBadge } from './StatusBadge';

const border: Record<string, string> = {
  critical: 'border-l-red-500',
  caution: 'border-l-amber-500',
  info: 'border-l-sky-400',
};

export function WarningsPanel({ warnings }: { warnings: EngineeringWarning[] }) {
  if (!warnings.length)
    return (
      <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">No engineering warnings.</p>
    );
  return (
    <ul className="space-y-2">
      {warnings.map((w) => (
        <li
          key={w.code}
          className={`rounded-md border border-l-4 border-slate-200 bg-surface px-3 py-2 ${border[w.severity]}`}
        >
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={w.severity} />
            <span className="text-sm font-semibold text-slate-800">{w.title}</span>
            <span className="text-xs text-slate-400">
              {w.affected_system} · {w.code}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600">{w.message}</p>
          {w.reference && (
            <Link to={`/references#${w.reference}`} className="text-xs text-accent-600 underline">
              Reference: {w.reference}
            </Link>
          )}
        </li>
      ))}
    </ul>
  );
}
