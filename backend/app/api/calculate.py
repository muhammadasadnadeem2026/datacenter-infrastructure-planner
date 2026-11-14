"""Calculation endpoints. No formulas here: every route delegates to app.calculations."""

from __future__ import annotations

from fastapi import APIRouter

from app.calculations import (
    bess,
    cooling,
    electrical,
    generator,
    it_load,
    pdu,
    rack_count,
    rack_density,
    transformer,
    units,
    ups,
)
from app.calculations import warnings as W
from app.calculations.ai_rack import compute_ai_cluster
from app.calculations.full import resolve_circuit, run_full_calculation
from app.schemas.inputs import (
    AIRackRequest,
    BESSRequest,
    CircuitRequest,
    ConvertRequest,
    CoolingRequest,
    ElectricalInputs,
    GeneratorRequest,
    ITLoadRequest,
    PDURequest,
    PowerConversionRequest,
    ProjectInputs,
    RackCountRequest,
    RackDensityRequest,
    TransformerRequest,
    UPSRequest,
)
from app.schemas.results import FullResponse, ToolResponse, full_response, tool_response

router = APIRouter(prefix="/api/calculate", tags=["calculate"])


@router.post("/full", response_model=FullResponse, summary="Full project calculation")
def calc_full(body: ProjectInputs):
    return full_response(run_full_calculation(body))


@router.post("/it-load", response_model=ToolResponse)
def calc_it_load(body: ITLoadRequest):
    i = body.it
    m = it_load.compute_it_load(input_mode=i.input_mode, rack_count=i.rack_count, kw_per_rack=i.kw_per_rack,
                                power_factor=i.power_factor, utilization_pct=i.utilization_pct, devices=i.devices)
    return tool_response({"it": m}, W.sort_warnings(W.it_warnings(m)))


@router.post("/power-factor", response_model=ToolResponse, summary="kW <-> kVA conversion")
def calc_power_factor(body: PowerConversionRequest):
    m = electrical.compute_power_conversion(kw=body.kw, kva=body.kva, power_factor=body.power_factor)
    return tool_response({"power_factor": m}, [])


@router.post("/convert", response_model=ToolResponse, summary="Unit conversion")
def calc_convert(body: ConvertRequest):
    m = units.convert(body.conversion, body.value, voltage=body.voltage, phase=body.phase,
                      power_factor=body.power_factor)
    return tool_response({"convert": m}, [])


@router.post("/cooling", response_model=ToolResponse)
def calc_cooling(body: CoolingRequest):
    m = cooling.compute_cooling(it_kw=body.it_kw, rack_count=body.rack_count,
                                liquid_capture_pct=body.liquid_capture_pct,
                                coolant_flow_lpm_per_kw=body.coolant_flow_lpm_per_kw)
    return tool_response({"cooling": m}, W.sort_warnings(W.cooling_warnings(m)))


@router.post("/circuit", response_model=ToolResponse)
def calc_circuit(body: CircuitRequest):
    v, a, ph, derate, name = resolve_circuit(ElectricalInputs(
        receptacle_id=body.receptacle_id, voltage=body.voltage, current=body.current, phase=body.phase,
        continuous_derate=body.continuous_derate))
    m = electrical.compute_circuit(voltage=v, current=a, phase=ph, continuous_factor=derate, rack_kw=body.rack_kw,
                                   power_factor=body.power_factor, circuits_per_rack=body.circuits_per_rack,
                                   receptacle_name=name)
    return tool_response({"circuit": m}, W.sort_warnings(W.circuit_warnings(m)))


@router.post("/pdu", response_model=ToolResponse)
def calc_pdu(body: PDURequest):
    p = body.pdu
    m = pdu.compute_pdu(rack_kw=body.rack_kw, power_factor=body.power_factor, growth_margin_pct=p.growth_margin_pct,
                        voltage=p.voltage, amperage=p.amperage, phase=p.phase, continuous_factor=p.continuous_derate,
                        feed=p.feed)
    return tool_response({"pdu": m}, W.sort_warnings(W.pdu_warnings(m)))


