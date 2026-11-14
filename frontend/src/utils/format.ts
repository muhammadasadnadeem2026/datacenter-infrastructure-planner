/** Display formatting only. No engineering math belongs in this file. */
import type { StepValue } from '../types/api';

export function formatNumber(value: number, unit = ''): string {
  if (!Number.isFinite(value)) return '—';
  const a = Math.abs(value);
  let digits: number;
  if (unit === '%') digits = 1;
  else if (a >= 1000) digits = 0;
  else if (a >= 100) digits = 1;
  else if (a >= 1) digits = 2;
  else if (a === 0) digits = 0;
  else digits = 4;
  return value.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}

const CURRENCY = /^[A-Z]{3}$/;

export function formatValue(value: StepValue, unit = ''): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'string') return value;
  if (CURRENCY.test(unit)) {
    try {
      return value.toLocaleString('en-US', { style: 'currency', currency: unit, maximumFractionDigits: 0 });
    } catch {
      return `${formatNumber(value)} ${unit}`;
    }
  }
  return formatNumber(value, unit);
}

export function formatWithUnit(value: StepValue, unit = ''): string {
  const v = formatValue(value, unit);
  if (!unit || CURRENCY.test(unit) || typeof value !== 'number') return v;
  return unit === '%' ? `${v} %` : `${v} ${unit}`;
}

export function titleCase(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
