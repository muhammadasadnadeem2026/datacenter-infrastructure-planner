export const MODULE_TITLES: Record<string, string> = {
  it: 'IT Load',
  rack_count: 'Rack Capacity',
  space: 'Space / White Space',
  circuit: 'Branch Circuits',
  pdu: 'Rack PDU',
  ups: 'UPS',
  battery: 'UPS Battery',
  facility: 'Facility / PUE',
  environment: 'Environment',
  cooling: 'Cooling',
  utility: 'Utility',
  transformer: 'Transformer',
  generator: 'Generator',
  bess: 'BESS',
  energy: 'Energy & Cost',
  rack_density: 'Rack Density',
  power_factor: 'Power Factor',
  convert: 'Conversion',
};

export const MODULE_ORDER = [
  'it',
  'rack_count',
  'space',
  'circuit',
  'pdu',
  'ups',
  'battery',
  'facility',
  'cooling',
  'environment',
  'utility',
  'transformer',
  'generator',
  'bess',
  'energy',
];

/** Chart palette, fixed order: Accent, Chart Rust, Chart Teal, Periwinkle, Chart Navy. */
export const SERIES_COLORS = ['#F2A93B', '#C4551A', '#0E6E73', '#F6C66E', '#3A3A55'];

export const STATUS_STYLES: Record<string, { label: string; cls: string; icon: string }> = {
  ok: { label: 'OK', cls: 'bg-emerald-50 text-emerald-800 ring-emerald-600/20', icon: '✓' },
  caution: { label: 'Caution', cls: 'bg-amber-50 text-amber-800 ring-amber-600/30', icon: '!' },
  critical: { label: 'Critical', cls: 'bg-red-50 text-red-800 ring-red-600/30', icon: '✕' },
  info: { label: 'Info', cls: 'bg-sky-50 text-sky-800 ring-sky-600/20', icon: 'i' },
  not_configured: { label: 'Not configured', cls: 'bg-slate-50 text-slate-500 ring-slate-400/20', icon: '–' },
};
