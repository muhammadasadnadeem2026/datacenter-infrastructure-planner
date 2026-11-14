"""Traceable calculation results.

Every engineering number the application displays is a Step: the value, the formula
that produced it, the substituted calculation, its units, any assumption and a
reference id. Modules collect Steps into a ModuleResult.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from app.constants.thresholds import COMPARE_DECIMALS

Number = int | float


@dataclass(frozen=True)
class Step:
    key: str
    label: str
    value: Any
    unit: str = ""
    formula: str = ""
    substitution: str = ""
    assumption: str = ""
    reference: str = ""


@dataclass
class ModuleResult:
    module: str
    steps: dict[str, Step] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    def add(
        self,
        key: str,
        label: str,
        value: Any,
        unit: str = "",
        formula: str = "",
        substitution: str = "",
        assumption: str = "",
        reference: str = "",
    ) -> Any:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{self.module}.{key} produced a non-finite value")
        self.steps[key] = Step(key, label, value, unit, formula, substitution, assumption, reference)
        return value

    def v(self, key: str) -> Any:
        return self.steps[key].value

    def get(self, key: str, default: Any = None) -> Any:
        step = self.steps.get(key)
        return default if step is None else step.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "steps": [asdict(s) for s in self.steps.values()],
            "data": self.data,
        }


def fmt(x: Any) -> str:
    """Format a number for a human-readable substituted calculation."""
    if isinstance(x, bool) or x is None:
        return str(x)
    if isinstance(x, int):
        return f"{x:,}"
    if isinstance(x, float):
        if x.is_integer() and abs(x) < 1e15:
            return f"{int(x):,}"
        if abs(x) < 0.001:
            return f"{x:.4g}"
        return f"{x:,.4f}".rstrip("0").rstrip(".")
    return str(x)


def safe_ceil(x: float) -> int:
    """Ceiling that ignores floating-point noise (e.g. 3.0000000001 -> 3)."""
    return math.ceil(round(x, COMPARE_DECIMALS))


def cmp_round(x: float) -> float:
    return round(x, COMPARE_DECIMALS)


def require_positive(name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite number greater than zero")
