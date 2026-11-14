/**
 * Zod mirror of the backend ProjectInputs model (backend/app/schemas/inputs.py).
 * Gives instant field-level feedback; the backend re-validates every request.
 */
import { z } from 'zod';

const num = (label: string) =>
  z
    .number({ invalid_type_error: `${label} must be a number`, required_error: `${label} is required` })
    .finite();

const pos = (label: string) => num(label).gt(0, `${label} must be greater than 0`);
const frac = (label: string) => pos(label).max(1, `${label} must be ≤ 1`);
const pct = (label: string) => pos(label).max(100, `${label} must be ≤ 100 %`);
const optionalNum = (schema: z.ZodNumber) => schema.nullable().optional();

export const redundancy = z.enum(['N', 'N+1', '2N']);
export const phase = z.enum(['single', 'three']);

const minUnits: Record<string, number> = { N: 1, 'N+1': 2, '2N': 2 };
function redundancyCheck(system: string) {
  return (v: { redundancy: string; quantity?: number; unit_count?: number }, ctx: z.RefinementCtx) => {
    const qty = v.quantity ?? v.unit_count ?? 0;
    if (v.unit_count === 0) return;
    const path = [v.quantity !== undefined ? 'quantity' : 'unit_count'];
    if (qty < minUnits[v.redundancy])
      ctx.addIssue({
        code: 'custom',
        path,
        message: `${system}: ${v.redundancy} needs at least ${minUnits[v.redundancy]} units`,
      });
    if (v.redundancy === '2N' && qty % 2)
      ctx.addIssue({ code: 'custom', path, message: `${system}: 2N needs an even number of units` });
  };
}

export const equipmentTypes = [
  'CPU Server',
  'GPU Server',
  'Storage',
  'Network Switch',
  'Router',
  'Firewall',
  'Rack PDU',
  'Other',
] as const;

export const deviceSchema = z.object({
  id: z.string().max(64).nullable().optional(),
  equipment_type: z.enum(equipmentTypes),
  description: z.string().max(200),
  quantity: num('Quantity').int().min(0).max(100_000),
  nameplate_w: num('Nameplate W').min(0).max(500_000),
  utilization_pct: num('Utilization').min(0).max(100),
  rack: z.string().max(64),
});

