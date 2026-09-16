"""Tests for setting up the Brink Flair integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brink_flair import PLATFORMS
from custom_components.brink_flair.const import (
    CONF_UNIT_ID,
    CONNECTION_TCP,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant

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


async def test_setup_entry_and_unload(hass: HomeAssistant) -> None:
    """async_setup_entry borrows a unit and async_unload_entry undoes the setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TCP_DATA,
        unique_id="tcp-127.0.0.1-502_20",
    )
    entry.add_to_hass(hass)

    unit = MockModbusUnit()
    coordinator = AsyncMock()

    with (
        patch(
            "custom_components.brink_flair.async_get_unit",
            return_value=unit,
        ) as mock_get_unit,
        patch(
            "custom_components.brink_flair.BrinkFlair",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.brink_flair.BrinkCoordinator",
            return_value=coordinator,
        ) as mock_coordinator_cls,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(),
        ) as mock_forward_setups,
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new=AsyncMock(return_value=True),
        ) as mock_unload_platforms,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)

        assert mock_get_unit.call_count == 1
        mock_coordinator_cls.assert_called_once()
        coordinator.async_config_entry_first_refresh.assert_awaited_once()
        assert entry.runtime_data is coordinator
        assert len(unit.connection_lost_calls) == 1
        mock_forward_setups.assert_awaited_once_with(entry, PLATFORMS)

        assert await hass.config_entries.async_unload(entry.entry_id)
        mock_unload_platforms.assert_awaited_with(entry, PLATFORMS)


async def test_connection_loss_schedules_reload(hass: HomeAssistant) -> None:
    """A dropped modbus link triggers a config entry reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TCP_DATA,
        unique_id="tcp-127.0.0.1-502_20",
    )
    entry.add_to_hass(hass)

    unit = MockModbusUnit()
    coordinator = AsyncMock()

    with (
        patch(
            "custom_components.brink_flair.async_get_unit",
            return_value=unit,
        ),
        patch(
            "custom_components.brink_flair.BrinkFlair",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.brink_flair.BrinkCoordinator",
            return_value=coordinator,
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)

    assert len(unit.connection_lost_calls) == 1
    on_connection_lost = unit.connection_lost_calls[0]
    with patch.object(
        hass.config_entries,
        "async_schedule_reload",
    ) as mock_schedule_reload:
        on_connection_lost()
    mock_schedule_reload.assert_called_once_with(entry.entry_id)
