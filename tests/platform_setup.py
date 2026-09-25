"""Shared helpers for the platform setup tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brink_flair.const import (
    CONF_UNIT_ID,
    CONNECTION_TCP,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .fake_device import FakeBrinkFlair

TCP_DATA: dict[str, Any] = {
    CONF_TYPE: CONNECTION_TCP,
    CONF_HOST: "127.0.0.1",
    CONF_PORT: DEFAULT_PORT,
    CONF_UNIT_ID: DEFAULT_UNIT_ID,
}


class MockModbusUnit:
    """Stands in for the ``ModbusUnit`` borrowed from the ``modbus`` integration."""

    def __init__(self) -> None:
        self.connection_lost_calls: list[Callable[[], None]] = []

    def on_connection_lost(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a connection-loss callback and return the unsubscribe callable."""
        self.connection_lost_calls.append(callback)
        return lambda: self.connection_lost_calls.remove(callback)


async def async_setup_brink_flair(
    hass: HomeAssistant,
    device: FakeBrinkFlair | None = None,
    enable: list[str] | None = None,
) -> tuple[MockConfigEntry, FakeBrinkFlair]:
    """Set up the integration through its real async_setup_entry path.

    Pass unique-id suffixes in ``enable`` to opt entities in that are disabled by
    default. They are pre-registered before setup, because reloading afterwards
    would run outside this helper's patches and open a real Modbus socket.
    """
    device = device or FakeBrinkFlair()
    entry = MockConfigEntry(
        domain=DOMAIN, data=TCP_DATA, unique_id="tcp-127.0.0.1-502_20"
    )
    entry.add_to_hass(hass)
    if enable:
        registry = er.async_get(hass)
        for key in enable:
            registry.async_get_or_create(
                "sensor", "brink_flair", f"{entry.entry_id}_{key}", config_entry=entry
            )
    with (
        patch(
            "custom_components.brink_flair.async_get_unit",
            return_value=MockModbusUnit(),
        ),
        patch(
            "custom_components.brink_flair.BrinkFlair",
            return_value=device,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
    return entry, device
