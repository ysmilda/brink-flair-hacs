"""Tests for the switch platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .platform_setup import async_setup_brink_flair


async def test_setup_registers_switches(hass: HomeAssistant) -> None:
    """The bypass boost switch and the optimistic standby mirror exist."""
    _ = await async_setup_brink_flair(hass)

    boost = hass.states.get("switch.flair_300_bypass_boost")
    assert boost is not None
    assert boost.state == "off"

    # Standby is optimistic and never read back, so it starts unknown.
    standby = hass.states.get("switch.flair_300_standby")
    assert standby is not None
    assert standby.state == "unknown"


async def test_bypass_boost_toggle_writes_register(hass: HomeAssistant) -> None:
    """Toggling the bypass boost writes the settings register."""
    entry, device = await async_setup_brink_flair(hass)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.flair_300_bypass_boost"},
        blocking=True,
    )
    assert device.settings.writes == [("bypass_boost", True)]

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("switch.flair_300_bypass_boost")
    assert state is not None
    assert state.state == "on"

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.flair_300_bypass_boost"},
        blocking=True,
    )
    assert device.settings.writes[-1] == ("bypass_boost", False)

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("switch.flair_300_bypass_boost")
    assert state is not None
    assert state.state == "off"


async def test_standby_toggle_is_optimistic(hass: HomeAssistant) -> None:
    """The standby switch mirrors the last request, never read back."""
    _, device = await async_setup_brink_flair(hass)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.flair_300_standby"},
        blocking=True,
    )
    assert device.standby is True
    state = hass.states.get("switch.flair_300_standby")
    assert state is not None
    assert state.state == "on"

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.flair_300_standby"},
        blocking=True,
    )
    assert device.standby is False
    state = hass.states.get("switch.flair_300_standby")
    assert state is not None
    assert state.state == "off"


async def test_bypass_boost_reads_register(hass: HomeAssistant) -> None:
    """The bypass boost switch reflects the register value on updates."""
    entry, device = await async_setup_brink_flair(hass)
    device.settings.bypass_boost = True
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("switch.flair_300_bypass_boost")
    assert state is not None
    assert state.state == "on"


async def test_bypass_boost_reads_unavailable(hass: HomeAssistant) -> None:
    """An unread register leaves the switch off."""
    entry, device = await async_setup_brink_flair(hass)
    device.settings.bypass_boost = None
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("switch.flair_300_bypass_boost")
    assert state is not None
    assert state.state == "unknown"
