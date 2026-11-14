import { useRef, useState } from 'react';
import { useFieldArray, type UseFormReturn } from 'react-hook-form';
import { equipmentTypes, type Device, type ProjectInputs } from '../../types/schemas';
import { csvToDevices, devicesToCsv } from '../../utils/csv';
import { downloadText, readFileText } from '../../utils/download';
import { formatNumber } from '../../utils/format';
import { getPath } from '../../utils/path';

interface Props {
  form: UseFormReturn<ProjectInputs>;
  /** Calculated watts per row, from the backend result (index aligned). */
  calculatedW: (number | undefined)[];
}

const cell =
  'w-full rounded border border-slate-300 bg-surface px-1.5 py-1 text-xs focus:border-accent-500 focus:outline-none';
const btn = 'btn';

const blank: Device = {
  equipment_type: 'CPU Server',
  description: '',
  quantity: 1,
  nameplate_w: 500,
  utilization_pct: 60,
  rack: '',
};

export function DeviceTable({ form, calculatedW }: Props) {
  const { fields, append, remove, insert, replace } = useFieldArray({
    control: form.control,
    name: 'it.devices',
  });
  const fileRef = useRef<HTMLInputElement>(null);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const num = { setValueAs: (v: unknown) => (v === '' ? NaN : Number(v)) };
  const errors = getPath(form.formState.errors, 'it.devices') as { message?: string } | undefined;

  async function onImport(file: File) {
    const { devices, errors: errs } = csvToDevices(await readFileText(file));
    if (devices.length) replace(devices);
    setImportMsg(
      devices.length
        ? `Imported ${devices.length} rows${errs.length ? `; skipped ${errs.length}: ${errs.slice(0, 3).join('; ')}` : ''}`
        : errs.join('; '),
    );
  }

  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-2">
        <button type="button" className={btn} onClick={() => append({ ...blank })}>
          + Add row
        </button>
        <button type="button" className={btn} onClick={() => fileRef.current?.click()}>
          Import CSV
        </button>
        <button
          type="button"
          className={btn}
          onClick={() =>
            downloadText(devicesToCsv(form.getValues('it.devices')), 'device_list.csv', 'text/csv')
          }
        >
          Export CSV
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void onImport(f);
            e.target.value = '';
          }}
        />
      </div>
      {importMsg && <p className="mb-2 text-xs text-slate-600">{importMsg}</p>}
      {errors?.message && <p className="mb-2 text-xs text-red-600">{errors.message}</p>}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-xs">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="px-1 py-1 font-medium">Type</th>
              <th className="px-1 py-1 font-medium">Description</th>
              <th className="w-16 px-1 py-1 font-medium">Qty</th>
              <th className="w-24 px-1 py-1 font-medium">Nameplate W</th>
              <th className="w-20 px-1 py-1 font-medium">Util. %</th>
              <th className="w-24 px-1 py-1 text-right font-medium">Calc. W</th>
              <th className="w-20 px-1 py-1 font-medium">Rack</th>
              <th className="w-20 px-1 py-1" />
            </tr>
          </thead>
          <tbody>
            {fields.map((field, i) => (
              <tr key={field.id} className="border-t border-slate-100">
                <td className="px-1 py-1">
                  <select className={cell} {...form.register(`it.devices.${i}.equipment_type`)}>
                    {equipmentTypes.map((t) => (
                      <option key={t}>{t}</option>
                    ))}
                  </select>
                </td>
                <td className="px-1 py-1">
                  <input className={cell} {...form.register(`it.devices.${i}.description`)} />
                </td>
                <td className="px-1 py-1">
                  <input
                    type="number"
                    className={`${cell} font-mono`}
                    {...form.register(`it.devices.${i}.quantity`, num)}
                  />
                </td>
                <td className="px-1 py-1">
                  <input
                    type="number"
                    className={`${cell} font-mono`}
                    {...form.register(`it.devices.${i}.nameplate_w`, num)}
                  />
                </td>
                <td className="px-1 py-1">
                  <input
                    type="number"
                    className={`${cell} font-mono`}
                    {...form.register(`it.devices.${i}.utilization_pct`, num)}
                  />
                </td>
                <td className="px-1 py-1 text-right font-mono tabular-nums text-slate-700">
                  {calculatedW[i] !== undefined ? formatNumber(calculatedW[i] as number) : '—'}
                </td>
                <td className="px-1 py-1">
                  <input className={cell} {...form.register(`it.devices.${i}.rack`)} />
                </td>
                <td className="whitespace-nowrap px-1 py-1 text-right">
                  <button
                    type="button"
                    title="Duplicate row"
                    className="px-1 text-slate-500 hover:text-accent-600"
                    onClick={() => insert(i + 1, { ...form.getValues(`it.devices.${i}`) })}
                  >
                    ⧉
                  </button>
                  <button
                    type="button"
                    title="Delete row"
                    className="px-1 text-slate-500 hover:text-red-600"
                    onClick={() => remove(i)}
                  >
                    ✕
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
