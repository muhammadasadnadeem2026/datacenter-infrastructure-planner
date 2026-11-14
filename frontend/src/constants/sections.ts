/** Main-calculator input sections. Labels and layout only; validation lives in types/schemas.ts. */
import type { Mode } from '../types/schemas';
import { getPath } from '../utils/path';
import { AREA_UNITS, PHASE_OPTIONS, REDUNDANCY_OPTIONS, type FieldDef, type Values } from './fields';

export interface SectionDef {
  id: string;
  title: string;
  level: Mode;
  description?: string;
  custom?: 'presets' | 'devices';
  fields: FieldDef[];
  defaultOpen?: boolean;
}

const is = (path: string, value: unknown) => (v: Values) => getPath(v, path) === value;
const libraryReceptacle = (v: Values) => getPath(v, 'electrical.receptacle_id') !== 'custom';

export const SECTIONS: SectionDef[] = [
  {
    id: 'presets',
    title: 'Deployment Presets',
    level: 'quick',
    custom: 'presets',
    fields: [],
    defaultOpen: true,
  },
  {
    id: 'it',
    title: 'IT Load',
    level: 'quick',
    defaultOpen: true,
    fields: [
      {
        name: 'it.input_mode',
        label: 'Input mode',
        type: 'select',
        level: 'standard',
        options: [
          { value: 'rack_average', label: 'Rack average' },
          { value: 'device_list', label: 'Device list' },
        ],
      },
      {
        name: 'it.rack_count',
        label: 'Number of racks',
        type: 'number',
        integer: true,
        min: 1,
        unit: 'racks',
      },
      {
        name: 'it.kw_per_rack',
        label: 'Average load per rack',
        type: 'number',
        gt: 0,
        unit: 'kW',
        showIf: (v) => getPath(v, 'it.input_mode') !== 'device_list',
      },
      { name: 'it.power_factor', label: 'Power factor', type: 'number', gt: 0, max: 1, step: 0.01 },
      {
        name: 'it.utilization_pct',
        label: 'Average utilization (energy)',
        type: 'number',
        gt: 0,
        max: 100,
        unit: '%',
        level: 'standard',
        help: 'Applied to annual energy only. Sizing always uses design load.',
      },
    ],
  },
  {
    id: 'devices',
    title: 'Device List',
    level: 'standard',
    custom: 'devices',
    fields: [],
  },
  {
    id: 'rack',
    title: 'Rack Configuration',
    level: 'standard',
    fields: [
      {
        name: 'rack.rack_rating_kw',
        label: 'Provisioned power per rack',
        type: 'number',
        gt: 0,
        unit: 'kW',
        help: 'Rack power capacity used for the IT row of the capacity balance and rack-count check.',
      },
    ],
  },
  {
    id: 'electrical',
    title: 'Electrical',
    level: 'standard',
    description: 'Rack branch circuit. Library receptacles fix voltage, current and phase.',
    fields: [
      {
        name: 'electrical.receptacle_id',
        label: 'Receptacle / circuit',
        type: 'select',
        dynamicOptions: 'receptacles',
        width: 'full',
      },
      {
        name: 'electrical.voltage',
        label: 'Voltage',
        type: 'number',
        gt: 0,
        unit: 'V',
        disabledIf: libraryReceptacle,
      },
      {
        name: 'electrical.current',
        label: 'Breaker / circuit rating',
        type: 'number',
        gt: 0,
        unit: 'A',
        disabledIf: libraryReceptacle,
      },
      {
        name: 'electrical.phase',
        label: 'Phase',
        type: 'select',
        options: PHASE_OPTIONS,
        disabledIf: libraryReceptacle,
      },
      {
        name: 'electrical.continuous_derate',
        label: 'Continuous load factor',
        type: 'number',
        gt: 0,
        max: 1,
        step: 0.01,
        disabledIf: libraryReceptacle,
      },
      {
        name: 'electrical.circuits_per_rack',
        label: 'Existing circuits per rack',
        type: 'number',
        integer: true,
        min: 0,
        help: '0 = evaluate at the minimum required circuit count.',
      },
    ],
  },
  {
    id: 'pdu',
    title: 'PDU / Branch Circuits',
    level: 'standard',
    fields: [
      { name: 'pdu.voltage', label: 'PDU voltage', type: 'number', gt: 0, unit: 'V' },
      { name: 'pdu.amperage', label: 'PDU input rating', type: 'number', gt: 0, unit: 'A' },
      { name: 'pdu.phase', label: 'Phase', type: 'select', options: PHASE_OPTIONS },
      {
        name: 'pdu.continuous_derate',
        label: 'Continuous load factor',
        type: 'number',
        gt: 0,
        max: 1,
        step: 0.01,
      },
      { name: 'pdu.growth_margin_pct', label: 'Growth margin', type: 'number', min: 0, unit: '%' },
      {
        name: 'pdu.feed',
        label: 'Rack feeds',
        type: 'select',
        options: [
          { value: 'none', label: 'Single feed' },
          { value: 'ab', label: 'A/B redundant' },
        ],
      },
    ],
  },
  {
    id: 'ups',
    title: 'UPS',
    level: 'standard',
    fields: [
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
      {
        name: 'ups.module_kva',
        label: 'Module rating (0 = auto)',
        type: 'number',
        min: 0,
        unit: 'kVA',
        help: 'Enter a catalogue module size to check a specific configuration.',
      },
      { name: 'ups.battery.enabled', label: 'Estimate battery runtime', type: 'checkbox', width: 'full' },
      ...batteryFields(),
    ],
  },
  {
    id: 'cooling',
    title: 'Cooling',
    level: 'standard',
    description: 'Leave unit capacity at 0 if the cooling plant is not yet defined.',
    fields: [
      {
        name: 'cooling.unit_capacity_kw',
        label: 'Cooling unit capacity',
        type: 'number',
        min: 0,
        unit: 'kW th',
      },
      { name: 'cooling.unit_count', label: 'Units installed', type: 'number', integer: true, min: 0 },
      { name: 'cooling.redundancy', label: 'Redundancy', type: 'select', options: REDUNDANCY_OPTIONS },
      {
        name: 'cooling.liquid_capture_pct',
        label: 'Liquid heat capture (DLC)',
        type: 'number',
        min: 0,
        max: 100,
        unit: '% liquid',
        help: 'Vendor liquid:air ratio, e.g. 85 for 85:15. 0 = air cooled.',
      },
      {
        name: 'cooling.coolant_flow_lpm_per_kw',
        label: 'Coolant specific flow (0 = n/a)',
        type: 'number',
        min: 0,
        max: 10,
        step: 0.1,
        unit: 'L/min per kW',
        showIf: (v) => Number(getPath(v, 'cooling.liquid_capture_pct')) > 0,
      },
    ],
  },
  {
    id: 'facility',
    title: 'Facility / PUE',
    level: 'quick',
    defaultOpen: true,
    fields: [
      { name: 'facility.pue', label: 'PUE', type: 'number', min: 1, step: 0.01 },
      {
        name: 'facility.cooling_share_pct',
        label: 'Cooling share of overhead',
        type: 'number',
        optional: true,
        min: 0,
        max: 100,
        unit: '%',
        level: 'engineering',
        placeholder: 'not entered',
      },
      {
        name: 'facility.electrical_loss_share_pct',
        label: 'Electrical-loss share',
        type: 'number',
        optional: true,
        min: 0,
        max: 100,
        unit: '%',
        level: 'engineering',
        placeholder: 'not entered',
      },
      {
        name: 'facility.other_share_pct',
        label: 'Other loads share',
        type: 'number',
        optional: true,
        min: 0,
        max: 100,
        unit: '%',
        level: 'engineering',
        placeholder: 'not entered',
      },
    ],
  },
  {
    id: 'environment',
    title: 'Environment',
    level: 'engineering',
    description: 'Derating factors must come from manufacturer data; none are assumed.',
    fields: [
      { name: 'environment.ambient_temp', label: 'Inlet / ambient temperature', type: 'number' },
      {
        name: 'environment.ambient_temp_unit',
        label: 'Unit',
        type: 'select',
        options: [
          { value: 'C', label: '°C' },
          { value: 'F', label: '°F' },
        ],
      },
      { name: 'environment.altitude', label: 'Site altitude', type: 'number' },
      {
        name: 'environment.altitude_unit',
        label: 'Unit',
        type: 'select',
        options: [
          { value: 'm', label: 'm' },
          { value: 'ft', label: 'ft' },
        ],
      },
      {
        name: 'environment.ashrae_class',
        label: 'Equipment class',
        type: 'select',
        options: ['A1', 'A2', 'A3', 'A4'].map((c) => ({ value: c, label: c })),
      },
      {
        name: 'environment.humidity_pct',
        label: 'Relative humidity',
        type: 'number',
        optional: true,
        unit: '%',
        placeholder: 'optional',
      },
      {
        name: 'environment.temperature_derate_factor',
        label: 'Temperature derate factor',
        type: 'number',
        gt: 0,
        max: 1,
        step: 0.01,
      },
      {
        name: 'environment.altitude_derate_factor',
        label: 'Altitude derate factor',
        type: 'number',
        gt: 0,
        max: 1,
        step: 0.01,
      },
      {
        name: 'environment.apply_derating',
        label: 'Apply factors to generator and cooling capacity',
        type: 'checkbox',
        width: 'full',
      },
    ],
  },
  {
    id: 'utility',
    title: 'Utility / Transformer',
    level: 'engineering',
    fields: [
      {
        name: 'utility.service_voltage_v',
        label: 'Utility service voltage',
        type: 'number',
        gt: 0,
        unit: 'V',
      },
      {
        name: 'utility.service_capacity_kva',
        label: 'Utility service capacity (0 = n/a)',
        type: 'number',
        min: 0,
        unit: 'kVA',
      },
      { name: 'transformer.enabled', label: 'Include transformers', type: 'checkbox', width: 'full' },
      ...transformerFields(),
    ],
  },
  {
    id: 'generator',
    title: 'Generator',
    level: 'engineering',
    fields: [
      { name: 'generator.enabled', label: 'Include standby generators', type: 'checkbox', width: 'full' },
      ...generatorFields(),
    ],
  },
  {
    id: 'bess',
    title: 'BESS',
    level: 'engineering',
    fields: [
      { name: 'bess.enabled', label: 'Include battery energy storage', type: 'checkbox', width: 'full' },
      ...bessFields('bess', is('bess.enabled', true)),
    ],
  },
  {
    id: 'space',
    title: 'Space / White Space',
    level: 'standard',
    fields: [
      {
        name: 'space.room_area',
        label: 'Room (white-space) area',
        type: 'number',
        optional: true,
        gt: 0,
        placeholder: 'optional',
      },
      { name: 'space.room_area_unit', label: 'Unit', type: 'select', options: AREA_UNITS },
    ],
  },
  {
    id: 'financial',
    title: 'Financial / Energy Cost',
    level: 'standard',
    description: 'Flat-rate estimate. Real utility tariffs vary.',
    fields: [
      {
        name: 'financial.electricity_rate',
        label: 'Energy rate',
        type: 'number',
        min: 0,
        step: 0.001,
        unit: '/kWh',
      },
      { name: 'financial.demand_charge', label: 'Demand charge', type: 'number', min: 0, unit: '/kW-month' },
      { name: 'financial.currency', label: 'Currency (ISO code)', type: 'text' },
    ],
  },
  {
    id: 'advanced',
    title: 'Advanced Assumptions',
    level: 'engineering',
    fields: [
      {
        name: 'advanced.hours_per_year',
        label: 'Operating hours per year',
        type: 'number',
        gt: 0,
        max: 8784,
        unit: 'h',
      },
      {
        name: 'advanced.facility_power_factor',
        label: 'Facility power factor',
        type: 'number',
        optional: true,
        gt: 0,
        max: 1,
        step: 0.01,
        placeholder: 'same as IT PF',
      },
    ],
  },
];

