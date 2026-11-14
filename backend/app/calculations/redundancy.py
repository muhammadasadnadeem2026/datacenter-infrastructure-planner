"""Redundancy arithmetic shared by UPS, transformer, generator, cooling and BESS."""

from __future__ import annotations

from app.calculations.trace import safe_ceil

REDUNDANCY_OPTIONS = ("N", "N+1", "2N")


def redundancy_multiplier(redundancy: str, n: int) -> float:
    """Installed-to-required capacity ratio for n required units."""
    if n < 1:
        raise ValueError("n must be at least 1")
    if redundancy == "N":
        return 1.0
    if redundancy == "N+1":
        return (n + 1) / n
    if redundancy == "2N":
        return 2.0
    raise ValueError(f"unknown redundancy '{redundancy}'")


def installed_unit_count(redundancy: str, n: int) -> int:
    """Units to install when n units carry the load."""
    if redundancy == "N":
        return n
    if redundancy == "N+1":
        return n + 1
    if redundancy == "2N":
        return 2 * n
    raise ValueError(f"unknown redundancy '{redundancy}'")


def usable_units(installed: int, redundancy: str) -> int:
    """Units that may carry load while the redundant units are held in reserve."""
    if redundancy == "N":
        return installed
    if redundancy == "N+1":
        return max(installed - 1, 0)
    if redundancy == "2N":
        return installed // 2
    raise ValueError(f"unknown redundancy '{redundancy}'")


def min_installed_for(redundancy: str) -> int:
    return {"N": 1, "N+1": 2, "2N": 2}[redundancy]


def units_needed(required: float, unit_capacity: float) -> int:
    if unit_capacity <= 0:
        raise ValueError("unit capacity must be > 0")
    return max(1, safe_ceil(required / unit_capacity))
