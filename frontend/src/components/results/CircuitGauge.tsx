import type { ModuleOut } from '../../types/api';
import { formatNumber } from '../../utils/format';
import { findStep } from '../../utils/steps';
import { StatusBadge } from './StatusBadge';

/** Linear loading gauge with the caution / critical limits returned by the engine. */
export function CircuitGauge({ module, title }: { module: ModuleOut; title: string }) {
  const load = findStep({ m: module }, 'm', 'loading_pct')?.value as number | undefined;
  const status = findStep({ m: module }, 'm', 'status')?.value as string | undefined;
  const limits = module.data.limits_pct as { caution: number; critical: number } | undefined;
  if (load === undefined || !limits) return null;
  const scale = Math.max(100, load);
  const pos = (v: number) => `${Math.min(v / scale, 1) * 100}%`;
  const bar = status === 'critical' ? 'bg-red-500' : status === 'caution' ? 'bg-amber-500' : 'bg-emerald-600';
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-slate-700">{title}</span>
        <span className="flex items-center gap-2">
          <span className="font-mono tabular-nums">{formatNumber(load, '%')} %</span>
          {status && <StatusBadge status={status} />}
        </span>
      </div>
      <div
        className="relative h-3 rounded-full bg-slate-100"
        role="meter"
        aria-valuenow={load}
        aria-valuemin={0}
        aria-valuemax={scale}
      >
        <div className={`h-3 rounded-full ${bar}`} style={{ width: pos(load) }} />
        {[limits.caution, limits.critical].map((l) => (
          <div key={l} className="absolute top-[-3px] h-[18px] w-0.5 bg-slate-500" style={{ left: pos(l) }} />
        ))}
      </div>
      <div className="relative mt-1 h-4 text-[10px] text-slate-500">
        <span className="absolute -translate-x-1/2" style={{ left: pos(limits.caution) }}>
          {formatNumber(limits.caution)} %
        </span>
        <span className="absolute -translate-x-1/2" style={{ left: pos(limits.critical) }}>
          {formatNumber(limits.critical)} %
        </span>
      </div>
    </div>
  );
}
