import type { Mode } from '../types/schemas';

export interface FieldOption {
  value: string;
  label: string;
}

export type Values = Record<string, unknown>;

export interface FieldDef {
  name: string;
  label: string;
  type: 'number' | 'select' | 'checkbox' | 'text';
  unit?: string;
  step?: number | 'any';
  min?: number;
  max?: number;
  /** strictly greater than */
  gt?: number;
  integer?: boolean;
  /** empty input allowed (sent as null) */
  optional?: boolean;
  placeholder?: string;
  options?: FieldOption[];
  /** options loaded at runtime */
  dynamicOptions?: 'receptacles';
  help?: string;
  /** minimum design mode in which the field is shown */
  level?: Mode;
  showIf?: (values: Values) => boolean;
  disabledIf?: (values: Values) => boolean;
  width?: 'full' | 'half';
}

export const MODE_RANK: Record<Mode, number> = { quick: 0, standard: 1, engineering: 2 };

export const visibleAt = (level: Mode | undefined, mode: Mode) =>
  MODE_RANK[level ?? 'quick'] <= MODE_RANK[mode];

export const REDUNDANCY_OPTIONS: FieldOption[] = [
  { value: 'N', label: 'N' },
  { value: 'N+1', label: 'N+1' },
  { value: '2N', label: '2N' },
];

export const PHASE_OPTIONS: FieldOption[] = [
  { value: 'single', label: 'Single-phase' },
  { value: 'three', label: 'Three-phase' },
];

export const AREA_UNITS: FieldOption[] = [
  { value: 'ft2', label: 'ft²' },
  { value: 'm2', label: 'm²' },
];
