"""Tests for the Brink Flair data update coordinator."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock

from modbus_connection import ModbusError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brink_flair.const import (
    CONF_UNIT_ID,
    CONF_UPDATE_INTERVAL,
    CONNECTION_TCP,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.brink_flair.coordinator import BrinkCoordinator
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .fake_device import FakeBrinkFlair

TCP_DATA: dict[str, Any] = {
    CONF_TYPE: CONNECTION_TCP,
    CONF_HOST: "127.0.0.1",
    CONF_PORT: DEFAULT_PORT,
    CONF_UNIT_ID: DEFAULT_UNIT_ID,
}


def _coordinator(hass: HomeAssistant, device: FakeBrinkFlair) -> BrinkCoordinator:
    entry = MockConfigEntry(
        domain=DOMAIN, data=TCP_DATA, unique_id="tcp-127.0.0.1-502_20"
    )
    entry.add_to_hass(hass)
    return BrinkCoordinator(hass, entry, device)


async def test_update_returns_device(hass: HomeAssistant) -> None:
    """A successful poll returns the device and bumps the update counter."""
    device = FakeBrinkFlair()
    coordinator = _coordinator(hass, device)

    result = await coordinator._async_update_data()

    assert result is device
    assert device.update_count == 1


async def test_update_propagates_modbus_error(hass: HomeAssistant) -> None:
    """A ModbusError on poll propagates as a translated UpdateFailed."""
    device = FakeBrinkFlair()
    device.async_update = AsyncMock(side_effect=ModbusError("link down"))
    coordinator = _coordinator(hass, device)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert exc_info.value.translation_domain == DOMAIN
    assert exc_info.value.translation_key == "communication_error"
    assert str(exc_info.value.__cause__) == "link down"


async def test_default_update_interval(hass: HomeAssistant) -> None:
    """Without options the coordinator polls at the default interval."""
    coordinator = _coordinator(hass, FakeBrinkFlair())

    assert coordinator.update_interval == timedelta(seconds=DEFAULT_UPDATE_INTERVAL)


async def test_update_interval_reads_options(hass: HomeAssistant) -> None:
    """An options-stored interval is picked up at coordinator creation."""
    device = FakeBrinkFlair()
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TCP_DATA,
        options={CONF_UPDATE_INTERVAL: 120},
        unique_id="tcp-127.0.0.1-502_20",
    )
    entry.add_to_hass(hass)
    coordinator = BrinkCoordinator(hass, entry, device)

    assert coordinator.update_interval == timedelta(seconds=120)


async def test_apply_options_adopts_new_interval(hass: HomeAssistant) -> None:
    """apply_options changes the interval without rebuilding the coordinator."""
    device = FakeBrinkFlair()
    entry = MockConfigEntry(
        domain=DOMAIN, data=TCP_DATA, unique_id="tcp-127.0.0.1-502_20"
    )
    entry.add_to_hass(hass)
    coordinator = BrinkCoordinator(hass, entry, device)
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_UPDATE_INTERVAL)

    hass.config_entries.async_update_entry(
        entry, options={CONF_UPDATE_INTERVAL: 60}
    )
    coordinator.apply_options()

    assert coordinator.update_interval == timedelta(seconds=60)
