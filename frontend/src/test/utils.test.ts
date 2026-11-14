import { describe, expect, it } from 'vitest';
import type { FieldDef } from '../constants/fields';
import { csvToDevices, devicesToCsv, parseCsvLine } from '../utils/csv';
import { formatValue, formatWithUnit } from '../utils/format';
import { getPath, setPath } from '../utils/path';
import { buildSchema } from '../utils/schemaBuilder';

describe('format', () => {
  it('formats engine values for display without changing them', () => {
    expect(formatValue(63.1578947, 'kVA')).toBe('63.16');
    expect(formatValue(204728.52, 'BTU/hr')).toBe('204,729');
    expect(formatValue(102492, 'USD')).toBe('$102,492');
    expect(formatWithUnit(80, '%')).toBe('80 %');
    expect(formatValue(true)).toBe('Yes');
    expect(formatValue(null)).toBe('—');
  });
});

describe('path helpers', () => {
  it('reads and writes nested values immutably', () => {
    const o = { a: { b: 1 } };
    expect(getPath(o, 'a.b')).toBe(1);
    const n = setPath(o, 'a.c.d', 2);
    expect(getPath(n, 'a.c.d')).toBe(2);
    expect(o).toEqual({ a: { b: 1 } });
  });
});

describe('device CSV', () => {
  const devices = [
    {
      equipment_type: 'GPU Server' as const,
      description: 'HGX, "8-GPU"',
      quantity: 4,
      nameplate_w: 10200,
      utilization_pct: 80,
      rack: 'A1',
    },
  ];
  it('round-trips including quotes and commas', () => {
    const { devices: back, errors } = csvToDevices(devicesToCsv(devices));
    expect(errors).toEqual([]);
    expect(back).toEqual(devices);
  });
  it('parses quoted cells', () => {
    expect(parseCsvLine('a,"b, c","d ""e"""')).toEqual(['a', 'b, c', 'd "e"']);
  });
  it('rejects invalid rows', () => {
    const r = csvToDevices(
      'equipment_type,quantity,nameplate_w,utilization_pct\nToaster,1,1,1\nStorage,-1,1,1\nStorage,1,1,150',
    );
    expect(r.devices).toHaveLength(0);
    expect(r.errors).toHaveLength(3);
  });
  it('reports missing columns', () => {
    expect(csvToDevices('foo,bar\n1,2').errors[0]).toMatch(/Missing columns/);
  });
});

describe('schema builder', () => {
  const fields: FieldDef[] = [
    { name: 'it_kw', label: 'IT load', type: 'number', gt: 0 },
    { name: 'ups.modules_n', label: 'Modules', type: 'number', integer: true, min: 1 },
    { name: 'ups.redundancy', label: 'Redundancy', type: 'select' },
    { name: 'area', label: 'Area', type: 'number', optional: true, gt: 0 },
  ];
  const schema = buildSchema(fields);
  it('accepts valid nested values', () => {
    expect(
      schema.safeParse({ it_kw: 60, ups: { modules_n: 2, redundancy: 'N+1' }, area: null }).success,
    ).toBe(true);
  });
  it.each([
    [{ it_kw: 0, ups: { modules_n: 2, redundancy: 'N' } }],
    [{ it_kw: NaN, ups: { modules_n: 2, redundancy: 'N' } }],
    [{ it_kw: Infinity, ups: { modules_n: 2, redundancy: 'N' } }],
    [{ it_kw: 5, ups: { modules_n: 1.5, redundancy: 'N' } }],
    [{ it_kw: 5, ups: { modules_n: 1, redundancy: '' } }],
  ])('rejects %j', (v) => {
    expect(schema.safeParse(v).success).toBe(false);
  });
});
