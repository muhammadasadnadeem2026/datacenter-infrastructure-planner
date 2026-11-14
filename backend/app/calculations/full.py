"""Full project calculation: orchestrates every module in dependency order.

Rack power -> IT load -> kVA -> circuits -> PDU -> UPS -> facility -> transformer ->
utility -> generator -> BESS -> cooling -> energy -> capacity balance -> warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.calculations import (
    bess as bess_mod,
)
from app.calculations import (
    cooling,
    electrical,
    energy,
    environment,
    facility,
    generator,
    it_load,
    pdu,
    rack_count,
    rack_density,
    transformer,
    ups,
    warnings,
)
from app.calculations.capacity import build_capacity_balance
from app.calculations.flow import build_power_flow, build_sankey
from app.calculations.trace import ModuleResult
from app.constants.receptacles import CUSTOM_RECEPTACLE_ID, get_receptacle
from app.schemas.inputs import ElectricalInputs, ProjectInputs
from app.version import CALC_ENGINE_VERSION

# Summary cards: (id, label, imperial (module, key), metric (module, key))
SUMMARY_CARDS: list[tuple[str, str, tuple[str, str], tuple[str, str]]] = [
    ("it_load", "IT Load", ("it", "it_kw"), ("it", "it_kw")),
    ("facility_load", "Facility Load", ("facility", "facility_kw"), ("facility", "facility_kw")),
    ("per_rack", "Per Rack", ("it", "kw_per_rack"), ("it", "kw_per_rack")),
    ("apparent_power", "Apparent Power", ("it", "it_kva"), ("it", "it_kva")),
    ("cooling_tons", "Cooling", ("cooling", "tons"), ("cooling", "tons")),
    ("heat_load", "Heat Load", ("cooling", "btu_hr"), ("cooling", "thermal_kw")),
    ("rack_count", "Racks", ("it", "rack_count"), ("it", "rack_count")),
    ("area_density", "Area Density", ("space", "w_per_ft2"), ("space", "w_per_m2")),
    ("ups_installed", "UPS Installed", ("ups", "installed_kva"), ("ups", "installed_kva")),
    ("circuit_loading", "Circuit Loading", ("circuit", "loading_pct"), ("circuit", "loading_pct")),
    ("transformer_loading", "Transformer Loading", ("transformer", "loading_pct"), ("transformer", "loading_pct")),
    ("generator_loading", "Generator Loading", ("generator", "loading_pct"), ("generator", "loading_pct")),
    ("bess_size", "BESS Size", ("bess", "installed_mwh"), ("bess", "installed_mwh")),
    ("annual_energy", "Annual Energy", ("energy", "annual_facility_mwh"), ("energy", "annual_facility_mwh")),
    ("annual_cost", "Annual Cost", ("energy", "annual_cost"), ("energy", "annual_cost")),
]


@dataclass
class FullCalculation:
    inputs: ProjectInputs
    modules: dict[str, ModuleResult]
    capacity: dict[str, Any]
    warnings: list[dict]
    power_flow: dict[str, Any]
    sankey: dict[str, Any]
    summary: list[dict[str, Any]] = field(default_factory=list)
    engine_version: str = CALC_ENGINE_VERSION
    calculated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "calculated_at": self.calculated_at,
            "mode": self.inputs.mode,
            "unit_system": self.inputs.unit_system,
            "modules": {k: m.to_dict() for k, m in self.modules.items()},
            "capacity": self.capacity,
            "warnings": self.warnings,
            "power_flow": self.power_flow,
            "sankey": self.sankey,
            "summary": self.summary,
        }


def resolve_circuit(e: ElectricalInputs) -> tuple[float, float, str, float, str]:
    """Library receptacles are authoritative; 'custom' uses the entered values."""
    if e.receptacle_id != CUSTOM_RECEPTACLE_ID:
        rec = get_receptacle(e.receptacle_id)
        if rec is None:
            raise ValueError(f"unknown receptacle '{e.receptacle_id}'")
        return rec["voltage"], rec["amps"], rec["phase"], rec["continuous_derate"], rec["name"]
    return e.voltage, e.current, e.phase, e.continuous_derate, "Custom circuit"


def _summary(modules: dict[str, ModuleResult]) -> list[dict[str, Any]]:
    cards = []
    for cid, label, imp, met in SUMMARY_CARDS:
        if imp[0] in modules and imp[1] in modules[imp[0]].steps:
            cards.append({"id": cid, "label": label,
                          "imperial": {"module": imp[0], "key": imp[1]},
                          "metric": {"module": met[0], "key": met[1]}})
    return cards


def run_full_calculation(inp: ProjectInputs) -> FullCalculation:
    standard = inp.mode in ("standard", "engineering")
    engineering = inp.mode == "engineering"
    modules: dict[str, ModuleResult] = {}
    pf = inp.it.power_factor

    # IT load
    it = it_load.compute_it_load(
        input_mode=inp.it.input_mode, rack_count=inp.it.rack_count, kw_per_rack=inp.it.kw_per_rack,
        power_factor=pf, utilization_pct=inp.it.utilization_pct, devices=inp.it.devices,
    )
    modules["it"] = it
    it_kw = it.v("it_kw")
    racks = it.v("rack_count")
    per_rack = it.v("kw_per_rack")

    rc = rack_count.compute_rack_count(it_kw=it_kw, rack_power_kw=inp.rack.rack_rating_kw, racks_planned=racks)
    modules["rack_count"] = rc

    if standard and inp.space.room_area:
        modules["space"] = rack_density.compute_space(
            it_kw=it_kw, rack_count=racks, area_value=inp.space.room_area, area_unit=inp.space.room_area_unit)

    # Rack electrical
    if standard:
        v, a, ph, derate, name = resolve_circuit(inp.electrical)
        modules["circuit"] = electrical.compute_circuit(
            voltage=v, current=a, phase=ph, continuous_factor=derate, rack_kw=per_rack, power_factor=pf,
            circuits_per_rack=inp.electrical.circuits_per_rack, receptacle_name=name,
        )
        modules["pdu"] = pdu.compute_pdu(
            rack_kw=per_rack, power_factor=pf, growth_margin_pct=inp.pdu.growth_margin_pct,
            voltage=inp.pdu.voltage, amperage=inp.pdu.amperage, phase=inp.pdu.phase,
            continuous_factor=inp.pdu.continuous_derate, feed=inp.pdu.feed,
        )
        modules["ups"] = ups.compute_ups(
            load_kw=it_kw, power_factor=pf, target_load_pct=inp.ups.target_load_pct,
            redundancy=inp.ups.redundancy, modules_n=inp.ups.modules_n, module_kva=inp.ups.module_kva,
        )
        b = inp.ups.battery
        if b.enabled:
            modules["battery"] = ups.compute_battery(
                load_kw=it_kw, chemistry=b.chemistry, nominal_voltage=b.nominal_voltage,
                capacity_kwh=b.capacity_kwh, capacity_ah=b.capacity_ah,
                discharge_efficiency=b.discharge_efficiency, degradation_pct=b.degradation_pct,
                runtime_target_min=b.runtime_target_min,
            )

    # Facility
    facility_pf = inp.advanced.facility_power_factor or pf
    fac = facility.compute_facility(
        it_kw=it_kw, pue=inp.facility.pue, power_factor=facility_pf,
        cooling_share_pct=inp.facility.cooling_share_pct,
        electrical_loss_share_pct=inp.facility.electrical_loss_share_pct,
        other_share_pct=inp.facility.other_share_pct,
    )
    modules["facility"] = fac
    fac_kw = fac.v("facility_kw")

    # Environment
    derate = 1.0
    if engineering:
        e = inp.environment
        env = environment.compute_environment(
            ambient_temp=e.ambient_temp, temp_unit=e.ambient_temp_unit, altitude=e.altitude,
            altitude_unit=e.altitude_unit, ashrae_class=e.ashrae_class, humidity_pct=e.humidity_pct,
            temperature_factor=e.temperature_derate_factor, altitude_factor=e.altitude_derate_factor,
        )
        modules["environment"] = env
        if e.apply_derating:
            derate = env.v("combined_factor")

    # Cooling
    extra_heat = fac.get("electrical_losses_kw", 0.0) if standard else 0.0
    c = inp.cooling
    modules["cooling"] = cooling.compute_cooling(
        it_kw=it_kw, rack_count=racks, kw_per_rack=per_rack,
        additional_heat_kw=extra_heat,
        additional_heat_note="Electrical distribution losses assumed rejected to room cooling." if extra_heat else "",
        unit_capacity_kw=c.unit_capacity_kw if standard else 0, unit_count=c.unit_count if standard else 0,
        redundancy=c.redundancy, capacity_factor=derate,
        liquid_capture_pct=c.liquid_capture_pct, coolant_flow_lpm_per_kw=c.coolant_flow_lpm_per_kw,
    )

    # Utility / transformer
    if engineering:
        modules["utility"] = ModuleResult("utility")
        modules["utility"].add("service_capacity_kva", "Utility service capacity", inp.utility.service_capacity_kva,
                               "kVA", "Input", f"{inp.utility.service_capacity_kva:g}",
                               assumption="0 means not configured.")
        t = inp.transformer
        if t.enabled:
            modules["transformer"] = transformer.compute_transformer(
                required_kva=fac.v("facility_kva"), primary_voltage=t.primary_voltage_v,
                secondary_voltage=t.secondary_voltage_v, kva_rating=t.kva_rating, efficiency=t.efficiency,
                impedance_pct=t.impedance_pct, quantity=t.quantity, redundancy=t.redundancy,
                target_utilization_pct=t.target_utilization_pct,
            )
        g = inp.generator
        if g.enabled:
            load_kw, note = _generator_load(g.load_basis, g.custom_load_kw, it_kw, fac)
            modules["generator"] = generator.compute_generator(
                critical_load_kw=load_kw, load_basis=g.load_basis, load_basis_note=note, unit_kw=g.unit_kw,
                unit_kva=g.unit_kva, power_factor=g.power_factor, quantity=g.quantity, redundancy=g.redundancy,
                step_load_pct=g.step_load_pct, target_loading_pct=g.target_loading_pct, derate_factor=derate,
            )
        bs = inp.bess
        if bs.enabled:
            power_mw, note = _bess_power(bs.power_basis, bs.custom_power_mw, it, fac)
            modules["bess"] = bess_mod.compute_bess(
                power_mw=power_mw, power_basis_note=note, duration_min=bs.duration_min,
                dc_bus_voltage=bs.dc_bus_voltage, pcs_efficiency=bs.pcs_efficiency,
                battery_efficiency=bs.battery_efficiency, depth_of_discharge=bs.depth_of_discharge,
                eol_capacity_factor=bs.eol_capacity_factor, redundancy=bs.redundancy,
                container_power_mw=bs.container_power_mw, container_energy_mwh=bs.container_energy_mwh,
            )

    # Energy
    modules["energy"] = energy.compute_energy(
        it_kw=it_kw, facility_kw=fac_kw, electricity_rate=inp.financial.electricity_rate,
        demand_charge=inp.financial.demand_charge, hours_per_year=inp.advanced.hours_per_year,
        utilization_pct=inp.it.utilization_pct, currency=inp.financial.currency,
    )

    balance = build_capacity_balance(
        it_kw=it_kw, modules=modules, rack_capacity_kw=rc.v("planned_rack_kw"), facility_pf=facility_pf,
        it_pf=pf, utility_capacity_kva=inp.utility.service_capacity_kva,
    )
    ws = warnings.evaluate(modules, balance, {
        "transformer": inp.transformer.target_utilization_pct,
        "generator": inp.generator.target_loading_pct,
    })
    return FullCalculation(
        inputs=inp, modules=modules, capacity=balance, warnings=ws,
        power_flow=build_power_flow(modules, balance, utility_voltage=inp.utility.service_voltage_v),
        sankey=build_sankey(fac), summary=_summary(modules),
    )


def _generator_load(basis: str, custom_kw: float, it_kw: float, fac: ModuleResult) -> tuple[float, str]:
    if basis == "it_only":
        return it_kw, "Only critical IT load is generator-backed."
    if basis == "it_cooling":
        cool_kw = fac.get("cooling_kw")
        if cool_kw is not None and fac.data["split_given"]:
            return it_kw + cool_kw, "IT load plus the entered cooling share of facility overhead."
        return fac.v("facility_kw"), ("Cooling share of overhead not entered; conservatively using the full "
                                      "facility load (IT × PUE).")
    if basis == "custom":
        return custom_kw, "User-entered essential load."
    return fac.v("facility_kw"), "Full facility load (IT × PUE) is generator-backed."


def _bess_power(basis: str, custom_mw: float, it: ModuleResult, fac: ModuleResult) -> tuple[float, str]:
    if basis == "it":
        return it.v("it_mw"), "BESS sized for the IT load."
    if basis == "facility":
        return fac.v("facility_mw"), "BESS sized for the full facility load (IT × PUE)."
    return custom_mw, "User-entered BESS power requirement."
