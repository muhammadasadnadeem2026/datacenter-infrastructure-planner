import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { visibleAt } from '../../constants/fields';
import { SECTIONS } from '../../constants/sections';
import { usePresets, useReceptacles } from '../../hooks/useConstants';
import { useProjectStore } from '../../stores/projectStore';
import { projectInputsSchema, type Mode, type ProjectInputs } from '../../types/schemas';
import { DeviceTable } from '../forms/DeviceTable';
import { FieldGrid } from '../forms/FieldGrid';
import { Section } from '../forms/Section';

const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: 'quick', label: 'Quick', hint: 'Racks, kW/rack, PF, PUE' },
  { id: 'standard', label: 'Standard', hint: '+ electrical, UPS, cooling, PDU, area, energy' },
  { id: 'engineering', label: 'Engineering', hint: '+ transformer, generator, BESS, environment' },
];

interface Props {
  initial: ProjectInputs;
  deviceWatts: (number | undefined)[];
}

export function CalculatorForm({ initial, deviceWatts }: Props) {
  const setInputs = useProjectStore((s) => s.setInputs);
  const replaceInputs = useProjectStore((s) => s.replaceInputs);
  const revision = useProjectStore((s) => s.revision);
  const dirty = useProjectStore((s) => s.dirty);
  const presets = usePresets();
  const receptacles = useReceptacles();

  const form = useForm<ProjectInputs>({
    resolver: zodResolver(projectInputsSchema),
    defaultValues: initial,
    mode: 'onChange',
  });

  // Inputs replaced from outside (preset, project load, import) -> reset the form.
  useEffect(() => {
    const next = useProjectStore.getState().inputs;
    if (next) form.reset(next);
  }, [revision, form]);

  // Every valid change propagates to the store; the results panel recalculates (debounced).
  useEffect(() => {
    const sub = form.watch((values) => {
      const parsed = projectInputsSchema.safeParse(values);
      if (parsed.success) setInputs(parsed.data);
    });
    return () => sub.unsubscribe();
  }, [form, setInputs]);

  const mode = useWatch({ control: form.control, name: 'mode' });
  const inputMode = useWatch({ control: form.control, name: 'it.input_mode' });
  const presetId = useWatch({ control: form.control, name: 'preset' });

  function applyPreset(id: string) {
    const p = presets.data?.find((x) => x.id === id);
    if (!p) return;
    if (dirty && !window.confirm(`Replace the current inputs with the "${p.name}" preset?`)) return;
    const current = form.getValues();
    replaceInputs({ ...p.inputs, mode: current.mode, unit_system: current.unit_system });
  }

  function onSelectChange(name: string, value: string) {
    if (name !== 'electrical.receptacle_id' || value === 'custom') return;
    const r = receptacles.data?.find((x) => x.id === value);
    if (!r) return;
    const opts = { shouldValidate: true, shouldDirty: true };
    form.setValue('electrical.voltage', r.voltage, opts);
    form.setValue('electrical.current', r.amps, opts);
    form.setValue('electrical.phase', r.phase, opts);
    form.setValue('electrical.continuous_derate', r.continuous_derate, opts);
  }

  return (
    <form className="space-y-3" onSubmit={(e) => e.preventDefault()} noValidate>
      <div className="card p-3">
        <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Design mode</div>
        <div
          className="grid grid-cols-3 gap-1 rounded-md bg-slate-100 p-1"
          role="radiogroup"
          aria-label="Design mode"
        >
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              role="radio"
              aria-checked={mode === m.id}
              title={m.hint}
              onClick={() => form.setValue('mode', m.id, { shouldDirty: true })}
              className={`rounded px-2 py-1.5 text-sm font-medium ${
                mode === m.id ? 'bg-surface text-accent-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        <p className="mt-1.5 text-xs text-slate-500">{MODES.find((m) => m.id === mode)?.hint}</p>
      </div>

      {SECTIONS.filter((s) => visibleAt(s.level, mode)).map((s) => {
        if (s.custom === 'devices' && inputMode !== 'device_list') return null;
        const fields = s.fields.filter((f) => visibleAt(f.level, mode));
        return (
          <Section
            key={s.id}
            title={s.title}
            description={s.description}
            defaultOpen={s.defaultOpen || s.custom === 'devices'}
          >
            {s.custom === 'presets' ? (
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {(presets.data ?? []).map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => applyPreset(p.id)}
                    className={`rounded-md border px-3 py-2 text-left ${
                      presetId === p.id
                        ? 'border-accent-500 bg-accent-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="text-sm font-medium text-slate-800">{p.name}</div>
                    <div className="text-xs text-slate-500">{p.summary}</div>
                  </button>
                ))}
                {presets.isError && (
                  <p className="text-xs text-red-600">Could not load presets from the API.</p>
                )}
              </div>
            ) : s.custom === 'devices' ? (
              <DeviceTable form={form} calculatedW={deviceWatts} />
            ) : (
              <FieldGrid form={form} fields={fields} onSelectChange={onSelectChange} />
            )}
          </Section>
        );
      })}
    </form>
  );
}
