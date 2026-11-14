import { zodResolver } from '@hookform/resolvers/zod';
import { useMemo } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { POWER_TABS } from '../../constants/navigation';
import type { ToolConfig } from '../../constants/tools';
import { useToolCalculation } from '../../hooks/useCalculation';
import { useReceptacles } from '../../hooks/useConstants';
import { selectUnitSystem, useProjectStore } from '../../stores/projectStore';
import type { ToolResponse } from '../../types/api';
import { buildSchema } from '../../utils/schemaBuilder';
import { findStep } from '../../utils/steps';
import { FieldGrid } from '../forms/FieldGrid';
import { ErrorNote, Loading, PageHeader } from '../layouts/PageHeader';
import { Disclaimer } from '../results/Disclaimer';
import { MetricCard } from '../results/MetricCard';
import { ModuleDetails } from '../results/ModuleDetails';
import { Panel } from '../results/ResultsDashboard';
import { WarningsPanel } from '../results/WarningsPanel';

/** Generic standalone calculator: form -> one backend endpoint -> traced results. */
export function ToolPage({ config }: { config: ToolConfig }) {
  const schema = useMemo(() => buildSchema(config.fields), [config.fields]);
  const unit = useProjectStore(selectUnitSystem);
  const receptacles = useReceptacles();
  const form = useForm({ resolver: zodResolver(schema), defaultValues: config.defaults, mode: 'onChange' });
  const values = useWatch({ control: form.control });
  const parsed = schema.safeParse(values);
  const body = parsed.success ? (config.buildRequest ? config.buildRequest(parsed.data) : parsed.data) : null;
  const calc = useToolCalculation<ToolResponse>(config.endpoint, body);

  function onSelectChange(name: string, value: string) {
    if (name !== 'receptacle_id' || value === 'custom') return;
    const r = receptacles.data?.find((x) => x.id === value);
    if (!r) return;
    const o = { shouldValidate: true };
    form.setValue('voltage', r.voltage, o);
    form.setValue('current', r.amps, o);
    form.setValue('phase', r.phase, o);
    form.setValue('continuous_derate', r.continuous_derate, o);
  }

  return (
    <div>
      <PageHeader
        title={config.title}
        description={config.description}
        tabs={config.group === 'power' ? POWER_TABS : undefined}
      />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <form className="min-w-0 card p-4" onSubmit={(e) => e.preventDefault()} noValidate>
          <FieldGrid form={form} fields={config.fields} onSelectChange={onSelectChange} />
        </form>
        <div className="min-w-0 space-y-4">
          {calc.isError && <ErrorNote>{(calc.error as Error).message}</ErrorNote>}
          {!calc.data && !calc.isError && <Loading />}
          {calc.data && (
            <div className={`space-y-4 ${calc.isFetching ? 'opacity-70' : ''}`}>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {config.highlights.map((h) => {
                  const step = findStep(
                    calc.data.modules,
                    h.module,
                    unit === 'metric' && h.metricKey ? h.metricKey : h.key,
                  );
                  return step ? (
                    <MetricCard key={`${h.module}.${h.key}`} label={step.label} step={step} />
                  ) : null;
                })}
              </div>
              <Panel title="Engineering checks">
                <WarningsPanel warnings={calc.data.warnings} />
              </Panel>
              <Panel
                title="Calculation details"
                aside={<span className="text-xs text-slate-500">engine v{calc.data.engine_version}</span>}
              >
                <ModuleDetails modules={calc.data.modules} openFirst />
              </Panel>
              <Disclaimer />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