export const projectInputsSchema = z.object({
  mode: z.enum(['quick', 'standard', 'engineering']),
  unit_system: z.enum(['imperial', 'metric']),
  preset: z.string().max(64),
  it: z
    .object({
      input_mode: z.enum(['rack_average', 'device_list']),
      rack_count: num('Racks').int('Racks must be a whole number').min(1, 'At least 1 rack').max(100_000),
      kw_per_rack: pos('kW per rack').max(2000),
      power_factor: frac('Power factor'),
      utilization_pct: pct('Utilization'),
      devices: z.array(deviceSchema).max(5000),
    })
    .superRefine((v, ctx) => {
      if (v.input_mode !== 'device_list') return;
      const total = v.devices.reduce((s, d) => s + d.quantity * d.nameplate_w * d.utilization_pct, 0);
      if (!v.devices.length || total <= 0)
        ctx.addIssue({
          code: 'custom',
          path: ['devices'],
          message: 'Add at least one device with non-zero power',
        });
    }),
  rack: z.object({ rack_rating_kw: pos('Rack rating').max(2000) }),
  space: z.object({
    room_area: optionalNum(pos('Room area').max(10_000_000)),
    room_area_unit: z.enum(['ft2', 'm2']),
  }),
  electrical: z.object({
    receptacle_id: z.string().max(64),
    voltage: pos('Voltage').max(1000),
    current: pos('Current').max(1000),
    phase,
    continuous_derate: frac('Continuous load factor'),
    circuits_per_rack: num('Circuits').int().min(0).max(64),
  }),
  pdu: z.object({
    voltage: pos('PDU voltage').max(1000),
    amperage: pos('PDU amperage').max(1000),
    phase,
    continuous_derate: frac('Continuous load factor'),
    growth_margin_pct: num('Growth margin').min(0).max(500),
    feed: z.enum(['none', 'ab']),
  }),
  ups: z.object({
    target_load_pct: pct('Target loading'),
    redundancy,
    modules_n: num('Modules').int().min(1).max(64),
    module_kva: num('Module kVA').min(0).max(100_000),
    battery: z
      .object({
        enabled: z.boolean(),
        chemistry: z.enum(['vrla', 'li_ion', 'nicd', 'other']),
        nominal_voltage: pos('Battery voltage').max(2000),
        capacity_kwh: num('Capacity kWh').min(0),
        capacity_ah: num('Capacity Ah').min(0),
        discharge_efficiency: frac('Discharge efficiency'),
        degradation_pct: num('Degradation').min(0).lt(100),
        runtime_target_min: pos('Runtime target').max(1440),
      })
      .superRefine((b, ctx) => {
        if (b.enabled && b.capacity_kwh <= 0 && b.capacity_ah <= 0)
          ctx.addIssue({ code: 'custom', path: ['capacity_kwh'], message: 'Enter capacity in kWh or Ah' });
      }),
  }),
  cooling: z
    .object({
      unit_capacity_kw: num('Unit capacity').min(0),
      unit_count: num('Units').int().min(0).max(1000),
      redundancy,
      liquid_capture_pct: num('Liquid capture').min(0).max(100),
      coolant_flow_lpm_per_kw: num('Coolant flow').min(0).max(10),
    })
    .superRefine(redundancyCheck('Cooling')),
  facility: z
    .object({
      pue: num('PUE').min(1, 'PUE must be ≥ 1').max(5),
      cooling_share_pct: optionalNum(num('Cooling share').min(0).max(100)),
      electrical_loss_share_pct: optionalNum(num('Electrical loss share').min(0).max(100)),
      other_share_pct: optionalNum(num('Other share').min(0).max(100)),
    })
    .superRefine((f, ctx) => {
      const total =
        (f.cooling_share_pct ?? 0) + (f.electrical_loss_share_pct ?? 0) + (f.other_share_pct ?? 0);
      if (total > 100)
        ctx.addIssue({
          code: 'custom',
          path: ['cooling_share_pct'],
          message: 'Overhead shares cannot exceed 100 %',
        });
    }),
  environment: z.object({
    ambient_temp: num('Temperature').min(-60).max(140),
    ambient_temp_unit: z.enum(['C', 'F']),
    altitude: num('Altitude').min(-500).max(30_000),
    altitude_unit: z.enum(['m', 'ft']),
    ashrae_class: z.enum(['A1', 'A2', 'A3', 'A4']),
    humidity_pct: optionalNum(num('Humidity').min(0).max(100)),
    temperature_derate_factor: frac('Temperature factor'),
    altitude_derate_factor: frac('Altitude factor'),
    apply_derating: z.boolean(),
  }),
  utility: z.object({
    service_voltage_v: pos('Service voltage'),
    service_capacity_kva: num('Service capacity').min(0),
  }),
  transformer: z
    .object({
      enabled: z.boolean(),
      primary_voltage_v: pos('Primary voltage'),
      secondary_voltage_v: pos('Secondary voltage'),
      kva_rating: pos('Transformer kVA'),
      efficiency: frac('Efficiency'),
      impedance_pct: pct('Impedance'),
      quantity: num('Quantity').int().min(1).max(500),
      redundancy,
      target_utilization_pct: pct('Target utilization'),
    })
    .superRefine(redundancyCheck('Transformer')),
  generator: z
    .object({
      enabled: z.boolean(),
      unit_kw: pos('Generator kW'),
      unit_kva: pos('Generator kVA'),
      power_factor: frac('Generator PF'),
      quantity: num('Quantity').int().min(1).max(500),
      redundancy,
      step_load_pct: pct('Step load'),
      target_loading_pct: pct('Target loading'),
      load_basis: z.enum(['it_only', 'it_cooling', 'full', 'custom']),
      custom_load_kw: num('Custom load').min(0),
    })
    .superRefine((g, ctx) => {
      redundancyCheck('Generator')(g, ctx);
      if (g.load_basis === 'custom' && g.custom_load_kw <= 0)
        ctx.addIssue({
          code: 'custom',
          path: ['custom_load_kw'],
          message: 'Enter the custom essential load',
        });
    }),
  bess: z.object({
    enabled: z.boolean(),
    power_basis: z.enum(['custom', 'it', 'facility']),
    custom_power_mw: pos('Power MW'),
    duration_min: pos('Duration'),
    dc_bus_voltage: pos('DC bus voltage'),
    pcs_efficiency: frac('PCS efficiency'),
    battery_efficiency: frac('Battery efficiency'),
    depth_of_discharge: frac('Depth of discharge'),
    eol_capacity_factor: frac('EOL factor'),
    redundancy: z.enum(['N', 'N+1']),
    container_power_mw: pos('Container MW'),
    container_energy_mwh: pos('Container MWh'),
  }),
  financial: z.object({
    electricity_rate: num('Electricity rate').min(0).max(100),
    demand_charge: num('Demand charge').min(0),
    currency: z.string().min(1).max(8),
  }),
  advanced: z.object({
    hours_per_year: pos('Hours per year').max(8784),
    facility_power_factor: optionalNum(frac('Facility PF')),
  }),
});

export type ProjectInputs = z.infer<typeof projectInputsSchema>;
export type Device = z.infer<typeof deviceSchema>;
export type Mode = ProjectInputs['mode'];
export type UnitSystem = ProjectInputs['unit_system'];
