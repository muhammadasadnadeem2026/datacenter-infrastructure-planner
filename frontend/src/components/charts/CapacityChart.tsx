import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { SERIES_COLORS } from '../../constants/modules';
import { chartTheme, useThemeStore } from '../../stores/themeStore';
import { tooltipStyle } from '../../constants/charts';
import type { CapacityRow } from '../../types/api';
import { formatNumber } from '../../utils/format';

/** Loading of each configured system against its usable capacity (one axis, %). */
export function CapacityChart({ rows }: { rows: CapacityRow[] }) {
  const c = chartTheme(useThemeStore((s) => s.resolved));
  const data = rows
    .filter((r) => r.loading_pct !== null)
    .map((r) => ({ name: r.label, loading: r.loading_pct as number, status: r.status }));
  if (!data.length) return null;
  const max = Math.max(110, ...data.map((d) => d.loading)) * 1.05;
  return (
    <figure>
      <div style={{ height: data.length * 34 + 40 }} className="w-full">
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }}>
            <CartesianGrid horizontal={false} stroke={c.grid} />
            <XAxis
              type="number"
              domain={[0, Math.ceil(max / 10) * 10]}
              tickFormatter={(v: number) => `${v}%`}
              tick={{ fontSize: 11, fill: c.tick }}
              stroke={c.axis}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={112}
              tick={{ fontSize: 11, fill: c.label }}
              stroke={c.axis}
            />
            <Tooltip
              cursor={{ fill: c.cursor }}
              contentStyle={tooltipStyle}
              formatter={(v: number) => [`${formatNumber(v, '%')} %`, 'Loading']}
            />
            <ReferenceLine
              x={80}
              stroke="#D68C00"
              strokeDasharray="4 3"
              label={{ value: '80 %', position: 'top', fontSize: 10, fill: '#D68C00' }}
            />
            <ReferenceLine
              x={100}
              stroke="#DC3A3A"
              strokeDasharray="4 3"
              label={{ value: '100 %', position: 'top', fontSize: 10, fill: '#DC3A3A' }}
            />
            <Bar dataKey="loading" fill={SERIES_COLORS[0]} barSize={16} radius={[0, 4, 4, 0]}>
              <LabelList
                dataKey="loading"
                position="right"
                formatter={(v: number) => `${formatNumber(v, '%')}%`}
                style={{ fontSize: 11, fill: c.label }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="text-xs text-slate-500">
        Loading of usable capacity. Caution above 80 %, critical above 100 %.
      </figcaption>
    </figure>
  );
}
