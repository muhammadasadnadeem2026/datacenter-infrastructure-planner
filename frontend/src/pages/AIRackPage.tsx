import { zodResolver } from '@hookform/resolvers/zod';
import { useMemo } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { FieldGrid } from '../components/forms/FieldGrid';
import { ErrorNote, Loading, PageHeader } from '../components/layouts/PageHeader';
import { CapacityTable } from '../components/results/CapacityTable';
import { Disclaimer } from '../components/results/Disclaimer';
import { ModuleDetails } from '../components/results/ModuleDetails';
import { Panel, SummaryGrid } from '../components/results/ResultsDashboard';
import { WarningsPanel } from '../components/results/WarningsPanel';
import { AREA_UNITS, PHASE_OPTIONS, REDUNDANCY_OPTIONS, type FieldDef } from '../constants/fields';
import { useToolCalculation } from '../hooks/useCalculation';
import { useAiRacks, useReceptacles } from '../hooks/useConstants';
import { selectUnitSystem, useProjectStore } from '../stores/projectStore';
import type { FullResponse } from '../types/api';
import { buildSchema } from '../utils/schemaBuilder';

const FIELDS: FieldDef[] = [
  { name: 'rack_count', label: 'Racks in cluster', type: 'number', integer: true, min: 1 },
  { name: 'rack_power_kw', label: 'Rack power', type: 'number', gt: 0, unit: 'kW' },
  { name: 'power_factor', label: 'Power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
  { name: 'pue', label: 'PUE', type: 'number', min: 1, step: 0.01 },
  { name: 'electricity_rate', label: 'Energy rate', type: 'number', min: 0, step: 0.001, unit: '/kWh' },
  { name: 'room_area', label: 'Room area', type: 'number', gt: 0, optional: true, placeholder: 'optional' },
  { name: 'room_area_unit', label: 'Unit', type: 'select', options: AREA_UNITS },
  {
    name: 'electrical.receptacle_id',
    label: 'Rack circuit',
    type: 'select',
    dynamicOptions: 'receptacles',
    width: 'full',
  },
  {
    name: 'electrical.voltage',
    label: 'Circuit voltage',
    type: 'number',
    gt: 0,
    unit: 'V',
    disabledIf: (v) => (v.electrical as { receptacle_id: string })?.receptacle_id !== 'custom',
  },
  {
    name: 'electrical.current',
    label: 'Circuit rating',
    type: 'number',
    gt: 0,
    unit: 'A',
    disabledIf: (v) => (v.electrical as { receptacle_id: string })?.receptacle_id !== 'custom',
  },
  {
    name: 'electrical.phase',
    label: 'Phase',
    type: 'select',
    options: PHASE_OPTIONS,
    disabledIf: (v) => (v.electrical as { receptacle_id: string })?.receptacle_id !== 'custom',
  },
  {
    name: 'electrical.continuous_derate',
    label: 'Continuous factor',
    type: 'number',
    gt: 0,
    max: 1,
    step: 0.01,
  },
  { name: 'electrical.circuits_per_rack', label: 'Existing circuits', type: 'number', integer: true, min: 0 },
  { name: 'pdu.voltage', label: 'PDU voltage', type: 'number', gt: 0, unit: 'V' },
  { name: 'pdu.amperage', label: 'PDU rating', type: 'number', gt: 0, unit: 'A' },
  { name: 'pdu.phase', label: 'PDU phase', type: 'select', options: PHASE_OPTIONS },
  {
    name: 'pdu.continuous_derate',
    label: 'PDU continuous factor',
    type: 'number',
    gt: 0,
    max: 1,
    step: 0.01,
  },
  { name: 'pdu.growth_margin_pct', label: 'Growth margin', type: 'number', min: 0, unit: '%' },
  {
    name: 'pdu.feed',
    label: 'Feeds',
    type: 'select',
    options: [
      { value: 'ab', label: 'A/B redundant' },
      { value: 'none', label: 'Single feed' },
    ],
  },
  { name: 'ups.target_load_pct', label: 'UPS target loading', type: 'number', gt: 0, max: 100, unit: '%' },
  { name: 'ups.redundancy', label: 'UPS redundancy', type: 'select', options: REDUNDANCY_OPTIONS },
  { name: 'ups.modules_n', label: 'UPS modules (n)', type: 'number', integer: true, min: 1 },
  { name: 'ups.module_kva', label: 'UPS module kVA (0 = auto)', type: 'number', min: 0 },
];

const DEFAULTS = {
  rack_count: 8,
  rack_power_kw: 120,
  power_factor: 0.95,
  pue: 1.25,
  electricity_rate: 0.1,
  room_area: 1200,
  room_area_unit: 'ft2',
  electrical: {
    receptacle_id: 'iec_60309_63a_415',
    voltage: 415,
    current: 63,
    phase: 'three',
    continuous_derate: 0.8,
    circuits_per_rack: 0,
  },
  pdu: {
    voltage: 415,
    amperage: 63,
    phase: 'three',
    continuous_derate: 0.8,
    growth_margin_pct: 10,
    feed: 'ab',
  },
  ups: { target_load_pct: 80, redundancy: 'N+1', modules_n: 3, module_kva: 0 },
};

export function AIRackPage() {
  const schema = useMemo(() => buildSchema(FIELDS), []);
  const form = useForm({ resolver: zodResolver(schema), defaultValues: DEFAULTS, mode: 'onChange' });
  const values = useWatch({ control: form.control });
  const parsed = schema.safeParse(values);
  const calc = useToolCalculation<FullResponse>('ai-rack', parsed.success ? parsed.data : null);
  const ai = useAiRacks();
  const receptacles = useReceptacles();
  const unit = useProjectStore(selectUnitSystem);
  const rackKw = useWatch({ control: form.control, name: 'rack_power_kw' });

  function onSelectChange(name: string, value: string) {
    if (name !== 'electrical.receptacle_id' || value === 'custom') return;
    const r = receptacles.data?.find((x) => x.id === value);
    if (!r) return;
    const o = { shouldValidate: true };
    form.setValue('electrical.voltage', r.voltage, o);
    form.setValue('electrical.current', r.amps, o);
    form.setValue('electrical.phase', r.phase, o);
    form.setValue('electrical.continuous_derate', r.continuous_derate, o);
  }

  return (
    <div>
      <PageHeader
        title="AI / GPU Cluster"
        description="Cluster load, facility power, cooling, circuits, PDUs, UPS, density and energy for identical high-density racks. The engine uses only the rack power value — vendor data is reference only."
      />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="min-w-0 space-y-3">
          <div className="card p-4">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
              Rack class presets (editable)
            </div>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {(ai.data?.classes ?? []).map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => form.setValue('rack_power_kw', c.typical_kw, { shouldValidate: true })}
                  className={`rounded-md border px-3 py-2 text-left ${Number(rackKw) === c.typical_kw ? 'border-accent-500 bg-accent-50' : 'border-slate-200'}`}
                >
                  <div className="text-sm font-medium">{c.name}</div>
                  <div className="text-xs text-slate-500">
                    {c.min_kw}
                    {c.max_kw ? `–${c.max_kw}` : '+'} kW · uses {c.typical_kw} kW · {c.cooling_type}
                  </div>
                </button>
              ))}
            </div>
          </div>
          <form className="card p-4" onSubmit={(e) => e.preventDefault()} noValidate>
            <FieldGrid form={form} fields={FIELDS} onSelectChange={onSelectChange} />
          </form>
          <div className="card p-4">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
              Equipment references
            </div>
            <ul className="space-y-2 text-xs text-slate-600">
              {(ai.data?.equipment_references ?? []).map((r) => (
                <li key={String(r.id)}>
                  <span className="font-medium text-slate-800">{String(r.platform)}</span> —{' '}
                  {String(r.rack_power_kw)} kW, {String(r.cooling_type)}.{' '}
                  <span className="text-slate-500">
                    {String(r.manufacturer)}; reviewed {r.review_date ? String(r.review_date) : 'not yet'}.{' '}
                    {String(r.notes ?? '')}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="min-w-0 space-y-4">
          {calc.isError && <ErrorNote>{(calc.error as Error).message}</ErrorNote>}
          {!calc.data && !calc.isError && <Loading />}
          {calc.data && (
            <div className={`space-y-4 ${calc.isFetching ? 'opacity-70' : ''}`}>
              <SummaryGrid result={calc.data} unitSystem={unit} />
              <Panel title="Engineering checks">
                <WarningsPanel warnings={calc.data.warnings} />
              </Panel>
              <Panel title="Capacity balance">
                <CapacityTable rows={calc.data.capacity.rows} bottleneck={calc.data.capacity.bottleneck} />
              </Panel>
              <Panel title="Calculation details">
                <ModuleDetails modules={calc.data.modules} />
              </Panel>
              <Disclaimer />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
