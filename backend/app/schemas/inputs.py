"""Unified project input model and tool request models.

All numbers are validated server-side: finite (no NaN / Infinity), within physical
ranges, and consistent across fields. The frontend Zod schema mirrors these rules but
is never trusted.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.validation.validators import check_redundancy_quantity

Redundancy = Literal["N", "N+1", "2N"]
Phase = Literal["single", "three"]
Mode = Literal["quick", "standard", "engineering"]
AreaUnit = Literal["ft2", "m2"]
TempUnit = Literal["C", "F"]
LengthUnit = Literal["m", "ft"]
EquipmentType = Literal[
    "CPU Server", "GPU Server", "Storage", "Network Switch", "Router", "Firewall", "Rack PDU", "Other"
]


class Strict(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class Device(Strict):
    id: str | None = Field(default=None, max_length=64)
    equipment_type: EquipmentType = "CPU Server"
    description: str = Field(default="", max_length=200)
    quantity: int = Field(ge=0, le=100_000)
    nameplate_w: float = Field(ge=0, le=500_000)
    utilization_pct: float = Field(ge=0, le=100)
    rack: str = Field(default="", max_length=64)


class ITInputs(Strict):
    input_mode: Literal["rack_average", "device_list"] = "rack_average"
    rack_count: int = Field(ge=1, le=100_000)
    kw_per_rack: float = Field(gt=0, le=2_000)
    power_factor: float = Field(gt=0, le=1)
    utilization_pct: float = Field(default=100, gt=0, le=100)
    devices: list[Device] = Field(default_factory=list, max_length=5_000)

    @model_validator(mode="after")
    def _devices_required(self) -> ITInputs:
        if self.input_mode == "device_list":
            total = sum(d.quantity * d.nameplate_w * d.utilization_pct for d in self.devices)
            if not self.devices or total <= 0:
                raise ValueError("device list mode requires at least one device with non-zero power")
        return self


class RackInputs(Strict):
    rack_rating_kw: float = Field(gt=0, le=2_000, description="Provisioned power capacity per rack")


class SpaceInputs(Strict):
    room_area: float | None = Field(default=None, gt=0, le=10_000_000)
    room_area_unit: AreaUnit = "ft2"


class ElectricalInputs(Strict):
    receptacle_id: str = Field(default="custom", max_length=64)
    voltage: float = Field(gt=0, le=1_000)
    current: float = Field(gt=0, le=1_000)
    phase: Phase = "single"
    continuous_derate: float = Field(default=0.8, gt=0, le=1)
    circuits_per_rack: int = Field(default=0, ge=0, le=64, description="Existing circuits; 0 = not specified")


class PDUInputs(Strict):
    voltage: float = Field(gt=0, le=1_000)
    amperage: float = Field(gt=0, le=1_000)
    phase: Phase = "three"
    continuous_derate: float = Field(default=0.8, gt=0, le=1)
    growth_margin_pct: float = Field(default=20, ge=0, le=500)
    feed: Literal["none", "ab"] = "ab"


class BatteryInputs(Strict):
    enabled: bool = False
    chemistry: Literal["vrla", "li_ion", "nicd", "other"] = "li_ion"
    nominal_voltage: float = Field(default=480, gt=0, le=2_000)
    capacity_kwh: float = Field(default=0, ge=0, le=1_000_000)
    capacity_ah: float = Field(default=0, ge=0, le=1_000_000)
    discharge_efficiency: float = Field(default=0.95, gt=0, le=1)
    degradation_pct: float = Field(default=20, ge=0, lt=100)
    runtime_target_min: float = Field(default=5, gt=0, le=1_440)

    @model_validator(mode="after")
    def _capacity(self) -> BatteryInputs:
        if self.enabled and self.capacity_kwh <= 0 and self.capacity_ah <= 0:
            raise ValueError("battery module requires capacity in kWh or Ah")
        return self


class UPSInputs(Strict):
    target_load_pct: float = Field(default=80, gt=0, le=100)
    redundancy: Redundancy = "N+1"
    modules_n: int = Field(default=2, ge=1, le=64)
    module_kva: float = Field(default=0, ge=0, le=100_000, description="0 = auto-size modules")
    battery: BatteryInputs = Field(default_factory=BatteryInputs)


class CoolingInputs(Strict):
    unit_capacity_kw: float = Field(default=0, ge=0, le=100_000, description="0 = not configured")
    unit_count: int = Field(default=0, ge=0, le=1_000)
    redundancy: Redundancy = "N+1"
    liquid_capture_pct: float = Field(default=0, ge=0, le=100, description="Share of heat captured by liquid")
    coolant_flow_lpm_per_kw: float = Field(default=0, ge=0, le=10, description="TCS flow per kW of IT; 0 = n/a")

    @model_validator(mode="after")
    def _qty(self) -> CoolingInputs:
        if self.unit_count > 0:
            check_redundancy_quantity("cooling", self.redundancy, self.unit_count)
        return self


class FacilityInputs(Strict):
    pue: float = Field(ge=1, le=5)
    cooling_share_pct: float | None = Field(default=None, ge=0, le=100)
    electrical_loss_share_pct: float | None = Field(default=None, ge=0, le=100)
    other_share_pct: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def _shares(self) -> FacilityInputs:
        total = sum(v or 0 for v in (self.cooling_share_pct, self.electrical_loss_share_pct, self.other_share_pct))
        if total > 100 + 1e-9:
            raise ValueError("overhead shares (cooling + electrical losses + other) cannot exceed 100 %")
        return self


class EnvironmentInputs(Strict):
    ambient_temp: float = Field(default=24, ge=-60, le=140)
    ambient_temp_unit: TempUnit = "C"
    altitude: float = Field(default=0, ge=-500, le=30_000)
    altitude_unit: LengthUnit = "m"
    ashrae_class: Literal["A1", "A2", "A3", "A4"] = "A1"
    humidity_pct: float | None = Field(default=None, ge=0, le=100)
    temperature_derate_factor: float = Field(default=1.0, gt=0, le=1)
    altitude_derate_factor: float = Field(default=1.0, gt=0, le=1)
    apply_derating: bool = False


class UtilityInputs(Strict):
    service_voltage_v: float = Field(default=13_800, gt=0, le=1_000_000)
    service_capacity_kva: float = Field(default=0, ge=0, le=10_000_000, description="0 = not configured")


class TransformerInputs(Strict):
    enabled: bool = True
    primary_voltage_v: float = Field(default=13_800, gt=0, le=1_000_000)
    secondary_voltage_v: float = Field(default=480, gt=0, le=1_000_000)
    kva_rating: float = Field(default=2_500, gt=0, le=1_000_000)
    efficiency: float = Field(default=0.985, gt=0, le=1)
    impedance_pct: float = Field(default=5.75, gt=0, le=100)
    quantity: int = Field(default=2, ge=1, le=500)
    redundancy: Redundancy = "N+1"
    target_utilization_pct: float = Field(default=80, gt=0, le=100)

    @model_validator(mode="after")
    def _qty(self) -> TransformerInputs:
        check_redundancy_quantity("transformer", self.redundancy, self.quantity)
        return self


class GeneratorInputs(Strict):
    enabled: bool = True
    unit_kw: float = Field(default=2_000, gt=0, le=100_000)
    unit_kva: float = Field(default=2_500, gt=0, le=125_000)
    power_factor: float = Field(default=0.8, gt=0, le=1)
    quantity: int = Field(default=2, ge=1, le=500)
    redundancy: Redundancy = "N+1"
    step_load_pct: float = Field(default=50, gt=0, le=100)
    target_loading_pct: float = Field(default=80, gt=0, le=100)
    load_basis: Literal["it_only", "it_cooling", "full", "custom"] = "full"
    custom_load_kw: float = Field(default=0, ge=0, le=10_000_000)

    @model_validator(mode="after")
    def _check(self) -> GeneratorInputs:
        check_redundancy_quantity("generator", self.redundancy, self.quantity)
        if self.load_basis == "custom" and self.custom_load_kw <= 0:
            raise ValueError("custom generator load basis requires custom_load_kw > 0")
        return self


class BESSInputs(Strict):
    enabled: bool = False
    power_basis: Literal["custom", "it", "facility"] = "facility"
    custom_power_mw: float = Field(default=1, gt=0, le=10_000)
    duration_min: float = Field(default=15, gt=0, le=10_080)
    dc_bus_voltage: float = Field(default=1_000, gt=0, le=5_000)
    pcs_efficiency: float = Field(default=0.97, gt=0, le=1)
    battery_efficiency: float = Field(default=0.95, gt=0, le=1)
    depth_of_discharge: float = Field(default=0.9, gt=0, le=1)
    eol_capacity_factor: float = Field(default=0.8, gt=0, le=1)
    redundancy: Literal["N", "N+1"] = "N"
    container_power_mw: float = Field(default=2, gt=0, le=1_000)
    container_energy_mwh: float = Field(default=4, gt=0, le=10_000)


class FinancialInputs(Strict):
    electricity_rate: float = Field(default=0.13, ge=0, le=100)
    demand_charge: float = Field(default=0, ge=0, le=10_000, description="$/kW-month")
    currency: str = Field(default="USD", min_length=1, max_length=8)


class AdvancedInputs(Strict):
    hours_per_year: float = Field(default=8760, gt=0, le=8784)
    facility_power_factor: float | None = Field(default=None, gt=0, le=1)


class ProjectInputs(Strict):
    mode: Mode = "standard"
    unit_system: Literal["imperial", "metric"] = "imperial"
    preset: str = Field(default="custom", max_length=64)
    it: ITInputs
    rack: RackInputs
    space: SpaceInputs = Field(default_factory=SpaceInputs)
    electrical: ElectricalInputs
    pdu: PDUInputs
    ups: UPSInputs = Field(default_factory=UPSInputs)
    cooling: CoolingInputs = Field(default_factory=CoolingInputs)
    facility: FacilityInputs
    environment: EnvironmentInputs = Field(default_factory=EnvironmentInputs)
    utility: UtilityInputs = Field(default_factory=UtilityInputs)
    transformer: TransformerInputs = Field(default_factory=TransformerInputs)
    generator: GeneratorInputs = Field(default_factory=GeneratorInputs)
    bess: BESSInputs = Field(default_factory=BESSInputs)
    financial: FinancialInputs = Field(default_factory=FinancialInputs)
    advanced: AdvancedInputs = Field(default_factory=AdvancedInputs)


# ---------------------------------------------------------------- tool requests


class ITLoadRequest(Strict):
    it: ITInputs


class PowerConversionRequest(Strict):
    kw: float | None = Field(default=None, ge=0, le=10_000_000)
    kva: float | None = Field(default=None, ge=0, le=10_000_000)
    power_factor: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def _one(self) -> PowerConversionRequest:
        if (self.kw is None) == (self.kva is None):
            raise ValueError("provide exactly one of kw or kva")
        return self


class ConvertRequest(Strict):
    conversion: str = Field(max_length=32)
    value: float = Field(ge=-1e12, le=1e12)
    voltage: float | None = Field(default=None, gt=0, le=1_000_000)
    phase: Phase | None = None
    power_factor: float | None = Field(default=None, gt=0, le=1)


class CoolingRequest(Strict):
    it_kw: float = Field(gt=0, le=10_000_000)
    rack_count: int = Field(default=1, ge=1, le=100_000)
    liquid_capture_pct: float = Field(default=0, ge=0, le=100)
    coolant_flow_lpm_per_kw: float = Field(default=0, ge=0, le=10)


class CircuitRequest(Strict):
    voltage: float = Field(gt=0, le=1_000)
    current: float = Field(gt=0, le=1_000)
    phase: Phase = "single"
    continuous_derate: float = Field(default=0.8, gt=0, le=1)
    rack_kw: float = Field(gt=0, le=2_000)
    power_factor: float = Field(default=0.95, gt=0, le=1)
    circuits_per_rack: int = Field(default=0, ge=0, le=64)
    receptacle_id: str = Field(default="custom", max_length=64)


class PDURequest(Strict):
    rack_kw: float = Field(gt=0, le=2_000)
    power_factor: float = Field(default=0.95, gt=0, le=1)
    pdu: PDUInputs


class UPSRequest(Strict):
    load_kw: float = Field(gt=0, le=10_000_000)
    power_factor: float = Field(default=0.95, gt=0, le=1)
    ups: UPSInputs


class TransformerRequest(Strict):
    required_kw: float = Field(gt=0, le=10_000_000)
    power_factor: float = Field(default=0.95, gt=0, le=1)
    transformer: TransformerInputs


class GeneratorRequest(Strict):
    load_kw: float = Field(gt=0, le=10_000_000)
    generator: GeneratorInputs
    derate_factor: float = Field(default=1.0, gt=0, le=1)


class BESSRequest(Strict):
    power_mw: float = Field(gt=0, le=10_000)
    bess: BESSInputs


class RackDensityRequest(Strict):
    rack_count: int = Field(ge=1, le=100_000)
    kw_per_rack: float = Field(gt=0, le=2_000)
    room_area: float | None = Field(default=None, gt=0, le=10_000_000)
    room_area_unit: AreaUnit = "ft2"
    voltage: float = Field(default=208, gt=0, le=1_000)
    current: float = Field(default=30, gt=0, le=1_000)
    phase: Phase = "single"
    continuous_derate: float = Field(default=0.8, gt=0, le=1)
    power_factor: float = Field(default=0.95, gt=0, le=1)


class RackCountRequest(Strict):
    it_kw: float = Field(gt=0, le=100_000_000)
    rack_power_kw: float = Field(gt=0, le=2_000)
    racks_planned: int | None = Field(default=None, ge=1, le=1_000_000)


class AIRackRequest(Strict):
    rack_count: int = Field(ge=1, le=100_000)
    rack_power_kw: float = Field(gt=0, le=2_000)
    power_factor: float = Field(default=0.95, gt=0, le=1)
    pue: float = Field(default=1.25, ge=1, le=5)
    electricity_rate: float = Field(default=0.10, ge=0, le=100)
    room_area: float | None = Field(default=None, gt=0, le=10_000_000)
    room_area_unit: AreaUnit = "ft2"
    electrical: ElectricalInputs
    pdu: PDUInputs
    ups: UPSInputs = Field(default_factory=UPSInputs)


class ReportRequest(Strict):
    project_name: str = Field(default="Untitled project", min_length=1, max_length=200)
    inputs: ProjectInputs
