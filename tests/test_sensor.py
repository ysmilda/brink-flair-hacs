"""Tests for the sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .platform_setup import async_setup_brink_flair


def _registry_ids(hass: HomeAssistant, entry_id: str, keys: list[str]) -> set[str]:
    """Return the registered (possibly disabled) entity ids for ``keys``."""
    registry = er.async_get(hass)
    return {
        registry.async_get_entity_id("sensor", "brink_flair", f"{entry_id}_{key}")
        for key in keys
    }


async def test_setup_registers_measurement_sensors(hass: HomeAssistant) -> None:
    """The measurement sensors are created with the expected state."""
    entry, _ = await async_setup_brink_flair(hass)

    pressure = hass.states.get("sensor.flair_300_supply_pressure")
    assert pressure is not None
    assert pressure.state == "150.0"
    assert pressure.attributes["unit_of_measurement"] == "Pa"

    temperature = hass.states.get("sensor.flair_300_supply_temperature")
    assert temperature is not None
    assert temperature.state == "21.3"
    assert temperature.attributes["unit_of_measurement"] == "°C"

    humidity = hass.states.get("sensor.flair_300_supply_humidity")
    assert humidity is not None
    assert humidity.state == "44.0"

    fan = hass.states.get("sensor.flair_300_supply_fan_speed")
    assert fan is not None
    assert fan.state == "1450"
    assert fan.attributes["unit_of_measurement"] == "rpm"

    # The volume setpoints are disabled by default, so they only exist in the
    # entity registry, not in the state machine.
    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "measurements_setpoint_supply_volume",
            "measurements_setpoint_exhaust_volume",
        ],
    )
    assert None not in registered

    # The extra measurements are disabled by default too, so they only exist
    # in the entity registry, not in the state machine.
    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "measurements_supply_mass_flow",
            "measurements_supply_anemometer_rpm",
            "measurements_exhaust_mass_flow",
            "measurements_exhaust_anemometer_rpm",
            "measurements_bypass_step_position",
            "measurements_preheater_capacity",
            "measurements_dwelling_temperature",
            "measurements_rht_humidity",
            "measurements_current_operating_time",
            "measurements_total_flow",
            "measurements_current_time",
            "measurements_current_date",
        ],
    )
    assert None not in registered
    assert hass.states.get("sensor.flair_300_supply_mass_flow") is None

    assert hass.states.get("sensor.flair_300_supply_volume") is not None
    assert hass.states.get("sensor.flair_300_exhaust_volume") is not None
    assert hass.states.get("sensor.flair_300_exhaust_pressure") is not None
    assert hass.states.get("sensor.flair_300_exhaust_fan_speed") is not None
    assert hass.states.get("sensor.flair_300_exhaust_temperature") is not None
    assert hass.states.get("sensor.flair_300_exhaust_humidity") is not None
    assert hass.states.get("sensor.flair_300_outside_temperature") is not None


async def test_setup_registers_filter_sensors(hass: HomeAssistant) -> None:
    """The filter life sensors are created from the device attributes."""
    _ = await async_setup_brink_flair(hass)

    hours = hass.states.get("sensor.flair_300_filter_hours_used")
    assert hours is not None
    assert hours.state == "120.5"

    volume = hass.states.get("sensor.flair_300_filter_used_volume")
    assert volume is not None
    assert volume.state == "18000.0"

    days = hass.states.get("sensor.flair_300_filter_days_used")
    assert days is not None
    assert days.state == "5.5"

    until_change = hass.states.get("sensor.flair_300_days_until_filter_change")
    assert until_change is not None
    assert until_change.state == "25.5"


async def test_setup_registers_diagnostic_sensors(hass: HomeAssistant) -> None:
    """The diagnostic status and identity sensors are created."""
    entry, _ = await async_setup_brink_flair(hass)

    device_type = hass.states.get("sensor.flair_300_device_type")
    assert device_type is not None
    assert device_type.state == "Flair 300"

    # The version and serial number sensors are disabled by default, so they
    # only exist in the entity registry, not in the state machine.
    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "info_software_version",
            "info_hardware_version",
            "info_serial_number",
        ],
    )
    assert None not in registered
    assert hass.states.get("sensor.flair_300_software_version") is None

    mode = hass.states.get("sensor.flair_300_operating_mode")
    assert mode is not None
    assert mode.state == "auto_modbus"

    bypass = hass.states.get("sensor.flair_300_bypass_status")
    assert bypass is not None
    assert bypass.state == "closed"

    frost = hass.states.get("sensor.flair_300_frost_status")
    assert frost is not None
    assert frost.state == "no_frost"

    assert hass.states.get("sensor.flair_300_frost_heater_setpoint") is not None
    assert hass.states.get("sensor.flair_300_frost_fan_reduction") is not None
