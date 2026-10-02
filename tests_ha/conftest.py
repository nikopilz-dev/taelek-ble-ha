"""Real HA config-flow tests. Run separately on Linux with the HA test plugin."""

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def _custom_integrations(enable_custom_integrations):
    yield
