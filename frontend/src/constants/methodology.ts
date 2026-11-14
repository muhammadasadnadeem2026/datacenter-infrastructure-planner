/**
 * Methodology documentation. Descriptive text only — the executable formulas live in
 * backend/app/calculations and are the single authoritative implementation.
 */
export interface MethodSection {
  id: string;
  title: string;
  intro: string;
  equations: { name: string; eq: string; note?: string }[];
}

export const METHODOLOGY: MethodSection[] = [
  {
    id: 'it-load',
    title: 'IT Load',
    intro: 'Design IT load drives all sizing. Two input modes are supported.',
    equations: [
      { name: 'Rack average', eq: 'P_IT = N_racks × P_rack' },
      {
        name: 'Device list',
        eq: 'P_IT = Σ (Qty_i × P_nameplate,i × u_i) / 1000',
        note: 'u_i = expected utilization as a fraction.',
      },
      { name: 'Per-rack load', eq: 'P_rack,avg = P_IT / N_racks' },
      { name: 'Operating load (energy only)', eq: 'P_op = P_IT × u_avg' },
    ],
  },
  {
    id: 'power-factor',
    title: 'Power Factor',
    intro: 'Real power (kW) and apparent power (kVA) are related by the power factor PF, 0 < PF ≤ 1.',
    equations: [
      { name: 'Apparent power', eq: 'S (kVA) = P (kW) / PF' },
      { name: 'Real power', eq: 'P (kW) = S (kVA) × PF' },
    ],
  },
  {
    id: 'single-phase',
    title: 'Single-Phase Power',
    intro: 'Capacity of a single-phase circuit at voltage V and current I.',
    equations: [
      { name: 'Circuit capacity', eq: 'S = V × I / 1000' },
      { name: 'Current', eq: 'I = S × 1000 / V' },
    ],
  },
  {
    id: 'three-phase',
    title: 'Three-Phase Power',
    intro: 'Balanced three-phase circuit with line-to-line voltage V_LL.',
    equations: [
      { name: 'Circuit capacity', eq: 'S = √3 × V_LL × I / 1000' },
      { name: 'Line current', eq: 'I = S × 1000 / (√3 × V_LL)' },
      { name: 'Balanced load per phase', eq: 'S_phase = S / 3' },
    ],
  },
  {
    id: 'continuous',
    title: 'Continuous Loads',
    intro:
      'Rack loads are treated as continuous. The usable capacity of a circuit is its rating times a continuous-load factor k (default 0.80, editable; verify against the adopted electrical code).',
    equations: [
      { name: 'Usable capacity', eq: 'S_usable = S_circuit × k' },
      { name: 'Minimum circuits', eq: 'n = ⌈ S_rack / S_usable ⌉', note: 'S_rack = P_rack / PF' },
      { name: 'Loading of rating', eq: 'L = S_rack / (n × S_circuit) × 100 %' },
      {
        name: 'Status bands',
        eq: 'L ≤ 0.875·k·100 → normal;  ≤ k·100 → caution;  > k·100 → fails',
        note: 'With k = 0.80 this gives the 70 % / 80 % bands. Loading is measured against the circuit rating, so the 80 % limit is not applied twice.',
      },
    ],
  },
  {
    id: 'cooling',
    title: 'Cooling',
    intro: 'Essentially all IT electrical power becomes heat that the cooling system must reject.',
    equations: [
      { name: 'Thermal load', eq: 'Q (kW th) = P_IT' },
      { name: 'BTU/hr', eq: 'Q (BTU/hr) = P_IT × 3412.142' },
      { name: 'Refrigeration tons', eq: 'T = Q (BTU/hr) / 12 000' },
      {
        name: 'Room heat (optional)',
        eq: 'Q_room = Q_IT + P_electrical losses',
        note: 'Only when an electrical-loss share is entered.',
      },
      { name: 'Usable cooling', eq: 'Q_usable = q_unit × k_env × n_usable' },
    ],
  },
  {
    id: 'pue',
    title: 'PUE and Facility Power',
    intro:
      'Power Usage Effectiveness is total facility power divided by IT power. PUE alone does not identify how overhead divides between cooling, electrical losses and other loads; that split is shown only when entered.',
    equations: [
      { name: 'Facility power', eq: 'P_fac = P_IT × PUE' },
      { name: 'Overhead', eq: 'P_ovh = P_fac − P_IT' },
      { name: 'IT share', eq: 'IT % = P_IT / P_fac × 100' },
      { name: 'Facility apparent power', eq: 'S_fac = P_fac / PF_fac' },
    ],
  },
  {
    id: 'ups',
    title: 'UPS',
    intro:
      'The UPS is sized so that the non-redundant (N) capacity runs at the target loading at design load.',
    equations: [
      { name: 'UPS load', eq: 'S_load = P_IT / PF' },
      { name: 'Required (before redundancy)', eq: 'S_req = S_load / f_target' },
      { name: 'Redundancy multiplier', eq: 'N: 1.0   N+1: (n+1)/n   2N: 2.0' },
      { name: 'Installed', eq: 'S_inst = S_req × m;   module = S_inst / modules' },
      {
        name: 'Battery runtime (optional)',
        eq: 't = E_nameplate × (1 − d) × η / P_load × 60',
        note: 'Idealized constant-power estimate. Runtime is never derived from kVA alone; manufacturer discharge curves govern.',
      },
    ],
  },
  {
    id: 'pdu',
    title: 'PDU',
    intro: 'Rack PDUs are sized per feed. With A/B feeds, each feed must carry the full design load alone.',
    equations: [
      { name: 'Design load', eq: 'P_design = P_rack × (1 + g)' },
      { name: 'PDUs per feed', eq: 'n = ⌈ (P_design / PF) / (S_PDU × k) ⌉' },
      { name: 'Design-case loading', eq: 'L = (S_rack / n) / S_PDU × 100 %' },
    ],
  },
  {
    id: 'rack-density',
    title: 'Rack Density',
    intro:
      'Density drives the cooling approach. Classification bands are configurable in backend/app/constants/cooling.py.',
    equations: [
      { name: 'Area density', eq: 'D = P_IT × 1000 / A   (W/ft² or W/m²)' },
      { name: 'Racks required', eq: 'N = ⌈ P_IT / P_rack,rated ⌉' },
      {
        name: 'Cooling bands (kW/rack)',
        eq: '≤5 conventional · ≤12 containment · ≤20 high-density air · ≤50 rear-door/hybrid · >50 liquid',
      },
    ],
  },
  {
    id: 'transformer',
    title: 'Transformer',
    intro:
      'Transformers serve the facility apparent load. Loading is evaluated with redundant units out of service.',
    equations: [
      { name: 'Loading', eq: 'L = S_fac / (S_unit × n_usable) × 100 %' },
      { name: 'Full-load current', eq: 'I_FL = S_unit × 1000 / (√3 × V_LL)' },
      {
        name: 'Approx. terminal fault current',
        eq: 'I_SC ≈ I_FL / (Z% / 100)',
        note: 'Infinite-source approximation at the transformer terminals. Not a substitute for a short-circuit study.',
      },
      { name: 'Utility-side kVA', eq: 'S_in = S_fac / η' },
    ],
  },
  {
    id: 'generator',
    title: 'Generator',
    intro:
      'The generator-backed load is selected explicitly (IT only, IT + cooling, full facility, custom) — never assumed.',
    equations: [
      { name: 'Unit usable rating', eq: 'P_unit = min(P_kW, S_kVA × PF) × k_site' },
      { name: 'Required capacity', eq: 'P_req = P_backed / f_target' },
      { name: 'Units', eq: 'n = ⌈ P_req / P_unit ⌉  then apply N / N+1 / 2N' },
      { name: 'Check', eq: 'P_unit × n_usable ≥ P_backed' },
    ],
  },
  {
    id: 'bess',
    title: 'BESS',
    intro:
      'AC (PCS) power and DC (battery) energy are sized separately; the container count is the larger of the two.',
    equations: [
      { name: 'Load energy', eq: 'E_load = P_MW × t_h' },
      { name: 'Battery energy', eq: 'E_batt = E_load / (η_PCS × η_batt × DoD × EOL)' },
      { name: 'Containers', eq: 'n = max(⌈P / P_container⌉, ⌈E_batt / E_container⌉) (+1 for N+1)' },
      { name: 'DC current', eq: 'I_DC = (P_AC / η_PCS) × 10⁶ / V_DC' },
    ],
  },
  {
    id: 'energy',
    title: 'Annual Energy',
    intro: 'A flat-rate estimate. Real tariffs (time-of-use, tiers, riders, taxes) vary.',
    equations: [
      { name: 'Annual facility energy', eq: 'E = P_fac × u_avg × 8760 h' },
      { name: 'Energy charge', eq: 'C_E = E × rate' },
      { name: 'Demand charge', eq: 'C_D = P_fac × $/kW-month × 12' },
      { name: 'Monthly average', eq: '(C_E + C_D) / 12' },
    ],
  },
  {
    id: 'units',
    title: 'Units',
    intro: 'Conversion constants used throughout the engine.',
    equations: [
      { name: 'Heat', eq: '1 kW = 3412.142 BTU/hr;  1 ton = 12 000 BTU/hr' },
      { name: 'Area', eq: '1 ft² = 0.09290304 m²' },
      { name: 'Length', eq: '1 ft = 0.3048 m' },
      { name: 'Temperature', eq: '°C = (°F − 32) × 5/9' },
    ],
  },
  {
    id: 'warnings',
    title: 'Warnings and Assumptions',
    intro:
      'A centralized warning engine evaluates every result (circuit loading, UPS target, transformer and generator capacity, rack density, area density, PF, PUE plausibility, redundancy, BESS DC current, environment). Thresholds live in backend/app/constants/thresholds.py. Every result states its assumption; saved studies store the engine version so later formula changes never silently alter them.',
    equations: [
      { name: 'Capacity status', eq: 'L ≤ 80 % → OK;  ≤ 100 % → Caution;  > 100 % → Critical' },
      { name: 'Bottleneck', eq: 'argmax(L_i)   and   P_IT,max,i = P_IT × S_usable,i / S_required,i' },
    ],
  },
];