export function batteryFields(prefix = 'ups.battery'): FieldDef[] {
  const on = is(`${prefix}.enabled`, true);
  return [
    {
      name: `${prefix}.chemistry`,
      label: 'Chemistry',
      type: 'select',
      showIf: on,
      options: [
        { value: 'li_ion', label: 'Lithium-ion' },
        { value: 'vrla', label: 'VRLA' },
        { value: 'nicd', label: 'NiCd' },
        { value: 'other', label: 'Other' },
      ],
    },
    {
      name: `${prefix}.nominal_voltage`,
      label: 'Nominal DC voltage',
      type: 'number',
      gt: 0,
      unit: 'V',
      showIf: on,
    },
    { name: `${prefix}.capacity_kwh`, label: 'Capacity', type: 'number', min: 0, unit: 'kWh', showIf: on },
    { name: `${prefix}.capacity_ah`, label: 'or capacity', type: 'number', min: 0, unit: 'Ah', showIf: on },
    {
      name: `${prefix}.discharge_efficiency`,
      label: 'Discharge efficiency',
      type: 'number',
      gt: 0,
      max: 1,
      step: 0.01,
      showIf: on,
    },
    {
      name: `${prefix}.degradation_pct`,
      label: 'Capacity degradation',
      type: 'number',
      min: 0,
      max: 99,
      unit: '%',
      showIf: on,
    },
    {
      name: `${prefix}.runtime_target_min`,
      label: 'Runtime target',
      type: 'number',
      gt: 0,
      unit: 'min',
      showIf: on,
    },
  ];
}

