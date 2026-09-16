"""Diagnostics support for the Brink Flair integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import BrinkCoordinator

# Nothing in the connection settings is secret enough to redact, but the
# pattern is kept so future sensitive fields are not accidentally exported.
_TO_REDACT: set[str] = set()


def _component_snapshot(component: object) -> dict[str, Any]:
    """Return the decoded register values of a library component."""
    declared = getattr(component, "declared_fields", None)
    if declared is None:
        return {}
    return {
        name: getattr(component, name) for name in declared if hasattr(component, name)
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry[BrinkCoordinator]
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = config_entry.runtime_data
    device = coordinator.device
    return {
        "entry": async_redact_data(config_entry.data, _TO_REDACT),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": repr(coordinator.last_exception),
        },
        "device": {
            "info": _component_snapshot(device.info),
            "measurements": _component_snapshot(device.measurements),
            "settings": _component_snapshot(device.settings),
            "status": _component_snapshot(device.status),
            "flow_limits": vars(device.flow_limits),
        },
    }
