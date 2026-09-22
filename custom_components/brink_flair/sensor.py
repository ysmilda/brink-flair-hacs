"""Sensor platform — measured values and diagnostic status of the Brink Flair unit."""

from dataclasses import dataclass
from enum import IntEnum
from typing import cast, override

from brink_flair_modbus import (
    BypassMode,
    BypassStatus,
    ControlMode,
    DateFormat,
    DigitalInputFunction,
    ExternalHeaterMode,
    FanFunction,
    FlowType,
    FrostStatus,
    GeoValveOutput,
    GeoValvePosition,
    Language,
    ModbusInterfaceType,
    ModbusParity,
    ModbusSpeed,
    OperatingMode,
    SignalOutputFunction,
    TimeNotation,
    VentilationLevel,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BrinkConfigEntry, BrinkCoordinator
from .entity import BrinkEntity

# State arrives through the coordinator; async_update is not used.
PARALLEL_UPDATES = 0

_MODES = [mode.name.lower() for mode in OperatingMode]
_BYPASS = [mode.name.lower() for mode in BypassStatus]
_FROST = [mode.name.lower() for mode in FrostStatus]


def _options(enum_type: type[IntEnum]) -> list[str]:
    """Return the lowercase option names of an enum for an ENUM sensor."""
    return [option.name.lower() for option in enum_type]


@dataclass(frozen=True, kw_only=True)
class BrinkSensorDescription(SensorEntityDescription):
    """Describes a sensor reading one attribute of one component."""

    component: str
    attribute: str


def _measurement(
    component: str,
    attribute: str,
    *,
    device_class: SensorDeviceClass | None = None,
    native_unit_of_measurement: str | None = None,
    state_class: SensorStateClass | None = None,
    diagnostic: bool = False,
    entity_registry_enabled_default: bool = True,
    precision: int | None = None,
    key: str | None = None,
    options: list[str] | None = None,
) -> BrinkSensorDescription:
    key = key or f"{component}_{attribute}"
    return BrinkSensorDescription(
        key=key,
        translation_key=key,
        component=component,
        attribute=attribute,
        device_class=device_class,
        native_unit_of_measurement=native_unit_of_measurement,
        state_class=state_class,
        options=options,
        entity_category=EntityCategory.DIAGNOSTIC if diagnostic else None,
        entity_registry_enabled_default=entity_registry_enabled_default,
        suggested_display_precision=precision,
    )


_MEASUREMENTS: tuple[BrinkSensorDescription, ...] = (
    _measurement(
        "measurements",
        "supply_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "exhaust_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.PA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "setpoint_supply_volume",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "supply_volume",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "supply_mass_flow",
        native_unit_of_measurement="kg/h",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "supply_fan_rpm",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "supply_anemometer_rpm",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "supply_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
    _measurement(
        "measurements",
        "supply_relative_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "setpoint_exhaust_volume",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "exhaust_volume",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "exhaust_mass_flow",
        native_unit_of_measurement="kg/h",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "exhaust_fan_rpm",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "exhaust_anemometer_rpm",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "exhaust_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
    _measurement(
        "measurements",
        "exhaust_relative_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _measurement(
        "measurements",
        "bypass_step_position",
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "preheater_capacity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "frost_heater_setpoint",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "frost_fan_reduction",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "outside_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
    _measurement(
        "measurements",
        "dwelling_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "rht_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "filter_used_hours",
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "filter_used_volume",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "current_operating_time",
        native_unit_of_measurement="h",
        state_class=SensorStateClass.TOTAL_INCREASING,
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "total_flow",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "current_time",
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "current_date",
        diagnostic=True,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "device",
        "exchange_filter_in",
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        precision=1,
    ),
    _measurement(
        "info",
        "model",
        key="info_device_type",
        diagnostic=True,
    ),
    _measurement(
        "info",
        "software_version",
        diagnostic=True,
        entity_registry_enabled_default=False
    ),
    _measurement(
        "info",
        "hardware_version",
        diagnostic=True,
        entity_registry_enabled_default=False
    ),
    _measurement(
        "info",
        "serial_number",
        diagnostic=True,
        entity_registry_enabled_default=False
    ),
)


def _setting(
    attribute: str,
    *,
    device_class: SensorDeviceClass | None = None,
    native_unit_of_measurement: str | None = None,
    precision: int | None = None,
    options: list[str] | None = None,
) -> BrinkSensorDescription:
    """Describe one writable settings field as a diagnostic sensor."""
    return _measurement(
        "settings",
        attribute,
        device_class=device_class,
        native_unit_of_measurement=native_unit_of_measurement,
        diagnostic=True,
        entity_registry_enabled_default=False,
        precision=precision,
        options=options,
    )


_SETTINGS: tuple[BrinkSensorDescription, ...] = (
    _setting("pwm_inlet_0", native_unit_of_measurement=PERCENTAGE),
    _setting("pwm_exhaust_0", native_unit_of_measurement=PERCENTAGE),
    _setting("pwm_inlet_1", native_unit_of_measurement=PERCENTAGE),
    _setting("pwm_exhaust_1", native_unit_of_measurement=PERCENTAGE),
    _setting("pwm_inlet_2", native_unit_of_measurement=PERCENTAGE),
    _setting("pwm_exhaust_2", native_unit_of_measurement=PERCENTAGE),
    _setting("pwm_inlet_3", native_unit_of_measurement=PERCENTAGE),
    _setting("pwm_exhaust_3", native_unit_of_measurement=PERCENTAGE),
    _setting(
        "flow_0",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    _setting(
        "flow_1",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    _setting(
        "flow_2",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    _setting(
        "flow_3",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    _setting(
        "desired_flow_rate",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    _setting("flow_type", device_class=SensorDeviceClass.ENUM, options=_options(FlowType)),
    _setting("switch_default_position"),
    _setting("display_as_switch"),
    _setting("imbalance_allowed"),
    _setting("imbalance_value", native_unit_of_measurement=PERCENTAGE),
    _setting("imbalance_intake", native_unit_of_measurement=PERCENTAGE, precision=1),
    _setting("imbalance_exhaust", native_unit_of_measurement=PERCENTAGE, precision=1),
    _setting(
        "bypass_mode",
        device_class=SensorDeviceClass.ENUM,
        options=_options(BypassMode),
    ),
    _setting(
        "bypass_from_dwelling",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting(
        "bypass_from_outside",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting(
        "bypass_hysteresis",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting("bypass_boost"),
    _setting("bypass_boost_position"),
    _setting(
        "frost_control_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting(
        "frost_minimum_inlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting("filter_change_days"),
    _setting(
        "external_heater_mode",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ExternalHeaterMode),
    ),
    _setting(
        "postheater_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting("rht_sensor_mode"),
    _setting("rht_sensor_sensitivity"),
    _setting("co2_sensor_mode"),
    _setting("co2_1_low_level", native_unit_of_measurement="ppm"),
    _setting("co2_1_high_level", native_unit_of_measurement="ppm"),
    _setting("co2_2_low_level", native_unit_of_measurement="ppm"),
    _setting("co2_2_high_level", native_unit_of_measurement="ppm"),
    _setting("co2_3_low_level", native_unit_of_measurement="ppm"),
    _setting("co2_3_high_level", native_unit_of_measurement="ppm"),
    _setting("co2_4_low_level", native_unit_of_measurement="ppm"),
    _setting("co2_4_high_level", native_unit_of_measurement="ppm"),
    _setting(
        "signal_output_function",
        device_class=SensorDeviceClass.ENUM,
        options=_options(SignalOutputFunction),
    ),
    _setting("cv_connected"),
    _setting("digital_input_1_closed"),
    _setting(
        "digital_input_1_function",
        device_class=SensorDeviceClass.ENUM,
        options=_options(DigitalInputFunction),
    ),
    _setting(
        "digital_input_1_supply_fan",
        device_class=SensorDeviceClass.ENUM,
        options=_options(FanFunction),
    ),
    _setting(
        "digital_input_1_exhaust_fan",
        device_class=SensorDeviceClass.ENUM,
        options=_options(FanFunction),
    ),
    _setting("digital_input_2_closed"),
    _setting(
        "digital_input_2_function",
        device_class=SensorDeviceClass.ENUM,
        options=_options(DigitalInputFunction),
    ),
    _setting(
        "digital_input_2_supply_fan",
        device_class=SensorDeviceClass.ENUM,
        options=_options(FanFunction),
    ),
    _setting(
        "digital_input_2_exhaust_fan",
        device_class=SensorDeviceClass.ENUM,
        options=_options(FanFunction),
    ),
    _setting("analogue_input_1_mode"),
    _setting(
        "analogue_input_1_vmin",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _setting(
        "analogue_input_1_vmax",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _setting("analogue_input_2_mode"),
    _setting(
        "analogue_input_2_vmin",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _setting(
        "analogue_input_2_vmax",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _setting("geo_exchanger"),
    _setting(
        "geo_minimum_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting(
        "geo_maximum_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        precision=1,
    ),
    _setting(
        "geo_valve_default_position",
        device_class=SensorDeviceClass.ENUM,
        options=_options(GeoValvePosition),
    ),
    _setting(
        "geo_valve_output",
        device_class=SensorDeviceClass.ENUM,
        options=_options(GeoValveOutput),
    ),
    _setting(
        "language",
        device_class=SensorDeviceClass.ENUM,
        options=_options(Language),
    ),
    _setting(
        "date_format",
        device_class=SensorDeviceClass.ENUM,
        options=_options(DateFormat),
    ),
    _setting(
        "time_notation",
        device_class=SensorDeviceClass.ENUM,
        options=_options(TimeNotation),
    ),
    _setting("clock_month_day"),
    _setting("clock_year"),
    _setting("clock_time"),
    _setting("clock_day_seconds"),
    _setting(
        "modbus_interface_type",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ModbusInterfaceType),
    ),
    _setting("modbus_slave_address"),
    _setting(
        "modbus_speed",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ModbusSpeed),
    ),
    _setting(
        "modbus_parity",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ModbusParity),
    ),
    _setting(
        "control_mode",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ControlMode),
    ),
    _setting(
        "level",
        device_class=SensorDeviceClass.ENUM,
        options=_options(VentilationLevel),
    ),
)


def _enum_sensor(
    component: str,
    attribute: str,
    options: list[str],
) -> BrinkSensorDescription:
    key = f"{component}_{attribute}"
    return BrinkSensorDescription(
        key=key,
        translation_key=key,
        component=component,
        attribute=attribute,
        device_class=SensorDeviceClass.ENUM,
        options=options,
        entity_category=EntityCategory.DIAGNOSTIC,
    )


_STATUS: tuple[BrinkSensorDescription, ...] = (
    _enum_sensor("status", "operation_mode", _MODES),
    _enum_sensor("status", "bypass_status", _BYPASS),
    _enum_sensor("status", "frost_status", _FROST),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Brink Flair sensors."""
    coordinator = entry.runtime_data
    entities: list[BrinkSensor] = [
        BrinkSensor(coordinator, d) for d in (*_MEASUREMENTS, *_STATUS, *_SETTINGS)
    ]
    async_add_entities(entities)


class BrinkSensor(BrinkEntity, SensorEntity):
    """A single value read from a component attribute."""

    entity_description: BrinkSensorDescription

    def __init__(
        self, coordinator: BrinkCoordinator, description: BrinkSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    @override
    def native_value(self) -> int | float | str | None:
        """Return the value; enums as lowercase names, floats rounded to precision."""
        value = getattr(self._subsystem, self.entity_description.attribute)
        if isinstance(value, IntEnum):
            return value.name.lower()
        precision = self.entity_description.suggested_display_precision
        if isinstance(value, float) and precision is not None:
            return round(value, precision)
        return cast(int | float | str | None, value)
