# Calculation engine

Engine version: see `backend/app/version.py` (`CALC_ENGINE_VERSION`).

## Architecture

```
ProjectInputs (Pydantic, validated)
      │
      ▼
calculations/full.py  ── orchestrates, in dependency order:
  it_load → rack_count → space → circuit → pdu → ups (+battery) → facility
  → environment → cooling → utility → transformer → generator → bess → energy
  → capacity balance → warnings → power flow / Sankey → summary cards
      │
      ▼
FullCalculation.to_dict()  ──►  API response  ──►  React UI
                             ──►  PDF report / XLSX / CSV
                             ──►  saved project (with engine version)
```

- **Pure functions** (e.g. `electrical.three_phase_kva(v, a)`) hold each formula exactly once.
- **Traced modules** (`compute_*`) call the pure functions and record a `Step` for every result:
  `key, label, value, unit, formula, substitution, assumption, reference`.
- API routes and exporters never compute; they reshape `Step`s.
- Mode gating: *quick* computes IT, rack, facility, cooling and energy; *standard* adds space,
  circuit, PDU, UPS, battery and cooling-plant capacity; *engineering* adds environment,
  utility, transformer, generator and BESS.

## Formulas

| Module | Result | Formula |
|---|---|---|
| IT | IT load (rack mode) | `P = racks × kW_per_rack` |
| IT | IT load (device mode) | `P = Σ(qty × W_nameplate × utilization) / 1000` |
| IT | Apparent power | `kVA = kW / PF` |
| Electrical | 1-φ capacity | `kVA = V × A / 1000` |
| Electrical | 3-φ capacity | `kVA = √3 × V × A / 1000` |
| Electrical | Usable | `kVA_usable = kVA × k_continuous` (default 0.80) |
| Electrical | Circuits | `n = ceil(kVA_rack / kVA_usable)` |
| Electrical | Loading | `L = kVA_rack / (n × kVA_circuit) × 100` |
| PDU | Design load | `kW × (1 + growth)`; per-feed count as circuits; A/B doubles the count |
| UPS | Required | `kVA_load / target` |
| UPS | Redundancy | N = 1, N+1 = (n+1)/n, 2N = 2 |
| Cooling | Heat | `BTU/hr = kW × 3412.142`, `tons = BTU/hr / 12000` |
| Facility | Power | `kW_fac = kW_IT × PUE` |
| Energy | Annual | `kWh = kW × utilization × hours`; cost = kWh × rate + peak kW × demand × 12 |
| Transformer | Loading | `kVA_fac / (kVA_unit × usable_units)` |
| Transformer | FLA | `I = kVA × 1000 / (√3 × V_LL)` |
| Transformer | Fault (approx.) | `I_SC = FLA / (Z%/100)` — infinite-source, terminal only |
| Generator | Unit rating | `min(kW, kVA × PF) × site_derate` |
| BESS | Battery energy | `E_load / (η_PCS × η_batt × DoD × EOL)` |
| BESS | Containers | `max(ceil(MW/MW_c), ceil(MWh/MWh_c))` (+1 for N+1) |
| BESS | DC current | `I = (P_AC / η_PCS) × 10⁶ / V_DC` |
| Rack count | Racks | `ceil(kW_IT / kW_rack)` |

### Engineering decisions worth knowing

1. **Circuit loading is measured against the circuit rating, not the derated capacity.** The
   continuous-load limit (80 % by default) is then applied once. Comparing rack load to the
   already-derated capacity and *then* checking against 80 % would double-derate and falsely
   fail correctly-sized circuits. The "% of usable capacity" value is also reported.
   Status bands scale with the continuous factor: k = 0.80 gives ≤70 % normal,
   ≤80 % caution, >80 % fail; exactly 80 % is *caution*, not failure.
2. **Redundancy**: usable units are all (N), installed − 1 (N+1) or installed / 2 (2N).
   Capacity checks always use usable capacity. Validation rejects N+1 with fewer than 2 units
   and 2N with an odd count.
3. **BESS container energy is treated as beginning-of-life nameplate**, so DoD and EOL are
   applied once, in the battery-energy formula.
4. **Generator load basis is explicit** (IT only, IT + cooling, full facility, custom). "IT +
   cooling" without an entered cooling share conservatively uses the full facility load and
   says so in the assumption.
5. **PUE does not identify the overhead split.** Unless you enter shares, the Sankey shows a
   single "Facility Overhead" flow.
6. **Battery runtime** is only computed from battery energy data and is labelled as an
   idealized constant-power estimate.
7. **Capacity balance** compares like with like (kW, kVA, kW thermal, MW, MWh) and ranks
   systems by loading %. It also reports the maximum IT load each system could carry at the
   current ratios, which makes the bottleneck unit-independent.

## Validation

Pydantic (`allow_inf_nan=False`, `extra="forbid"`) rejects NaN / ±Infinity, unknown fields,
non-positive ratings, PF ∉ (0, 1], PUE < 1, efficiencies ∉ (0, 1], UPS target ∉ (0, 100],
negative rates, area ≤ 0, invalid redundancy/quantity combinations and overhead shares
above 100 %. The frontend Zod schema mirrors these rules for instant feedback; the backend
never trusts it.

## Warnings

`calculations/warnings.py` is the only place warning logic lives. Each warning has
`severity (info | caution | critical), code, title, message, affected_system, reference`.
Thresholds are in `constants/thresholds.py`.

## Versioning

`CALC_ENGINE_VERSION` follows semver: MAJOR when a formula, constant or default changes
numeric results; MINOR for new outputs; PATCH for wording. Saved projects keep the version
that produced them. *Recalculate* on the Projects page (`POST /api/projects/{id}/recalculate`)
is the only way to move a study to a newer engine.

## Tests

`backend/tests` covers every spec example (63.1579 kVA, 204,728.52 BTU/hr, 17.0607 tons,
90 kW, 788,400 kWh, $102,492, 6.24 / 4.992 kVA, 3 circuits, 332.55 kVA), boundaries (PF = 1,
PF = 0, zero racks, exactly 80 % loading, NaN/Infinity), propagation across modules,
bottleneck detection with PF, MW-scale BESS and 300 MW AI deployments, plus API integration
tests for every endpoint, project CRUD and exports.
