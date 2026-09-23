"""Tests for the select platform."""

from __future__ import annotations

from brink_flair_modbus import BypassMode, ControlMode
from modbus_connection import ModbusError
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .platform_setup import async_setup_brink_flair


async def test_setup_registers_selects(hass: HomeAssistant) -> None:
    """The mode selects are created with the current enum value."""
    _ = await async_setup_brink_flair(hass)

    control = hass.states.get("select.flair_300_control_mode")
    assert control is not None
    assert control.state == "step"

    level = hass.states.get("select.flair_300_ventilation_level")
    assert level is not None
    assert level.state == "medium"

    bypass = hass.states.get("select.flair_300_bypass_mode")
    assert bypass is not None
    assert bypass.state == "auto"


async def test_select_option_writes_enum(hass: HomeAssistant) -> None:
    """Selecting an option writes the matching enum member to the unit."""
    entry, device = await async_setup_brink_flair(hass)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.flair_300_control_mode", "option": "flow"},
        blocking=True,
    )

    assert device.settings.writes == [("control_mode", ControlMode.FLOW)]

    # The option is already visible before the unit confirms it.
    state = hass.states.get("select.flair_300_control_mode")
    assert state is not None
    assert state.state == "flow"

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("select.flair_300_control_mode")
    assert state is not None
    assert state.state == "flow"


async def test_bypass_override_blocks_high_supply(hass: HomeAssistant) -> None:
    """A forced bypass is refused while the supply volume is high."""
    _, device = await async_setup_brink_flair(hass)
    device.measurements.supply_volume = 260.0

    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.flair_300_bypass_mode", "option": "open"},
            blocking=True,
        )

    assert exc_info.value.translation_domain == "brink_flair"
    assert exc_info.value.translation_key == "bypass_override_blocked"
    assert exc_info.value.translation_placeholders == {"supply_volume": "260.0"}
    assert device.settings.writes == []


async def test_bypass_override_allows_low_supply(hass: HomeAssistant) -> None:
    """The guard stays silent below the threshold."""
    entry, device = await async_setup_brink_flair(hass)
    device.measurements.supply_volume = 150.0

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.flair_300_bypass_mode", "option": "closed"},
        blocking=True,
    )

    assert device.settings.writes == [("bypass_mode", BypassMode.CLOSED)]

    state = hass.states.get("select.flair_300_bypass_mode")
    assert state is not None
    assert state.state == "closed"

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("select.flair_300_bypass_mode")
    assert state is not None
    assert state.state == "closed"


async def test_bypass_override_allows_unknown_supply(hass: HomeAssistant) -> None:
    """The guard stays silent when the unit reports no supply volume."""
    entry, device = await async_setup_brink_flair(hass)
    device.measurements.supply_volume = None

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.flair_300_bypass_mode", "option": "closed"},
        blocking=True,
    )

    assert device.settings.writes == [("bypass_mode", BypassMode.CLOSED)]

    state = hass.states.get("select.flair_300_bypass_mode")
    assert state is not None
    assert state.state == "closed"

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("select.flair_300_bypass_mode")
    assert state is not None
    assert state.state == "closed"


async def test_select_reflects_updated_option(hass: HomeAssistant) -> None:
    """A coordinator update re-reads the option into the state machine."""
    entry, device = await async_setup_brink_flair(hass)
    device.settings.control_mode = ControlMode.OFF
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("select.flair_300_control_mode")
    assert state is not None
    assert state.state == "off"


async def test_select_unknown_option(hass: HomeAssistant) -> None:
    """An unread enum value reports state unknown."""
    entry, device = await async_setup_brink_flair(hass)
    device.settings.control_mode = None
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("select.flair_300_control_mode")
    assert state is not None
    assert state.state == "unknown"


async def test_select_rolls_back_on_write_failure(hass: HomeAssistant) -> None:
    """A failed write restores the previous option instead of the guessed one."""
    entry, device = await async_setup_brink_flair(hass)
    device.settings.fail_writes = True

    with pytest.raises(ModbusError):
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.flair_300_control_mode", "option": "flow"},
            blocking=True,
        )

    state = hass.states.get("select.flair_300_control_mode")
    assert state is not None
    assert state.state == "step"

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("select.flair_300_control_mode")
    assert state is not None
    assert state.state == "step"