@router.post("/ups", response_model=ToolResponse)
def calc_ups(body: UPSRequest):
    u = body.ups
    mods = {"ups": ups.compute_ups(load_kw=body.load_kw, power_factor=body.power_factor,
                                   target_load_pct=u.target_load_pct, redundancy=u.redundancy,
                                   modules_n=u.modules_n, module_kva=u.module_kva)}
    ws = W.ups_warnings(mods["ups"])
    b = u.battery
    if b.enabled:
        mods["battery"] = ups.compute_battery(
            load_kw=body.load_kw, chemistry=b.chemistry, nominal_voltage=b.nominal_voltage,
            capacity_kwh=b.capacity_kwh, capacity_ah=b.capacity_ah, discharge_efficiency=b.discharge_efficiency,
            degradation_pct=b.degradation_pct, runtime_target_min=b.runtime_target_min)
        ws += W.battery_warnings(mods["battery"])
    return tool_response(mods, W.sort_warnings(ws))


@router.post("/transformer", response_model=ToolResponse)
def calc_transformer(body: TransformerRequest):
    t = body.transformer
    required_kva = electrical.kva_from_kw(body.required_kw, body.power_factor)
    m = transformer.compute_transformer(
        required_kva=required_kva, primary_voltage=t.primary_voltage_v, secondary_voltage=t.secondary_voltage_v,
        kva_rating=t.kva_rating, efficiency=t.efficiency, impedance_pct=t.impedance_pct, quantity=t.quantity,
        redundancy=t.redundancy, target_utilization_pct=t.target_utilization_pct)
    m.add("required_kw", "Load (real power)", body.required_kw, "kW", "Input", str(body.required_kw))
    return tool_response({"transformer": m}, W.sort_warnings(W.transformer_warnings(m, t.target_utilization_pct)))


@router.post("/generator", response_model=ToolResponse)
def calc_generator(body: GeneratorRequest):
    g = body.generator
    m = generator.compute_generator(
        critical_load_kw=body.load_kw, load_basis="custom", load_basis_note="Load entered in the generator tool.",
        unit_kw=g.unit_kw, unit_kva=g.unit_kva, power_factor=g.power_factor, quantity=g.quantity,
        redundancy=g.redundancy, step_load_pct=g.step_load_pct, target_loading_pct=g.target_loading_pct,
        derate_factor=body.derate_factor)
    return tool_response({"generator": m}, W.sort_warnings(W.generator_warnings(m, g.target_loading_pct)))


@router.post("/bess", response_model=ToolResponse)
def calc_bess(body: BESSRequest):
    b = body.bess
    m = bess.compute_bess(
        power_mw=body.power_mw, power_basis_note="Power entered in the BESS tool.", duration_min=b.duration_min,
        dc_bus_voltage=b.dc_bus_voltage, pcs_efficiency=b.pcs_efficiency, battery_efficiency=b.battery_efficiency,
        depth_of_discharge=b.depth_of_discharge, eol_capacity_factor=b.eol_capacity_factor, redundancy=b.redundancy,
        container_power_mw=b.container_power_mw, container_energy_mwh=b.container_energy_mwh)
    return tool_response({"bess": m}, W.sort_warnings(W.bess_warnings(m)))


@router.post("/rack-density", response_model=ToolResponse)
def calc_rack_density(body: RackDensityRequest):
    mods = rack_density.compute_rack_density(
        rack_count=body.rack_count, kw_per_rack=body.kw_per_rack, area_value=body.room_area,
        area_unit=body.room_area_unit, voltage=body.voltage, current=body.current, phase=body.phase,
        continuous_factor=body.continuous_derate, power_factor=body.power_factor)
    ws = W.cooling_warnings(mods["cooling"]) + W.circuit_warnings(mods["circuit"])
    if "space" in mods:
        ws += W.density_warnings(mods["space"])
    return tool_response(mods, W.sort_warnings(ws))


@router.post("/rack-count", response_model=ToolResponse)
def calc_rack_count(body: RackCountRequest):
    m = rack_count.compute_rack_count(it_kw=body.it_kw, rack_power_kw=body.rack_power_kw,
                                      racks_planned=body.racks_planned)
    return tool_response({"rack_count": m}, W.sort_warnings(W.rack_warnings(m)))


@router.post("/ai-rack", response_model=FullResponse, summary="AI / GPU cluster calculation")
def calc_ai_rack(body: AIRackRequest):
    return full_response(compute_ai_cluster(body))
