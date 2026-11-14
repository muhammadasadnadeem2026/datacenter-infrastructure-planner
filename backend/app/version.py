"""Calculation engine version.

Every saved calculation stores this value. Bump it whenever a formula, constant,
threshold or default assumption changes, so that stored engineering studies can be
traced to the engine that produced them.

Versioning policy (semver):
  MAJOR - a formula or constant change that alters numeric results
  MINOR - new modules / new outputs, existing results unchanged
  PATCH - text, labels, warnings wording
"""

CALC_ENGINE_VERSION = "1.0.0"
APP_NAME = "HallPlan"