export function transformerFields(
  prefix = 'transformer',
  gate = is('transformer.enabled', true),
): FieldDef[] {
  return [
    {
      name: `${prefix}.primary_voltage_v`,
      label: 'Primary voltage',
      type: 'number',
      gt: 0,
      unit: 'V',
      showIf: gate,
    },
    {
      name: `${prefix}.secondary_voltage_v`,
      label: 'Secondary voltage',
      type: 'number',
      gt: 0,
      unit: 'V',
      showIf: gate,
    },
    {
      name: `${prefix}.kva_rating`,
      label: 'Rating per unit',
      type: 'number',
      gt: 0,
      unit: 'kVA',
      showIf: gate,
    },
    { name: `${prefix}.quantity`, label: 'Quantity', type: 'number', integer: true, min: 1, showIf: gate },
    {
      name: `${prefix}.redundancy`,
      label: 'Redundancy',
      type: 'select',
      options: REDUNDANCY_OPTIONS,
      showIf: gate,
    },
    {
      name: `${prefix}.efficiency`,
      label: 'Efficiency',
      type: 'number',
      gt: 0,
      max: 1,
      step: 0.001,
      showIf: gate,
    },
    {
      name: `${prefix}.impedance_pct`,
      label: 'Impedance',
      type: 'number',
      gt: 0,
      unit: '%Z',
      step: 0.01,
      showIf: gate,
    },
    {
      name: `${prefix}.target_utilization_pct`,
      label: 'Target utilization',
      type: 'number',
      gt: 0,
      max: 100,
      unit: '%',
      showIf: gate,
    },
  ];
}

