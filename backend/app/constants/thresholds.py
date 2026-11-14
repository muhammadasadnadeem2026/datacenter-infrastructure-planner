"""Engineering check thresholds used by the centralized warning engine.

These are configurable planning thresholds, not code requirements. Where a value is
commonly associated with a standard, the reference id points to references.json;
the user must verify the provision against the edition adopted for the project.
"""

# Branch circuits (continuous-load check)
CIRCUIT_CAUTION_PCT = 70.0
CIRCUIT_CRITICAL_PCT = 80.0
DEFAULT_CONTINUOUS_LOAD_FACTOR = 0.80

# Capacity balance status bands (loading of usable, post-redundancy capacity)
CAPACITY_CAUTION_PCT = 80.0
CAPACITY_CRITICAL_PCT = 100.0

# Power factor
PF_REVIEW_BELOW = 0.90

# PUE plausibility
PUE_REALISTIC_MIN = 1.05
PUE_HIGH = 2.0

# Density
LIQUID_COOLING_KW_PER_RACK = 50.0
HIGH_AREA_DENSITY_W_PER_FT2 = 300.0

# BESS DC architecture
BESS_DC_CURRENT_HIGH_A = 10_000.0

# Environment
ALTITUDE_DERATE_REVIEW_M = 1000.0

# Numeric tolerance for boundary comparisons (e.g. exactly 80 % loading)
COMPARE_DECIMALS = 6
