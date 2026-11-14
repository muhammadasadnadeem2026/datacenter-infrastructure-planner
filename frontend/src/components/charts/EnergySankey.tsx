import { Layer, Rectangle, ResponsiveContainer, Sankey, Tooltip } from 'recharts';
import { SERIES_COLORS } from '../../constants/modules';
import { chartTheme, useThemeStore } from '../../stores/themeStore';
import { tooltipStyle } from '../../constants/charts';
import type { FullResponse } from '../../types/api';
import { formatNumber } from '../../utils/format';

interface NodeProps {
  x: number;
  y: number;
  width: number;
  height: number;
  index: number;
  payload: { name: string; value: number };
  containerWidth: number;
}

function SankeyNode({ x, y, width, height, index, payload, containerWidth }: NodeProps) {
  const isSource = index === 0;
  const color = isSource ? '#6C7CD7' : SERIES_COLORS[(index - 1) % SERIES_COLORS.length];
  const labelRight = !isSource && x + width + 6 < containerWidth;
  return (
    <Layer>
      <Rectangle x={x} y={y} width={width} height={Math.max(height, 2)} fill={color} radius={2} />
      <text
        x={labelRight ? x + width + 6 : x - 6}
        y={y + height / 2}
        textAnchor={labelRight ? 'start' : 'end'}
        dominantBaseline="middle"
        className="fill-slate-700 text-[11px]"
      >
        {payload.name}: {formatNumber(payload.value)} kW
      </text>
    </Layer>
  );
}

export function EnergySankey({ sankey }: { sankey: FullResponse['sankey'] }) {
  const c = chartTheme(useThemeStore((s) => s.resolved));
  if (!sankey.links.length) return null;
  return (
    <figure>
      <div className="h-56 w-full">
        <ResponsiveContainer>
          <Sankey
            data={sankey}
            nodeWidth={10}
            nodePadding={18}
            margin={{ top: 8, bottom: 8, left: 160, right: 170 }}
            link={{ stroke: c.link, strokeOpacity: 0.55 }}
            node={(p: NodeProps) => <SankeyNode {...p} />}
          >
            <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => `${formatNumber(v)} kW`} />
          </Sankey>
        </ResponsiveContainer>
      </div>
      <figcaption className="mt-1 text-xs text-slate-500">
        {sankey.split_given
          ? 'Overhead split uses the shares you entered under Facility / PUE.'
          : 'PUE alone does not identify the cooling / electrical-loss split, so all non-IT power is shown as Facility Overhead.'}
      </figcaption>
    </figure>
  );
}
