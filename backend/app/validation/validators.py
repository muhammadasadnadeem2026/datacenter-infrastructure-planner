"""Cross-field validation helpers shared by input schemas."""

from __future__ import annotations

import math

from app.calculations.redundancy import min_installed_for


def check_redundancy_quantity(system: str, redundancy: str, quantity: int) -> None:
    minimum = min_installed_for(redundancy)
    if quantity < minimum:
        raise ValueError(f"{system}: {redundancy} redundancy requires at least {minimum} units")
    if redundancy == "2N" and quantity % 2:
        raise ValueError(f"{system}: 2N redundancy requires an even number of units")


def ensure_finite(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value
