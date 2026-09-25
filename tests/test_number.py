"""Tests for the number platform."""

from __future__ import annotations

from modbus_connection import ModbusError
import pytest

from custom_components.brink_flair.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory

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


async def test_setup_registers_config_numbers(hass: HomeAssistant) -> None:
    """The PWM, CO2, analogue and geo settings are writable CONFIG numbers."""
    _ = await async_setup_brink_flair(hass)

    pwm = hass.states.get("number.flair_300_inlet_fan_pwm_step_0")
    assert pwm is not None
    assert pwm.state == "50"
    assert pwm.attributes["min"] == 15
    assert pwm.attributes["max"] == 100
    assert pwm.attributes["unit_of_measurement"] == "%"

    exhaust = hass.states.get("number.flair_300_exhaust_fan_pwm_step_3")
    assert exhaust is not None
    assert exhaust.state == "95"

    co2_low = hass.states.get("number.flair_300_co2_sensor_1_low_level")
    assert co2_low is not None
    assert co2_low.state == "800"
    assert co2_low.attributes["unit_of_measurement"] == "ppm"
    assert co2_low.attributes["min"] == 400
    co2_high = hass.states.get("number.flair_300_co2_sensor_4_high_level")
    assert co2_high is not None
    assert co2_high.state == "1200"

    voltage = hass.states.get("number.flair_300_analogue_input_1_maximum_voltage")
    assert voltage is not None
    assert voltage.state == "10.0"
    assert voltage.attributes["unit_of_measurement"] == "V"
    assert voltage.attributes["device_class"] == "voltage"

    postheater = hass.states.get("number.flair_300_post_heater_setpoint")
    assert postheater is not None
    assert postheater.state == "20.0"
    assert postheater.attributes["device_class"] == "temperature"

    assert hass.states.get("number.flair_300_imbalance_percentage") is not None
    assert hass.states.get("number.flair_300_humidity_sensor_sensitivity") is not None
    assert hass.states.get("number.flair_300_switch_default_position") is not None
    assert hass.states.get("number.flair_300_geo_minimum_temperature") is not None
    assert hass.states.get("number.flair_300_geo_maximum_temperature") is not None


async def test_config_number_is_config_category(hass: HomeAssistant) -> None:
    """Every writable settings number is a CONFIG entity, not diagnostic."""
    entry, _ = await async_setup_brink_flair(hass)

    registry = er.async_get(hass)
    for unique_id in (
        "settings_flow_0",
        "settings_pwm_inlet_0",
        "settings_co2_1_low_level",
        "settings_analogue_input_1_vmin",
        "settings_postheater_setpoint",
    ):
        entity_id = registry.async_get_entity_id(
            "number", DOMAIN, f"{entry.entry_id}_{unique_id}"
        )
        assert entity_id is not None, unique_id
        assert registry.async_get(entity_id).entity_category is EntityCategory.CONFIG


async def test_config_number_write_reaches_device(hass: HomeAssistant) -> None:
    """A moved settings number still writes through to the device."""
    _entry, device = await async_setup_brink_flair(hass)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.flair_300_co2_sensor_1_low_level", "value": 950},
        blocking=True,
    )

    assert device.settings.writes == [("co2_1_low_level", 950.0)]
    assert hass.states.get("number.flair_300_co2_sensor_1_low_level").state == "950.0"


async def test_set_value_writes_and_updates_state(hass: HomeAssistant) -> None:
    """Setting a value writes the attribute and shows it optimistically."""
    entry, device = await async_setup_brink_flair(hass)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.flair_300_desired_flow_rate", "value": 260},
        blocking=True,
    )

    assert device.settings.writes == [("desired_flow_rate", 260.0)]

    # The value is already visible before the unit confirms it.
    state = hass.states.get("number.flair_300_desired_flow_rate")
    assert state is not None
    assert state.state == "260.0"

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("number.flair_300_desired_flow_rate")
    assert state is not None
    assert state.state == "260.0"


async def test_set_value_rolls_back_on_write_failure(hass: HomeAssistant) -> None:
    """A failed write restores the previous reading instead of the guessed value."""
    entry, device = await async_setup_brink_flair(hass)
    device.settings.fail_writes = True

    with pytest.raises(ModbusError):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.flair_300_desired_flow_rate", "value": 260},
            blocking=True,
        )

    state = hass.states.get("number.flair_300_desired_flow_rate")
    assert state is not None
    assert state.state == "250"

    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()
    state = hass.states.get("number.flair_300_desired_flow_rate")
    assert state is not None
    assert state.state == "250"
