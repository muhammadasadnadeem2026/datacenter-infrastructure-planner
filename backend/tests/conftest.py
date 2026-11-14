import copy
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.constants.presets import get_preset  # noqa: E402
from app.database.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import project  # noqa: E402,F401


@pytest.fixture(autouse=True)
def _db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def acceptance_inputs():
    """Spec acceptance example: 10 racks × 6 kW, PF 0.95, PUE 1.5, $0.13/kWh."""
    x = copy.deepcopy(get_preset("enterprise"))
    x["it"].update(rack_count=10, kw_per_rack=6, power_factor=0.95)
    x["facility"]["pue"] = 1.5
    x["financial"]["electricity_rate"] = 0.13
    return x
