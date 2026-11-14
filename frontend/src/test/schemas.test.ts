import { describe, expect, it } from 'vitest';
import { projectInputsSchema, type ProjectInputs } from '../types/schemas';

const base: ProjectInputs = {
  mode: 'standard',
  unit_system: 'imperial',
  preset: 'custom',
  it: {
    input_mode: 'rack_average',
    rack_count: 10,
    kw_per_rack: 6,
    power_factor: 0.95,
    utilization_pct: 100,
    devices: [],
  },
  rack: { rack_rating_kw: 8 },
  space: { room_area: 1000, room_area_unit: 'ft2' },
  electrical: {
    receptacle_id: 'custom',
    voltage: 208,
    current: 30,
    phase: 'single',
    continuous_derate: 0.8,
    circuits_per_rack: 0,
  },
  pdu: {
    voltage: 208,
    amperage: 30,
    phase: 'three',
    continuous_derate: 0.8,
    growth_margin_pct: 20,
    feed: 'ab',
  },
  ups: {
    target_load_pct: 80,
    redundancy: 'N+1',
    modules_n: 2,
    module_kva: 0,
    battery: {
      enabled: false,
      chemistry: 'li_ion',
      nominal_voltage: 480,
      capacity_kwh: 0,
      capacity_ah: 0,
      discharge_efficiency: 0.95,
      degradation_pct: 20,
      runtime_target_min: 5,
    },
  },
  cooling: {
    unit_capacity_kw: 0,
    unit_count: 0,
    redundancy: 'N+1',
    liquid_capture_pct: 0,
    coolant_flow_lpm_per_kw: 0,
  },
  facility: { pue: 1.5, cooling_share_pct: null, electrical_loss_share_pct: null, other_share_pct: null },
  environment: {
    ambient_temp: 24,
    ambient_temp_unit: 'C',
    altitude: 0,
    altitude_unit: 'm',
    ashrae_class: 'A1',
    humidity_pct: null,
    temperature_derate_factor: 1,
    altitude_derate_factor: 1,
    apply_derating: false,
  },
  utility: { service_voltage_v: 13800, service_capacity_kva: 0 },
  transformer: {
    enabled: false,
    primary_voltage_v: 13800,
    secondary_voltage_v: 480,
    kva_rating: 750,
    efficiency: 0.985,
    impedance_pct: 5.75,
    quantity: 2,
    redundancy: 'N+1',
    target_utilization_pct: 80,
  },
  generator: {
    enabled: false,
    unit_kw: 500,
    unit_kva: 625,
    power_factor: 0.8,
    quantity: 2,
    redundancy: 'N+1',
    step_load_pct: 50,
    target_loading_pct: 80,
    load_basis: 'full',
    custom_load_kw: 0,
  },
  bess: {
    enabled: false,
    power_basis: 'facility',
    custom_power_mw: 1,
    duration_min: 5,
    dc_bus_voltage: 800,
    pcs_efficiency: 0.97,
    battery_efficiency: 0.95,
    depth_of_discharge: 0.9,
    eol_capacity_factor: 0.8,
    redundancy: 'N',
    container_power_mw: 1,
    container_energy_mwh: 2,
  },
  financial: { electricity_rate: 0.13, demand_charge: 0, currency: 'USD' },
  advanced: { hours_per_year: 8760, facility_power_factor: null },
};

const withPatch = (fn: (d: ProjectInputs) => void) => {
  const d = structuredClone(base);
  fn(d);
  return projectInputsSchema.safeParse(d).success;
};

type Patch = (d: ProjectInputs) => void;

const invalid: [string, Patch][] = [
  ['zero racks', (d) => (d.it.rack_count = 0)],
  ['kW/rack 0', (d) => (d.it.kw_per_rack = 0)],
  ['PF 0', (d) => (d.it.power_factor = 0)],
  ['PF above 1', (d) => (d.it.power_factor = 1.01)],
  ['PUE below 1', (d) => (d.facility.pue = 0.9)],
  ['negative rate', (d) => (d.financial.electricity_rate = -1)],
  ['NaN', (d) => (d.it.kw_per_rack = NaN)],
  ['Infinity', (d) => (d.it.kw_per_rack = Infinity)],
  ['UPS target 0', (d) => (d.ups.target_load_pct = 0)],
  ['efficiency above 1', (d) => (d.transformer.efficiency = 1.2)],
  ['area 0', (d) => (d.space.room_area = 0)],
  [
    '2N odd units',
    (d) => {
      d.transformer.redundancy = '2N';
      d.transformer.quantity = 3;
    },
  ],
  [
    'shares above 100',
    (d) => {
      d.facility.cooling_share_pct = 70;
      d.facility.other_share_pct = 40;
    },
  ],
  ['empty device list', (d) => (d.it.input_mode = 'device_list')],
];

describe('projectInputsSchema (mirror of backend validation)', () => {
  it('accepts the acceptance-test example', () => {
    expect(projectInputsSchema.safeParse(base).success).toBe(true);
  });
  it.each(invalid)('rejects %s', (_, fn) => {
    expect(withPatch(fn)).toBe(false);
  });
  it('accepts PF = 1 and an omitted optional area', () => {
    expect(
      withPatch((d) => {
        d.it.power_factor = 1;
        d.space.room_area = null;
      }),
    ).toBe(true);
  });
});
