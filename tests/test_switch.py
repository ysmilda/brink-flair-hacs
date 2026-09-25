"""Tests for the switch platform."""

from __future__ import annotations

from custom_components.brink_flair.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory

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


async def test_setup_registers_config_switches(hass: HomeAssistant) -> None:
    """The boolean settings are writable CONFIG switches."""
    _ = await async_setup_brink_flair(hass)

    imbalance = hass.states.get("switch.flair_300_imbalance_allowed")
    assert imbalance is not None
    assert imbalance.state == "on"

    input_1 = hass.states.get("switch.flair_300_digital_input_1_normally_closed")
    assert input_1 is not None
    assert input_1.state == "on"

    input_2 = hass.states.get("switch.flair_300_digital_input_2_normally_closed")
    assert input_2 is not None
    assert input_2.state == "off"

    assert hass.states.get("switch.flair_300_display_acts_as_switch") is not None
    assert hass.states.get("switch.flair_300_humidity_sensor_mode") is not None
    assert hass.states.get("switch.flair_300_co2_sensor_mode") is not None
    assert hass.states.get("switch.flair_300_cv_exhaust_connected") is not None
    assert hass.states.get("switch.flair_300_analogue_input_1_enabled") is not None
    assert hass.states.get("switch.flair_300_analogue_input_2_enabled") is not None
    assert hass.states.get("switch.flair_300_geo_heat_exchanger") is not None


async def test_config_switches_are_config_category(hass: HomeAssistant) -> None:
    """Every settings switch is a CONFIG entity, not diagnostic."""
    entry, _ = await async_setup_brink_flair(hass)

    registry = er.async_get(hass)
    for unique_id in (
        "settings_bypass_boost",
        "settings_display_as_switch",
        "settings_cv_connected",
        "settings_geo_exchanger",
    ):
        entity_id = registry.async_get_entity_id(
            "switch", DOMAIN, f"{entry.entry_id}_{unique_id}"
        )
        assert entity_id is not None, unique_id
        assert registry.async_get(entity_id).entity_category is EntityCategory.CONFIG


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
