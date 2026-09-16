"""Tests for the Brink Flair data update coordinator."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from modbus_connection import ModbusError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brink_flair.const import (
    CONF_UNIT_ID,
    CONNECTION_TCP,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
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
