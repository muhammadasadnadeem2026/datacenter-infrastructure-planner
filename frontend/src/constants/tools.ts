/** Standalone tool pages. Each maps a small form to one backend calculation endpoint. */
import { getPath } from '../utils/path';
import { AREA_UNITS, PHASE_OPTIONS, REDUNDANCY_OPTIONS, type FieldDef, type Values } from './fields';
import { batteryFields, bessFields, generatorFields, transformerFields } from './sections';

export interface Highlight {
  module: string;
  key: string;
  metricKey?: string;
}

export interface ToolConfig {
  id: string;
  path: string;
  title: string;
  description: string;
  endpoint: string;
  fields: FieldDef[];
  defaults: Values;
  highlights: Highlight[];
  buildRequest?: (values: Values) => unknown;
  group?: 'power';
}

const always = () => true;

export const TOOLS: ToolConfig[] = [
  {
    id: 'kw-kva',
    path: '/tools/kw-kva',
    group: 'power',
    title: 'kW ↔ kVA Converter',
    description: 'Convert between real power and apparent power for a given power factor.',
    endpoint: 'power-factor',
    fields: [
      {
        name: 'direction',
        label: 'Convert from',
        type: 'select',
        options: [
          { value: 'kw', label: 'kW → kVA' },
          { value: 'kva', label: 'kVA → kW' },
        ],
      },
      { name: 'value', label: 'Value', type: 'number', min: 0, unit: 'kW / kVA' },
      { name: 'power_factor', label: 'Power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
    ],
    defaults: { direction: 'kw', value: 60, power_factor: 0.95 },
    buildRequest: (v) =>
      v.direction === 'kw'
        ? { kw: v.value, power_factor: v.power_factor }
        : { kva: v.value, power_factor: v.power_factor },
    highlights: [
      { module: 'power_factor', key: 'kva' },
      { module: 'power_factor', key: 'kw' },
    ],
  },
  {
    id: 'circuit',
    path: '/tools/circuit',
    group: 'power',
    title: 'Rack Circuit Calculator',
    description: 'Single- and three-phase circuit capacity, continuous-load derating and circuits per rack.',
    endpoint: 'circuit',
    fields: [
      {
        name: 'receptacle_id',
        label: 'Receptacle / circuit',
        type: 'select',
        dynamicOptions: 'receptacles',
        width: 'full',
      },
      {
        name: 'voltage',
        label: 'Voltage',
        type: 'number',
        gt: 0,
        unit: 'V',
        disabledIf: (v) => v.receptacle_id !== 'custom',
      },
      {
        name: 'current',
        label: 'Circuit rating',
        type: 'number',
        gt: 0,
        unit: 'A',
        disabledIf: (v) => v.receptacle_id !== 'custom',
      },
      {
        name: 'phase',
        label: 'Phase',
        type: 'select',
        options: PHASE_OPTIONS,
        disabledIf: (v) => v.receptacle_id !== 'custom',
      },
      {
        name: 'continuous_derate',
        label: 'Continuous load factor',
        type: 'number',
        gt: 0,
        max: 1,
        step: 0.01,
        disabledIf: (v) => v.receptacle_id !== 'custom',
      },
      { name: 'rack_kw', label: 'Rack load', type: 'number', gt: 0, unit: 'kW' },
      { name: 'power_factor', label: 'Power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
      {
        name: 'circuits_per_rack',
        label: 'Existing circuits (0 = size)',
        type: 'number',
        integer: true,
        min: 0,
      },
    ],
    defaults: {
      receptacle_id: 'custom',
      voltage: 208,
      current: 30,
      phase: 'single',
      continuous_derate: 0.8,
      rack_kw: 11,
      power_factor: 0.95,
      circuits_per_rack: 0,
    },
    highlights: [
      { module: 'circuit', key: 'nominal_kva' },
      { module: 'circuit', key: 'usable_kva' },
      { module: 'circuit', key: 'rack_kva' },
      { module: 'circuit', key: 'min_circuits' },
      { module: 'circuit', key: 'loading_pct' },
      { module: 'circuit', key: 'headroom_kva' },
    ],
  },
  {
    id: 'rack-count',
    path: '/tools/rack-count',
    group: 'power',
    title: 'Rack Count Calculator',
    description: 'How many racks of a given rating are needed for a target IT load.',
    endpoint: 'rack-count',
    fields: [
      { name: 'it_kw', label: 'Target IT load', type: 'number', gt: 0, unit: 'kW' },
      { name: 'rack_power_kw', label: 'Rack rating', type: 'number', gt: 0, unit: 'kW' },
      {
        name: 'racks_planned',
        label: 'Racks planned',
        type: 'number',
        integer: true,
        min: 1,
        optional: true,
        placeholder: 'optional',
      },
    ],
    defaults: { it_kw: 8400, rack_power_kw: 142, racks_planned: null },
    highlights: [
      { module: 'rack_count', key: 'racks_required' },
      { module: 'rack_count', key: 'installed_rack_kw' },
      { module: 'rack_count', key: 'unused_kw' },
    ],
  },
  {
    id: 'cooling',
    path: '/tools/cooling',
    title: 'Cooling Load',
    description: 'Heat rejection from IT load: thermal kW, BTU/hr, refrigeration tons and density class.',
    endpoint: 'cooling',
    fields: [
      { name: 'it_kw', label: 'IT load', type: 'number', gt: 0, unit: 'kW' },
      { name: 'rack_count', label: 'Racks', type: 'number', integer: true, min: 1 },
      {
        name: 'liquid_capture_pct',
        label: 'Liquid heat capture (DLC)',
        type: 'number',
        min: 0,
        max: 100,
        unit: '% liquid',
      },
      {
        name: 'coolant_flow_lpm_per_kw',
        label: 'Coolant specific flow (0 = n/a)',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'L/min per kW',
        showIf: (v) => Number(v.liquid_capture_pct) > 0,
      },
    ],
    defaults: { it_kw: 60, rack_count: 10, liquid_capture_pct: 0, coolant_flow_lpm_per_kw: 0 },
    highlights: [
      { module: 'cooling', key: 'thermal_kw' },
      { module: 'cooling', key: 'btu_hr' },
      { module: 'cooling', key: 'tons' },
      { module: 'cooling', key: 'btu_hr_per_rack' },
      { module: 'cooling', key: 'classification' },
      { module: 'cooling', key: 'air_heat_kw' },
      { module: 'cooling', key: 'coolant_flow_lpm' },
    ],
  },
  {
    id: 'ups-sizing',
    path: '/tools/ups-sizing',
    title: 'UPS Sizing',
    description: 'UPS capacity with N, N+1 or 2N redundancy, module sizing and optional battery runtime.',
    endpoint: 'ups',
    fields: [
      { name: 'load_kw', label: 'IT load', type: 'number', gt: 0, unit: 'kW' },
      { name: 'power_factor', label: 'Power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
      {
        name: 'ups.target_load_pct',
        label: 'Target UPS loading',
        type: 'number',
        gt: 0,
        max: 100,
        unit: '%',
      },
      { name: 'ups.redundancy', label: 'Redundancy', type: 'select', options: REDUNDANCY_OPTIONS },
      { name: 'ups.modules_n', label: 'Modules carrying load (n)', type: 'number', integer: true, min: 1 },
      { name: 'ups.module_kva', label: 'Module rating (0 = auto)', type: 'number', min: 0, unit: 'kVA' },
      { name: 'ups.battery.enabled', label: 'Estimate battery runtime', type: 'checkbox', width: 'full' },
      ...batteryFields(),
    ],
    defaults: {
      load_kw: 220,
      power_factor: 0.95,
      ups: {
        target_load_pct: 80,
        redundancy: 'N+1',
        modules_n: 2,
        module_kva: 0,
        battery: {
          enabled: false,
          chemistry: 'li_ion',
          nominal_voltage: 480,
          capacity_kwh: 40,
          capacity_ah: 0,
          discharge_efficiency: 0.95,
          degradation_pct: 20,
          runtime_target_min: 5,
        },
      },
    },
    highlights: [
      { module: 'ups', key: 'load_kva' },
      { module: 'ups', key: 'required_kva' },
      { module: 'ups', key: 'installed_kva' },
      { module: 'ups', key: 'module_count' },
      { module: 'ups', key: 'module_kva' },
      { module: 'ups', key: 'utilization_usable_pct' },
    ],
  },
  {
    id: 'pdu',
    path: '/tools/pdu',
    title: 'Rack PDU',
    description: 'PDU count, loading and line current with growth margin and A/B feeds.',
    endpoint: 'pdu',
    fields: [
      { name: 'rack_kw', label: 'Rack IT load', type: 'number', gt: 0, unit: 'kW' },
      { name: 'power_factor', label: 'Power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
      { name: 'pdu.growth_margin_pct', label: 'Growth margin', type: 'number', min: 0, unit: '%' },
      { name: 'pdu.voltage', label: 'PDU voltage', type: 'number', gt: 0, unit: 'V' },
      { name: 'pdu.amperage', label: 'PDU rating', type: 'number', gt: 0, unit: 'A' },
      { name: 'pdu.phase', label: 'Phase', type: 'select', options: PHASE_OPTIONS },
      {
        name: 'pdu.continuous_derate',
        label: 'Continuous load factor',
        type: 'number',
        gt: 0,
        max: 1,
        step: 0.01,
      },
      {
        name: 'pdu.feed',
        label: 'Feeds',
        type: 'select',
        options: [
          { value: 'none', label: 'Single feed' },
          { value: 'ab', label: 'A/B redundant' },
        ],
      },
    ],
    defaults: {
      rack_kw: 11,
      power_factor: 0.95,
      pdu: {
        growth_margin_pct: 20,
        voltage: 208,
        amperage: 30,
        phase: 'three',
        continuous_derate: 0.8,
        feed: 'ab',
      },
    },
    highlights: [
      { module: 'pdu', key: 'design_kw' },
      { module: 'pdu', key: 'pdus_total' },
      { module: 'pdu', key: 'loading_pct' },
      { module: 'pdu', key: 'line_current_a' },
    ],
  },
  {
    id: 'rack-density',
    path: '/tools/rack-density',
    title: 'Rack Density',
    description: 'Total IT load, area power density, circuits per rack and cooling / thermal class.',
    endpoint: 'rack-density',
    fields: [
      { name: 'rack_count', label: 'Racks', type: 'number', integer: true, min: 1 },
      { name: 'kw_per_rack', label: 'Load per rack', type: 'number', gt: 0, unit: 'kW' },
      {
        name: 'room_area',
        label: 'Room area',
        type: 'number',
        gt: 0,
        optional: true,
        placeholder: 'optional',
      },
      { name: 'room_area_unit', label: 'Unit', type: 'select', options: AREA_UNITS },
      { name: 'voltage', label: 'Circuit voltage', type: 'number', gt: 0, unit: 'V' },
      { name: 'current', label: 'Circuit rating', type: 'number', gt: 0, unit: 'A' },
      { name: 'phase', label: 'Phase', type: 'select', options: PHASE_OPTIONS },
      {
        name: 'continuous_derate',
        label: 'Continuous load factor',
        type: 'number',
        gt: 0,
        max: 1,
        step: 0.01,
      },
      { name: 'power_factor', label: 'Power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
    ],
    defaults: {
      rack_count: 20,
      kw_per_rack: 11,
      room_area: 2000,
      room_area_unit: 'ft2',
      voltage: 208,
      current: 30,
      phase: 'three',
      continuous_derate: 0.8,
      power_factor: 0.95,
    },
    highlights: [
      { module: 'rack_density', key: 'it_kw' },
      { module: 'space', key: 'w_per_ft2', metricKey: 'w_per_m2' },
      { module: 'circuit', key: 'min_circuits' },
      { module: 'rack_density', key: 'cooling_class' },
      { module: 'rack_density', key: 'thermal_class' },
    ],
  },
  {
    id: 'transformer',
    path: '/tools/transformer',
    title: 'Transformer',
    description:
      'Transformer loading with redundancy, full-load current and approximate terminal fault current.',
    endpoint: 'transformer',
    fields: [
      { name: 'required_kw', label: 'Load served', type: 'number', gt: 0, unit: 'kW' },
      { name: 'power_factor', label: 'Load power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
      ...transformerFields('transformer', always),
    ],
    defaults: {
      required_kw: 1900,
      power_factor: 0.95,
      transformer: {
        enabled: true,
        primary_voltage_v: 13800,
        secondary_voltage_v: 480,
        kva_rating: 2500,
        efficiency: 0.985,
        impedance_pct: 5.75,
        quantity: 2,
        redundancy: 'N+1',
        target_utilization_pct: 80,
      },
    },
    highlights: [
      { module: 'transformer', key: 'required_kva' },
      { module: 'transformer', key: 'loading_pct' },
      { module: 'transformer', key: 'secondary_fla_a' },
      { module: 'transformer', key: 'fault_current_ka' },
    ],
  },
  {
    id: 'generator',
    path: '/tools/generator',
    title: 'Generator',
    description: 'Standby generator quantity, utilization and reserve with redundancy and site derating.',
    endpoint: 'generator',
    fields: [
      { name: 'load_kw', label: 'Generator-backed load', type: 'number', gt: 0, unit: 'kW' },
      { name: 'derate_factor', label: 'Site derate factor', type: 'number', gt: 0, max: 1, step: 0.01 },
      ...generatorFields('generator', always).filter(
        (f) => !f.name.endsWith('load_basis') && !f.name.endsWith('custom_load_kw'),
      ),
    ],
    defaults: {
      load_kw: 3000,
      derate_factor: 1,
      generator: {
        enabled: true,
        unit_kw: 2000,
        unit_kva: 2500,
        power_factor: 0.8,
        quantity: 3,
        redundancy: 'N+1',
        step_load_pct: 50,
        target_loading_pct: 80,
        load_basis: 'custom',
        custom_load_kw: 3000,
      },
    },
    buildRequest: (v) => ({
      ...v,
      generator: { ...(v.generator as Values), load_basis: 'custom', custom_load_kw: v.load_kw },
    }),
    highlights: [
      { module: 'generator', key: 'required_capacity_kw' },
      { module: 'generator', key: 'units_recommended' },
      { module: 'generator', key: 'usable_kw' },
      { module: 'generator', key: 'loading_pct' },
      { module: 'generator', key: 'reserve_kw' },
    ],
  },
  {
    id: 'bess',
    path: '/tools/bess',
    title: 'Battery Energy Storage',
    description:
      'BESS power and energy sizing, container count and DC current — AC and DC sides kept separate.',
    endpoint: 'bess',
    fields: [
      { name: 'power_mw', label: 'Required AC power', type: 'number', gt: 0, unit: 'MW' },
      ...bessFields('bess', always, false),
    ],
    defaults: {
      power_mw: 10,
      bess: {
        enabled: true,
        power_basis: 'custom',
        custom_power_mw: 10,
        duration_min: 15,
        dc_bus_voltage: 1000,
        pcs_efficiency: 0.97,
        battery_efficiency: 0.95,
        depth_of_discharge: 0.9,
        eol_capacity_factor: 0.8,
        redundancy: 'N',
        container_power_mw: 2.5,
        container_energy_mwh: 5,
      },
    },
    highlights: [
      { module: 'bess', key: 'battery_mwh' },
      { module: 'bess', key: 'containers_power' },
      { module: 'bess', key: 'containers_energy' },
      { module: 'bess', key: 'containers_total' },
      { module: 'bess', key: 'dc_current_a' },
    ],
  },
];

export const toolById = (id: string) => TOOLS.find((t) => t.id === id)!;

export function isVisible(f: FieldDef, values: Values): boolean {
  return f.showIf ? f.showIf(values) : true;
}

export { getPath };
