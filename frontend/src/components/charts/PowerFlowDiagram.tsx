import type { FlowMetric, FlowNode } from '../../types/api';
import { formatNumber } from '../../utils/format';

const W = 480;
const NODE_W = 230;
const NODE_H = 50;
const GAP = 22;
const MAIN_X = 20;
const SRC_X = 300;
const SRC_W = 160;

function metricText(m: FlowMetric) {
  if (m.value === null || m.value === undefined) return null;
  const v = formatNumber(m.value, m.unit);
  return `${m.label} ${v}${m.unit ? (m.unit === '%' ? ' %' : ` ${m.unit}`) : ''}`;
}

function NodeBox({
  x,
  y,
  w,
  node,
  dashed = false,
}: {
  x: number;
  y: number;
  w: number;
  node: FlowNode;
  dashed?: boolean;
}) {
  const lines = node.metrics.map(metricText).filter(Boolean) as string[];
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={NODE_H}
        rx={6}
        className={dashed ? 'fill-amber-50 stroke-amber-500' : 'fill-surface stroke-slate-300'}
        strokeWidth={1.5}
        strokeDasharray={dashed ? '4 3' : undefined}
      />
      <text x={x + 10} y={y + 18} className="fill-slate-800 text-[12px] font-semibold">
        {node.label}
      </text>
      <text x={x + 10} y={y + 36} className="fill-slate-600 font-mono text-[10px]">
        {lines.join(' · ')}
      </text>
      <title>{`${node.label}\n${lines.join('\n')}`}</title>
    </g>
  );
}

export function PowerFlowDiagram({ nodes, sources }: { nodes: FlowNode[]; sources: FlowNode[] }) {
  const chain = nodes.filter((n) => n.visible);
  const srcs = sources.filter((s) => s.visible);
  const lvIndex = chain.findIndex((n) => n.id === 'lv_switchgear');
  const height = chain.length * (NODE_H + GAP) - GAP + 10;
  const yOf = (i: number) => 5 + i * (NODE_H + GAP);

  return (
    <figure>
      <svg
        viewBox={`0 0 ${W} ${height}`}
        className="w-full"
        role="img"
        aria-label="Power flow single-line diagram"
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto"
          >
            <path d="M0,0 L10,5 L0,10 z" className="fill-slate-400" />
          </marker>
        </defs>
        {chain.slice(0, -1).map((n, i) => (
          <line
            key={`l-${n.id}`}
            x1={MAIN_X + NODE_W / 2}
            x2={MAIN_X + NODE_W / 2}
            y1={yOf(i) + NODE_H}
            y2={yOf(i + 1) - 2}
            className="stroke-slate-400"
            strokeWidth={2}
            markerEnd="url(#arrow)"
          />
        ))}
        {srcs.map((s, j) => {
          const sy = yOf(Math.max(lvIndex, 0)) + (j - (srcs.length - 1) / 2) * (NODE_H + 10);
          const ty = yOf(Math.max(lvIndex, 0)) + NODE_H / 2;
          return (
            <g key={s.id}>
              <path
                d={`M ${SRC_X} ${sy + NODE_H / 2} C ${SRC_X - 30} ${sy + NODE_H / 2}, ${MAIN_X + NODE_W + 30} ${ty}, ${MAIN_X + NODE_W + 2} ${ty}`}
                fill="none"
                className="stroke-amber-500"
                strokeWidth={2}
                strokeDasharray="5 4"
                markerEnd="url(#arrow)"
              />
              <NodeBox x={SRC_X} y={sy} w={SRC_W} node={s} dashed />
            </g>
          );
        })}
        {chain.map((n, i) => (
          <NodeBox key={n.id} x={MAIN_X} y={yOf(i)} w={NODE_W} node={n} />
        ))}
      </svg>
      <figcaption className="mt-1 text-xs text-slate-500">
        Normal path (solid) and standby / parallel sources (dashed). Nodes appear only when the equipment is
        configured.
      </figcaption>
    </figure>
  );
}
