"""Tests for the diagnostics report."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .platform_setup import async_setup_brink_flair


async def test_diagnostics_reports_entry_and_device(hass: HomeAssistant) -> None:
    """The diagnostics report carries the entry data and device snapshot."""
    entry, _ = await async_setup_brink_flair(hass)

    from custom_components.brink_flair.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    report = await async_get_config_entry_diagnostics(hass, entry)

    assert report["entry"]["host"] == "127.0.0.1"
    assert report["entry"]["port"] == 502
    assert report["coordinator"]["last_update_success"] is True
    assert report["device"]["info"]["device_type"] == 24
    assert report["device"]["info"]["manufacturer"] == "Brink"
    assert report["device"]["measurements"]["supply_pressure"] == 150.0
    assert report["device"]["settings"]["control_mode"] == 1
    assert report["device"]["status"]["filter_dirty"] is False
    assert report["device"]["flow_limits"] == {
        "flow_max": 300,
        "modbus_flow_rate_max": 280,
    }


def test_component_snapshot_handles_unknown_component() -> None:
    """A component without declared fields contributes no snapshot."""
    from custom_components.brink_flair.diagnostics import _component_snapshot

    assert _component_snapshot(object()) == {}