export function generatorFields(prefix = 'generator', gate = is('generator.enabled', true)): FieldDef[] {
  return [
    {
      name: `${prefix}.load_basis`,
      label: 'Generator-backed load',
      type: 'select',
      showIf: gate,
      width: 'full',
      options: [
        { value: 'it_only', label: 'Critical IT only' },
        { value: 'it_cooling', label: 'IT + cooling' },
        { value: 'full', label: 'Full facility' },
        { value: 'custom', label: 'Custom essential load' },
      ],
    },
    {
      name: `${prefix}.custom_load_kw`,
      label: 'Custom essential load',
      type: 'number',
      min: 0,
      unit: 'kW',
      showIf: (v) => gate(v) && getPath(v, `${prefix}.load_basis`) === 'custom',
    },
    { name: `${prefix}.unit_kw`, label: 'Unit rating', type: 'number', gt: 0, unit: 'kW', showIf: gate },
    { name: `${prefix}.unit_kva`, label: 'Unit rating', type: 'number', gt: 0, unit: 'kVA', showIf: gate },
    {
      name: `${prefix}.power_factor`,
      label: 'Load power factor',
      type: 'number',
      gt: 0,
      max: 1,
      step: 0.01,
      showIf: gate,
    },
    { name: `${prefix}.quantity`, label: 'Quantity', type: 'number', integer: true, min: 1, showIf: gate },
    {
      name: `${prefix}.redundancy`,
      label: 'Redundancy',
      type: 'select',
      options: REDUNDANCY_OPTIONS,
      showIf: gate,
    },
    {
      name: `${prefix}.step_load_pct`,
      label: 'Step-load limit',
      type: 'number',
      gt: 0,
      max: 100,
      unit: '%',
      showIf: gate,
    },
    {
      name: `${prefix}.target_loading_pct`,
      label: 'Target loading',
      type: 'number',
      gt: 0,
      max: 100,
      unit: '%',
      showIf: gate,
    },
  ];
}

