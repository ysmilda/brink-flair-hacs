"""Tests for the sensor platform."""

from __future__ import annotations

from brink_flair_modbus import Co2SensorStatus

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .fake_device import FakeBrinkFlair
from .platform_setup import async_setup_brink_flair


def _registry_ids(hass: HomeAssistant, entry_id: str, keys: list[str]) -> set[str]:
    """Return the registered (possibly disabled) entity ids for ``keys``."""
    registry = er.async_get(hass)
    return {
        registry.async_get_entity_id("sensor", "brink_flair", f"{entry_id}_{key}")
        for key in keys
    }


def _registry_entry(
    hass: HomeAssistant, entry_id: str, key: str
) -> er.RegistryEntry | None:
    """Return the registry entry for a sensor ``key``."""
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", "brink_flair", f"{entry_id}_{key}"
    )
    if entity_id is None:
        return None
    return registry.async_get(entity_id)


async def test_setup_registers_measurement_sensors(hass: HomeAssistant) -> None:
    """The core measurement sensors are created with the expected state."""
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

    assert hass.states.get("sensor.flair_300_supply_volume") is not None
    assert hass.states.get("sensor.flair_300_exhaust_volume") is not None
    assert hass.states.get("sensor.flair_300_exhaust_pressure") is not None
    assert hass.states.get("sensor.flair_300_exhaust_fan_speed") is not None
    assert hass.states.get("sensor.flair_300_exhaust_temperature") is not None
    assert hass.states.get("sensor.flair_300_exhaust_humidity") is not None
    assert hass.states.get("sensor.flair_300_outside_temperature") is not None
    assert hass.states.get("sensor.flair_300_operating_mode") is not None

    # The volume setpoints and the advanced measurements exist only in the
    # entity registry, disabled by default.
    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "measurements_setpoint_supply_volume",
            "measurements_setpoint_exhaust_volume",
            "measurements_supply_mass_flow",
            "measurements_exhaust_mass_flow",
            "measurements_supply_anemometer_rpm",
            "measurements_exhaust_anemometer_rpm",
            "measurements_bypass_step_position",
            "measurements_preheater_capacity",
            "measurements_rht_humidity",
            "measurements_current_operating_time",
            "measurements_total_flow",
        ],
    )
    assert None not in registered

    mass_flow_entry = _registry_entry(
        hass, entry.entry_id, "measurements_supply_mass_flow"
    )
    assert mass_flow_entry is not None
    assert mass_flow_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


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
    """The diagnostic status and identity sensors are created, but disabled."""
    entry, _ = await async_setup_brink_flair(hass)

    mode = hass.states.get("sensor.flair_300_operating_mode")
    assert mode is not None
    assert mode.state == "auto_modbus"

    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "info_device_type",
            "status_bypass_status",
            "status_frost_status",
            "status_fan_control_type",
            "status_ventilation_mode",
            "status_supply_fan_status",
            "status_exhaust_fan_status",
            "status_preheater_status",
            "status_ebus_power_status",
            "status_geo_exchanger_status",
            "status_system_error",
            "status_flow_switch_position",
            "status_active_incident",
            "measurements_frost_heater_setpoint",
            "measurements_frost_fan_reduction",
        ],
    )
    assert None not in registered

    for entity_id in (
        "sensor.flair_300_device_type",
        "sensor.flair_300_bypass_status",
        "sensor.flair_300_frost_status",
        "sensor.flair_300_fan_control_type",
    ):
        assert hass.states.get(entity_id) is None


async def test_setup_registers_connected_co2_sensors(hass: HomeAssistant) -> None:
    """CO2 slots that report a connected state register disabled sensors."""
    entry, _ = await async_setup_brink_flair(hass)

    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "status_co2_1_value",
            "status_co2_1_status",
            "status_co2_2_value",
            "status_co2_2_status",
        ],
    )
    assert None not in registered

    for entity_id in (
        "sensor.flair_300_co2_sensor_1",
        "sensor.flair_300_co2_sensor_2",
    ):
        assert hass.states.get(entity_id) is None

    for key in ("status_co2_3_value", "status_co2_4_value"):
        assert _registry_entry(hass, entry.entry_id, key) is None


async def test_setup_registers_optional_sensors(hass: HomeAssistant) -> None:
    """The extension module and dwelling probe register disabled sensors."""
    entry, _ = await async_setup_brink_flair(hass)

    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "measurements_dwelling_temperature",
            "measurements_extension_temperature",
            "measurements_extension_analogue_input_1",
            "measurements_extension_analogue_input_2",
            "measurements_extension_analogue_output_1",
            "measurements_extension_analogue_output_2",
        ],
    )
    assert None not in registered

    for entity_id in (
        "sensor.flair_300_dwelling_temperature",
        "sensor.flair_300_extension_temperature",
    ):
        assert hass.states.get(entity_id) is None


