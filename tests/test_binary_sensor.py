"""Tests for the binary sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .platform_setup import async_setup_brink_flair


async def test_clean_filter_off(hass: HomeAssistant) -> None:
    """A clean filter reports the problem binary sensor off."""
    _ = await async_setup_brink_flair(hass)

    state = hass.states.get("binary_sensor.flair_300_filter_dirty")
    assert state is not None
    assert state.state == "off"


async def test_dirty_filter_on(hass: HomeAssistant) -> None:
    """An expired counter turns the problem binary sensor on."""
    entry, device = await async_setup_brink_flair(hass)
    device.status.filter_dirty = True
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.flair_300_filter_dirty")
    assert state is not None
    assert state.state == "on"


async def test_unknown_filter_state(hass: HomeAssistant) -> None:
    """An unread counter reports an unknown binary sensor."""
    entry, device = await async_setup_brink_flair(hass)
    device.status.filter_dirty = None
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.flair_300_filter_dirty")
    assert state is not None
    assert state.state == "unknown"
