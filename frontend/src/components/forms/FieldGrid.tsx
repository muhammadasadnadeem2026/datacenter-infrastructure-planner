import type { FieldValues, UseFormReturn } from 'react-hook-form';
import { useWatch } from 'react-hook-form';
import type { FieldDef, FieldOption, Values } from '../../constants/fields';
import { useReceptacles } from '../../hooks/useConstants';
import { getPath } from '../../utils/path';

interface Props<T extends FieldValues> {
  form: UseFormReturn<T>;
  fields: FieldDef[];
  /** Called after a select changes (e.g. receptacle -> fill voltage / current). */
  onSelectChange?: (name: string, value: string) => void;
}

const inputCls =
  'w-full rounded-md border border-slate-300 bg-surface px-2.5 py-1.5 text-sm text-slate-900 shadow-sm ' +
  'focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-100 disabled:bg-slate-100 ' +
  'disabled:text-slate-500 aria-[invalid=true]:border-red-500';

function useOptions(f: FieldDef): FieldOption[] {
  const rec = useReceptacles();
  if (f.dynamicOptions === 'receptacles') {
    const lib = (rec.data ?? []).map((r) => ({
      value: r.id,
      label: `${r.name} — ${r.voltage} V ${r.amps} A ${r.phase === 'three' ? '3φ' : '1φ'}`,
    }));
    return [{ value: 'custom', label: 'Custom (enter values)' }, ...lib];
  }
  return f.options ?? [];
}

function Field<T extends FieldValues>({
  form,
  f,
  values,
  onSelectChange,
}: {
  form: UseFormReturn<T>;
  f: FieldDef;
  values: Values;
  onSelectChange?: Props<T>['onSelectChange'];
}) {
  const options = useOptions(f);
  const error = getPath(form.formState.errors, f.name) as { message?: string } | undefined;
  const disabled = f.disabledIf?.(values) ?? false;
  const id = `f-${f.name.replace(/\./g, '-')}`;
  const name = f.name as never;
  const span = f.width === 'full' ? 'sm:col-span-2' : '';

  if (f.type === 'checkbox') {
    return (
      <label className={`flex items-center gap-2 text-sm text-slate-700 ${span}`}>
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-slate-300 text-accent-600"
          {...form.register(name)}
        />
        {f.label}
      </label>
    );
  }

  let control;
  if (f.type === 'select') {
    const reg = form.register(name, {
      onChange: (e: React.ChangeEvent<HTMLSelectElement>) => onSelectChange?.(f.name, e.target.value),
    });
    control = (
      <select id={id} className={inputCls} disabled={disabled} aria-invalid={!!error} {...reg}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    );
  } else if (f.type === 'text') {
    control = (
      <input
        id={id}
        type="text"
        className={inputCls}
        disabled={disabled}
        aria-invalid={!!error}
        {...form.register(name)}
      />
    );
  } else {
    control = (
      <input
        id={id}
        type="number"
        inputMode="decimal"
        step={f.step ?? 'any'}
        placeholder={f.placeholder}
        className={`${inputCls} font-mono tabular-nums`}
        disabled={disabled}
        aria-invalid={!!error}
        {...form.register(name, {
          setValueAs: (v: unknown) =>
            v === '' || v === null || v === undefined ? (f.optional ? null : NaN) : Number(v),
        })}
      />
    );
  }

  return (
    <div className={span}>
      <label
        htmlFor={id}
        className="mb-1 flex items-baseline justify-between gap-2 text-xs font-medium text-slate-600"
      >
        <span>{f.label}</span>
        {f.unit && <span className="font-normal text-slate-400">{f.unit}</span>}
      </label>
      {control}
      {error?.message ? (
        <p className="mt-1 text-xs text-red-600">{error.message}</p>
      ) : f.help ? (
        <p className="mt-1 text-xs text-slate-500">{f.help}</p>
      ) : null}
    </div>
  );
}

export function FieldGrid<T extends FieldValues>({ form, fields, onSelectChange }: Props<T>) {
  const values = (useWatch({ control: form.control }) ?? {}) as Values;
  const shown = fields.filter((f) => (f.showIf ? f.showIf(values) : true));
  if (!shown.length) return null;
  return (
    <div className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
      {shown.map((f) => (
        <Field key={f.name} form={form} f={f} values={values} onSelectChange={onSelectChange} />
      ))}
    </div>
  );
}
