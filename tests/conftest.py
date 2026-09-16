"""Shared fixtures for the Brink Flair test suite."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow the ``hass`` fixture to load integrations from ``custom_components``."""
    yield
