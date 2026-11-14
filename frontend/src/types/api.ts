/** Shapes returned by the HallPlan API. The frontend never computes these values. */

export type StepValue = number | string | boolean | null;

export interface Step {
  key: string;
  label: string;
  value: StepValue;
  unit: string;
  formula: string;
  substitution: string;
  assumption: string;
  reference: string;
}

export interface ModuleOut {
  module: string;
  steps: Step[];
  data: Record<string, unknown>;
}

export type Severity = 'info' | 'caution' | 'critical';

export interface EngineeringWarning {
  severity: Severity;
  code: string;
  title: string;
  message: string;
  affected_system: string;
  reference: string;
}

export interface ToolResponse {
  engine_version: string;
  modules: Record<string, ModuleOut>;
  warnings: EngineeringWarning[];
}

export type CapacityStatus = 'ok' | 'caution' | 'critical' | 'not_configured';

export interface CapacityRow {
  system: string;
  label: string;
  required: number | null;
  installed: number | null;
  usable: number | null;
  unit: string;
  redundancy: string;
  loading_pct: number | null;
  reserve: number | null;
  max_it_kw: number | null;
  usable_kw_equivalent: number | null;
  status: CapacityStatus;
  note: string;
}

export interface Bottleneck {
  system: string;
  label: string;
  loading_pct: number;
  max_it_kw: number;
  status: CapacityStatus;
  message: string;
}

export interface FlowMetric {
  label: string;
  value: number | null;
  unit: string;
}

export interface FlowNode {
  id: string;
  label: string;
  visible: boolean;
  metrics: FlowMetric[];
  feeds?: string;
}

export interface SummaryCard {
  id: string;
  label: string;
  imperial: { module: string; key: string };
  metric: { module: string; key: string };
}

export interface FullResponse extends ToolResponse {
  calculated_at: string;
  mode: string;
  unit_system: 'imperial' | 'metric';
  capacity: { rows: CapacityRow[]; bottleneck: Bottleneck | null };
  power_flow: { nodes: FlowNode[]; sources: FlowNode[] };
  sankey: {
    nodes: { name: string }[];
    links: { source: number; target: number; value: number }[];
    split_given: boolean;
  };
  summary: SummaryCard[];
}

export interface Receptacle {
  id: string;
  name: string;
  voltage: number;
  amps: number;
  phase: 'single' | 'three';
  continuous_derate: number;
  description: string;
  nominal_kva: number;
  usable_kva: number;
}

export interface PresetMeta {
  id: string;
  name: string;
  summary: string;
  inputs: import('./schemas').ProjectInputs;
}

export interface Reference {
  id: string;
  organization: string;
  document: string;
  edition: string;
  section: string;
  description: string;
  url: string;
  date_verified: string | null;
  verification_status: string;
}

export interface Meta {
  app: string;
  engine_version: string;
  disclaimer: string;
  redundancy_options: string[];
}

export interface ProjectSummary {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  calculator_version: string;
}

export interface ProjectRecord extends ProjectSummary {
  inputs: import('./schemas').ProjectInputs;
  results: FullResponse;
  warnings: EngineeringWarning[];
}
