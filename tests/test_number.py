"""Tests for the number platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .platform_setup import async_setup_brink_flair


async def test_setup_registers_numbers(hass: HomeAssistant) -> None:
    """The writable numbers are created from the model's flow envelope."""
    _ = await async_setup_brink_flair(hass)

    desired = hass.states.get("number.flair_300_desired_flow_rate")
    assert desired is not None
    assert desired.state == "250"
    assert desired.attributes["min"] == 0
    assert desired.attributes["max"] == 280

    step = hass.states.get("number.flair_300_flow_rate_step_0")
    assert step is not None
    assert step.state == "100"
    assert step.attributes["min"] == 0
    assert step.attributes["max"] == 300

    position = hass.states.get("number.flair_300_bypass_boost_position")
    assert position is not None
    assert position.state == "2"
    assert position.attributes["step"] == 1

    inside = hass.states.get("number.flair_300_bypass_temperature_inside")
    assert inside is not None
    assert inside.state == "20.0"
    assert inside.attributes["unit_of_measurement"] == "°C"

    assert hass.states.get("number.flair_300_intake_imbalance") is not None
    assert hass.states.get("number.flair_300_exhaust_imbalance") is not None
    assert hass.states.get("number.flair_300_bypass_temperature_outside") is not None
    assert hass.states.get("number.flair_300_bypass_hysteresis") is not None
    assert hass.states.get("number.flair_300_frost_control_temperature") is not None
    assert (
        hass.states.get("number.flair_300_frost_minimum_inlet_temperature") is not None
    )
    assert hass.states.get("number.flair_300_filter_change_days") is not None


async def test_set_value_writes_and_updates_state(hass: HomeAssistant) -> None:
    """Setting a value writes the attribute, the poll then reflects it."""
    entry, device = await async_setup_brink_flair(hass)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.flair_300_desired_flow_rate", "value": 260},
        blocking=True,
    )

    assert device.settings.writes == [("desired_flow_rate", 260.0)]

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("number.flair_300_desired_flow_rate")
    assert state is not None
    assert state.state == "260.0"
