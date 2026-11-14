"""Physical conversion constants. The single source of truth for every conversion."""

import math

BTU_HR_PER_KW = 3412.142
"""1 kW of heat = 3412.142 BTU/hr."""

BTU_HR_PER_TON = 12000.0
"""1 ton of refrigeration = 12,000 BTU/hr."""

HOURS_PER_YEAR = 8760
"""Non-leap year. Editable per project under Advanced Assumptions."""

MONTHS_PER_YEAR = 12

M2_PER_FT2 = 0.09290304
"""Exact: 1 ft = 0.3048 m, so 1 ft^2 = 0.09290304 m^2."""

M_PER_FT = 0.3048

KW_PER_MW = 1000.0

LPM_PER_GPM = 3.785411784
"""US gallon = 3.785411784 L (exact)."""

SQRT3 = math.sqrt(3)