async def test_optional_sensors_absent_when_hardware_missing(
    hass: HomeAssistant,
) -> None:
    """Optional sensors do not register while their hardware is absent."""
    device = FakeBrinkFlair()
    device.info.extension_device_type = 0
    device.measurements.dwelling_temperature = None
    device.status.co2_1_status = None
    device.status.co2_1_value = None
    device.status.co2_2_status = Co2SensorStatus.ERROR
    device.status.co2_2_value = 0
    entry, _ = await async_setup_brink_flair(hass, device)

    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "status_co2_1_value",
            "status_co2_1_status",
            "status_co2_2_value",
            "status_co2_2_status",
            "measurements_dwelling_temperature",
            "measurements_extension_temperature",
        ],
    )
    assert None in registered


async def test_co2_sensor_added_when_it_connects(hass: HomeAssistant) -> None:
    """A CO2 sensor that starts reporting appears after an update."""
    device = FakeBrinkFlair()
    device.status.co2_3_status = None
    device.status.co2_3_value = None
    entry, _ = await async_setup_brink_flair(hass, device)

    assert _registry_entry(hass, entry.entry_id, "status_co2_3_value") is None

    device.status.co2_3_status = Co2SensorStatus.RUNNING
    device.status.co2_3_value = 700
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    registered = _registry_ids(
        hass, entry.entry_id, ["status_co2_3_value", "status_co2_3_status"]
    )
    assert None not in registered


async def test_enabled_conditional_sensor_removed_when_hardware_drops(
    hass: HomeAssistant,
) -> None:
    """A live enabled sensor is flushed out once its hardware stops reporting.

    The optional sensors are registered as disabled by default, but a user can
    enable them. After a reload those entities are added to the platform and
    must be removed from it as well when the hardware drops out.
    """
    entry, device = await async_setup_brink_flair(
        hass, pre_enable_keys=("status_co2_1_value",)
    )

    value_entry = _registry_entry(hass, entry.entry_id, "status_co2_1_value")
    assert value_entry is not None
    assert not value_entry.disabled

    live = hass.states.get(value_entry.entity_id)
    assert live is not None
    assert live.state == "800"

    device.status.co2_1_status = Co2SensorStatus.ERROR
    device.status.co2_1_value = 0
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    assert hass.states.get(value_entry.entity_id) is None
    assert _registry_entry(hass, entry.entry_id, "status_co2_1_value") is None


async def test_optional_sensor_removed_when_hardware_drops(
    hass: HomeAssistant,
) -> None:
    """Sensors are fully removed once their hardware stops reporting."""
    entry, device = await async_setup_brink_flair(hass)

    for key in (
        "status_co2_1_value",
        "measurements_dwelling_temperature",
        "measurements_extension_temperature",
    ):
        assert _registry_entry(hass, entry.entry_id, key) is not None

    # The dwelling probe and extension module report that they are gone, and the
    # second CO2 sensor drops to an error state.
    device.measurements.dwelling_temperature = None
    device.info.extension_device_type = 0
    device.status.co2_1_status = Co2SensorStatus.ERROR
    device.status.co2_1_value = 0
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    registered = _registry_ids(
        hass,
        entry.entry_id,
        [
            "status_co2_1_value",
            "status_co2_1_status",
            "measurements_dwelling_temperature",
            "measurements_extension_temperature",
            "measurements_extension_analogue_input_1",
        ],
    )
    assert None in registered

    # Reconnecting the same hardware brings the sensors back.
    device.measurements.dwelling_temperature = 21.5
    device.info.extension_device_type = 24
    device.status.co2_1_status = Co2SensorStatus.RUNNING
    device.status.co2_1_value = 800
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    for key in (
        "status_co2_1_value",
        "measurements_dwelling_temperature",
        "measurements_extension_temperature",
    ):
        assert _registry_entry(hass, entry.entry_id, key) is not None


async def test_removal_skips_missing_registry_entry(hass: HomeAssistant) -> None:
    """Removal still succeeds when the registry entry is already gone."""
    entry, device = await async_setup_brink_flair(hass)

    co2_entry = _registry_entry(hass, entry.entry_id, "status_co2_1_value")
    assert co2_entry is not None

    registry = er.async_get(hass)
    registry.async_remove(co2_entry.entity_id)

    device.status.co2_1_status = Co2SensorStatus.ERROR
    device.status.co2_1_value = 0
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    assert _registry_entry(hass, entry.entry_id, "status_co2_1_value") is None


async def test_co2_value_follows_status_enum(hass: HomeAssistant) -> None:
    """A connected CO2 slot keeps its sensor even before a reading arrives."""
    entry, device = await async_setup_brink_flair(hass)

    device.status.co2_2_value = None
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    registered = _registry_ids(
        hass, entry.entry_id, ["status_co2_2_value", "status_co2_2_status"]
    )
    assert None not in registered