export function bessFields(
  prefix: string,
  gate: (v: Values) => boolean = () => true,
  withBasis = true,
): FieldDef[] {
  const basis: FieldDef[] = withBasis
    ? [
        {
          name: `${prefix}.power_basis`,
          label: 'Power requirement',
          type: 'select',
          showIf: gate,
          options: [
            { value: 'facility', label: 'Facility load' },
            { value: 'it', label: 'IT load' },
            { value: 'custom', label: 'Custom' },
          ],
        },
        {
          name: `${prefix}.custom_power_mw`,
          label: 'Custom power',
          type: 'number',
          gt: 0,
          unit: 'MW',
          showIf: (v) => gate(v) && getPath(v, `${prefix}.power_basis`) === 'custom',
        },
      ]
    : [];
  return [
    ...basis,
    {
      name: `${prefix}.duration_min`,
      label: 'Backup duration',
      type: 'number',
      gt: 0,
      unit: 'min',
      showIf: gate,
    },
    {
      name: `${prefix}.dc_bus_voltage`,
      label: 'DC bus voltage',
      type: 'number',
      gt: 0,
      unit: 'V DC',
      showIf: gate,
    },
    {
      name: `${prefix}.pcs_efficiency`,
      label: 'PCS efficiency',
      type: 'number',
      gt: 0,
      max: 1,
      step: 0.01,
      showIf: gate,
    },
    {
      name: `${prefix}.battery_efficiency`,
      label: 'Battery efficiency',
      type: 'number',
      gt: 0,
      max: 1,
      step: 0.01,
      showIf: gate,
    },
    {
      name: `${prefix}.depth_of_discharge`,
      label: 'Depth of discharge',
      type: 'number',
      gt: 0,
      max: 1,
      step: 0.01,
      showIf: gate,
    },
    {
      name: `${prefix}.eol_capacity_factor`,
      label: 'End-of-life capacity',
      type: 'number',
      gt: 0,
      max: 1,
      step: 0.01,
      showIf: gate,
    },
    {
      name: `${prefix}.redundancy`,
      label: 'Redundancy',
      type: 'select',
      showIf: gate,
      options: [
        { value: 'N', label: 'N' },
        { value: 'N+1', label: 'N+1' },
      ],
    },
    {
      name: `${prefix}.container_power_mw`,
      label: 'Container PCS power',
      type: 'number',
      gt: 0,
      unit: 'MW',
      showIf: gate,
    },
    {
      name: `${prefix}.container_energy_mwh`,
      label: 'Container nameplate energy',
      type: 'number',
      gt: 0,
      unit: 'MWh',
      showIf: gate,
    },
  ];
}
