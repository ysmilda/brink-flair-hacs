"""Tests for the button platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .platform_setup import async_setup_brink_flair


async def test_setup_registers_reset_filter_button(hass: HomeAssistant) -> None:
    """The filter reset button is created."""
    _ = await async_setup_brink_flair(hass)

    state = hass.states.get("button.flair_300_filter_reset")
    assert state is not None


async def test_press_resets_filter(hass: HomeAssistant) -> None:
    """Pressing the button pulses the filter-reset on the unit."""
    device = (await async_setup_brink_flair(hass))[1]
    assert device.filter_resets == 0

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.flair_300_filter_reset"},
        blocking=True,
    )

    assert device.filter_resets == 1
