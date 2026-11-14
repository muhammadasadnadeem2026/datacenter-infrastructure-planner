import { useState } from 'react';
import { ErrorNote, Loading, PageHeader } from '../components/layouts/PageHeader';
import { StepDetail } from '../components/results/StepDetail';
import { POWER_TABS } from '../constants/navigation';
import { useToolCalculation } from '../hooks/useCalculation';
import { useConversions } from '../hooks/useConstants';
import type { ToolResponse } from '../types/api';
import { formatWithUnit } from '../utils/format';
import { findStep } from '../utils/steps';

const input =
  'w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm font-mono focus:border-accent-500 focus:outline-none';

export function UnitsConverterPage() {
  const conversions = useConversions();
  const [conversion, setConversion] = useState('kw_to_btu_hr');
  const [value, setValue] = useState('100');
  const [voltage, setVoltage] = useState('480');
  const [phase, setPhase] = useState<'single' | 'three'>('three');
  const [pf, setPf] = useState('0.95');

  const def = conversions.data?.find((c) => c.id === conversion);
  const needs = def?.needs ?? [];
  const num = (s: string) => (s.trim() === '' ? NaN : Number(s));
  const body: Record<string, unknown> = { conversion, value: num(value) };
  if (needs.includes('voltage')) body.voltage = num(voltage);
  if (needs.includes('phase')) body.phase = phase;
  if (needs.includes('power_factor')) body.power_factor = num(pf);
  const valid = Object.values(body).every((v) => typeof v !== 'number' || Number.isFinite(v));
  const calc = useToolCalculation<ToolResponse>('convert', def && valid ? body : null);
  const step = findStep(calc.data?.modules, 'convert', 'result');

  return (
    <div>
      <PageHeader
        title="Unit Converter"
        description="Temperature, area, power, heat and electrical conversions."
        tabs={POWER_TABS}
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-3 card p-4">
          <label className="block text-xs font-medium text-slate-600">
            Conversion
            <select
              className={`${input} mt-1 font-sans`}
              value={conversion}
              onChange={(e) => setConversion(e.target.value)}
            >
              {(conversions.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Value ({def?.from_unit})
            <input
              className={`${input} mt-1`}
              type="number"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </label>
          {needs.includes('voltage') && (
            <label className="block text-xs font-medium text-slate-600">
              Voltage (V)
              <input
                className={`${input} mt-1`}
                type="number"
                value={voltage}
                onChange={(e) => setVoltage(e.target.value)}
              />
            </label>
          )}
          {needs.includes('phase') && (
            <label className="block text-xs font-medium text-slate-600">
              Phase
              <select
                className={`${input} mt-1 font-sans`}
                value={phase}
                onChange={(e) => setPhase(e.target.value as 'single' | 'three')}
              >
                <option value="single">Single-phase</option>
                <option value="three">Three-phase</option>
              </select>
            </label>
          )}
          {needs.includes('power_factor') && (
            <label className="block text-xs font-medium text-slate-600">
              Power factor
              <input
                className={`${input} mt-1`}
                type="number"
                step="0.01"
                value={pf}
                onChange={(e) => setPf(e.target.value)}
              />
            </label>
          )}
          {!valid && <p className="text-xs text-red-600">Enter finite numeric values.</p>}
        </div>
        <div className="space-y-3">
          {calc.isError && <ErrorNote>{(calc.error as Error).message}</ErrorNote>}
          {!step && !calc.isError && <Loading />}
          {step && (
            <div className="card p-4">
              <div className="text-xs uppercase tracking-wide text-slate-500">Result</div>
              <div className="my-1 font-mono text-2xl font-semibold tabular-nums">
                {formatWithUnit(step.value, step.unit)}
              </div>
              <StepDetail step={step} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
