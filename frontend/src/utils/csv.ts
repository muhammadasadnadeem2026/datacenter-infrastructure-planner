/** Device-list CSV import / export. Serializes inputs only; calculated watts come from the API. */
import { equipmentTypes, type Device } from '../types/schemas';

export const DEVICE_CSV_HEADER = [
  'equipment_type',
  'description',
  'quantity',
  'nameplate_w',
  'utilization_pct',
  'rack',
];

function escape(v: string | number): string {
  const s = String(v);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function devicesToCsv(devices: Device[]): string {
  const rows = devices.map((d) =>
    [d.equipment_type, d.description, d.quantity, d.nameplate_w, d.utilization_pct, d.rack]
      .map(escape)
      .join(','),
  );
  return [DEVICE_CSV_HEADER.join(','), ...rows].join('\n');
}

export function parseCsvLine(line: string): string[] {
  const out: string[] = [];
  let cur = '';
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (quoted) {
      if (c === '"' && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else if (c === '"') quoted = false;
      else cur += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') {
      out.push(cur);
      cur = '';
    } else cur += c;
  }
  out.push(cur);
  return out.map((s) => s.trim());
}

export interface CsvImportResult {
  devices: Device[];
  errors: string[];
}

export function csvToDevices(text: string): CsvImportResult {
  const lines = text.split(/\r?\n/).filter((l) => l.trim());
  const errors: string[] = [];
  if (!lines.length) return { devices: [], errors: ['File is empty'] };
  const header = parseCsvLine(lines[0]).map((h) => h.toLowerCase());
  const idx = Object.fromEntries(DEVICE_CSV_HEADER.map((h) => [h, header.indexOf(h)]));
  const missing = DEVICE_CSV_HEADER.filter((h) => idx[h] < 0 && h !== 'description' && h !== 'rack');
  if (missing.length) return { devices: [], errors: [`Missing columns: ${missing.join(', ')}`] };

  const devices: Device[] = [];
  lines.slice(1).forEach((line, n) => {
    const cells = parseCsvLine(line);
    const get = (k: string) => (idx[k] >= 0 ? (cells[idx[k]] ?? '') : '');
    const type = get('equipment_type') as Device['equipment_type'];
    const quantity = Number(get('quantity'));
    const nameplate_w = Number(get('nameplate_w'));
    const utilization_pct = Number(get('utilization_pct'));
    const row = n + 2;
    if (!equipmentTypes.includes(type)) return errors.push(`Row ${row}: unknown equipment type "${type}"`);
    if (!Number.isInteger(quantity) || quantity < 0) return errors.push(`Row ${row}: invalid quantity`);
    if (!Number.isFinite(nameplate_w) || nameplate_w < 0)
      return errors.push(`Row ${row}: invalid nameplate W`);
    if (!Number.isFinite(utilization_pct) || utilization_pct < 0 || utilization_pct > 100)
      return errors.push(`Row ${row}: utilization must be 0–100`);
    devices.push({
      equipment_type: type,
      description: get('description'),
      quantity,
      nameplate_w,
      utilization_pct,
      rack: get('rack'),
    });
  });
  return { devices, errors };
}
