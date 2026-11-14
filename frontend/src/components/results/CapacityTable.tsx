import type { Bottleneck, CapacityRow } from '../../types/api';
import { formatNumber } from '../../utils/format';
import { StatusBadge } from './StatusBadge';

const n = (v: number | null, unit = '') => (v === null ? '—' : formatNumber(v, unit));

export function CapacityTable({ rows, bottleneck }: { rows: CapacityRow[]; bottleneck: Bottleneck | null }) {
  return (
    <div>
      {bottleneck && (
        <div
          className={`mb-3 rounded-md px-3 py-2 text-sm ${
            bottleneck.status === 'critical'
              ? 'bg-red-50 text-red-800'
              : bottleneck.status === 'caution'
                ? 'bg-amber-50 text-amber-900'
                : 'bg-accent-50 text-accent-800'
          }`}
        >
          <strong>System bottleneck: {bottleneck.label}.</strong> {bottleneck.message}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
              <th className="py-1.5 pr-2 font-medium">System</th>
              <th className="px-2 py-1.5 text-right font-medium">Required</th>
              <th className="px-2 py-1.5 text-right font-medium">Installed</th>
              <th className="px-2 py-1.5 text-right font-medium">Usable</th>
              <th className="px-2 py-1.5 text-right font-medium">Loading</th>
              <th className="px-2 py-1.5 text-right font-medium">Reserve</th>
              <th className="px-2 py-1.5 font-medium">Redund.</th>
              <th className="py-1.5 pl-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="font-mono tabular-nums">
            {rows.map((r) => (
              <tr
                key={r.system}
                className={`border-b border-slate-100 ${bottleneck?.system === r.system ? 'bg-accent-50/60' : ''}`}
                title={r.note}
              >
                <td className="py-1.5 pr-2 font-sans text-slate-800">
                  {r.label}
                  <span className="ml-1 text-xs text-slate-400">{r.unit}</span>
                </td>
                <td className="px-2 py-1.5 text-right">{n(r.required)}</td>
                <td className="px-2 py-1.5 text-right">{n(r.installed)}</td>
                <td className="px-2 py-1.5 text-right">{n(r.usable)}</td>
                <td className="px-2 py-1.5 text-right">
                  {r.loading_pct === null ? '—' : `${formatNumber(r.loading_pct, '%')} %`}
                </td>
                <td className="px-2 py-1.5 text-right">{n(r.reserve)}</td>
                <td className="px-2 py-1.5 font-sans text-slate-600">{r.redundancy}</td>
                <td className="py-1.5 pl-2 font-sans">
                  <StatusBadge status={r.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        Each row compares like units (kW, kVA, kW thermal, MW, MWh), so power factor is applied within the
        row. Loading is against usable capacity with redundant units held in reserve.
      </p>
    </div>
  );
}
