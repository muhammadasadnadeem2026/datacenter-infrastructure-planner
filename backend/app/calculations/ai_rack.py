"""AI / GPU cluster tool: composes the full engine for a cluster of identical racks.

The engine only consumes the selected rack power value, never vendor identity.
"""

from __future__ import annotations

from app.calculations.full import FullCalculation, run_full_calculation
from app.schemas.inputs import (
    AIRackRequest,
    FacilityInputs,
    FinancialInputs,
    ITInputs,
    ProjectInputs,
    RackInputs,
    SpaceInputs,
)


def build_ai_project(req: AIRackRequest) -> ProjectInputs:
    return ProjectInputs(
        mode="standard",
        preset="ai_cluster",
        it=ITInputs(rack_count=req.rack_count, kw_per_rack=req.rack_power_kw, power_factor=req.power_factor),
        rack=RackInputs(rack_rating_kw=req.rack_power_kw),
        space=SpaceInputs(room_area=req.room_area, room_area_unit=req.room_area_unit),
        electrical=req.electrical,
        pdu=req.pdu,
        ups=req.ups,
        facility=FacilityInputs(pue=req.pue),
        financial=FinancialInputs(electricity_rate=req.electricity_rate),
    )


def compute_ai_cluster(req: AIRackRequest) -> FullCalculation:
    return run_full_calculation(build_ai_project(req))
