import type { ReactNode } from 'react';
import type { FullResponse } from '../../types/api';
import type { UnitSystem } from '../../types/schemas';
import { findStep } from '../../utils/steps';
import { CapacityChart } from '../charts/CapacityChart';
import { EnergySankey } from '../charts/EnergySankey';
import { PowerFlowDiagram } from '../charts/PowerFlowDiagram';
import { CapacityTable } from './CapacityTable';
import { CircuitGauge } from './CircuitGauge';
import { Disclaimer } from './Disclaimer';
import { MetricCard } from './MetricCard';
import { AssumptionsList, ModuleDetails } from './ModuleDetails';
import { WarningsPanel } from './WarningsPanel';

export function Panel({ title, children, aside }: { title: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className="min-w-0 card p-4">
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-bold text-slate-800">
          <span className="h-3.5 w-1 rounded-full bg-accent-600" aria-hidden />
          {title}
        </h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

export function SummaryGrid({ result, unitSystem }: { result: FullResponse; unitSystem: UnitSystem }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4">
      {result.summary.map((card) => {
        const ref = card[unitSystem];
        const step = findStep(result.modules, ref.module, ref.key);
        return step ? <MetricCard key={card.id} label={card.label} step={step} /> : null;
      })}
    </div>
  );
}

export function ResultsDashboard({ result, unitSystem }: { result: FullResponse; unitSystem: UnitSystem }) {
  const counts = result.warnings.reduce<Record<string, number>>(
    (acc, w) => ({ ...acc, [w.severity]: (acc[w.severity] ?? 0) + 1 }),
    {},
  );
  return (
    <div className="space-y-4">
      <SummaryGrid result={result} unitSystem={unitSystem} />

      <Panel
        title="Engineering checks"
        aside={
          <span className="text-xs text-slate-500">
            {counts.critical ?? 0} critical · {counts.caution ?? 0} caution · {counts.info ?? 0} info
          </span>
        }
      >
        <WarningsPanel warnings={result.warnings} />
      </Panel>

      <Panel title="Infrastructure capacity balance">
        <CapacityTable rows={result.capacity.rows} bottleneck={result.capacity.bottleneck} />
        <div className="mt-4">
          <CapacityChart rows={result.capacity.rows} />
        </div>
      </Panel>

      {(result.modules.circuit || result.modules.pdu) && (
        <Panel title="Rack distribution loading">
          <div className="space-y-4">
            {result.modules.circuit && (
              <CircuitGauge module={result.modules.circuit} title="Branch circuit loading (of rating)" />
            )}
            {result.modules.pdu && (
              <CircuitGauge module={result.modules.pdu} title="PDU loading (design case)" />
            )}
          </div>
        </Panel>
      )}

      <div className="grid grid-cols-1 gap-4 2xl:grid-cols-2">
        <Panel title="Power flow">
          <PowerFlowDiagram nodes={result.power_flow.nodes} sources={result.power_flow.sources} />
        </Panel>
        <Panel title="Facility power split">
          <EnergySankey sankey={result.sankey} />
        </Panel>
      </div>

      <Panel
        title="Calculation details"
        aside={<span className="text-xs text-slate-500">engine v{result.engine_version}</span>}
      >
        <ModuleDetails modules={result.modules} />
      </Panel>

      <Panel title="Assumptions">
        <AssumptionsList modules={result.modules} />
      </Panel>

      <Disclaimer />
    </div>
  );
}
