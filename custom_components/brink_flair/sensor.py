"""Sensor platform — measured values and diagnostic status of the Brink Flair unit."""

from dataclasses import dataclass
from datetime import date, time
from enum import IntEnum
from typing import Any, cast, override

from brink_flair_modbus import (
    BypassStatus,
    FrostStatus,
    ModbusParity,
    ModbusSpeed,
    OperatingMode,
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
    entity_category: EntityCategory | None = None,
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
        entity_category=entity_category,
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
        entity_category=EntityCategory.DIAGNOSTIC,
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
        entity_category=EntityCategory.DIAGNOSTIC,
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
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "preheater_capacity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "frost_heater_setpoint",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _measurement(
        "measurements",
        "frost_fan_reduction",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
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
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _measurement(
        "measurements",
        "filter_used_volume",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _measurement(
        "measurements",
        "current_operating_time",
        native_unit_of_measurement="h",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "total_flow",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "current_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "current_date",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "device",
        "exchange_filter_in",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        precision=1,
    ),
    _measurement(
        "info",
        "model",
        key="info_device_type",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _measurement(
        "info",
        "software_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "info",
        "hardware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "info",
        "serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
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
    """Describe one writable settings field as a diagnostic sensor.

    The sensor platform forbids EntityCategory.CONFIG, so the writable CONFIG
    entities live in number.py and select.py; this read-only mirror stays
    diagnostic.
    """
    return _measurement(
        "settings",
        attribute,
        device_class=device_class,
        native_unit_of_measurement=native_unit_of_measurement,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=precision,
        options=options,
    )


_SETTINGS: tuple[BrinkSensorDescription, ...] = (
    # The Modbus link settings are configured in the config flow instead: writing
    # the station address or line speed from an entity moves the unit out from
    # under the open connection with nothing left to reconnect it. These stay
    # read-only so the unit's actual settings stay visible for diagnosis.
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

# The four settings registers the unit splits its clock across. The weekday and
# seconds register is kept in the raw attributes but deliberately left out of
# the decoded value: the unit packs it ambiguously, and guessing risks showing
# a plausible but wrong time.
_CLOCK_FIELDS: tuple[str, ...] = (
    "clock_month_day",
    "clock_year",
    "clock_time",
    "clock_day_seconds",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Brink Flair sensors."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        BrinkSensor(coordinator, d) for d in (*_MEASUREMENTS, *_STATUS, *_SETTINGS)
    ]
    entities.append(BrinkClockSensor(coordinator))
    async_add_entities(entities)


def _bcd(value: int) -> int | None:
    """Decode one packed BCD byte, or ``None`` when it is not valid BCD."""
    tens, ones = divmod(value, 16)
    return tens * 10 + ones if ones <= 9 else None


@dataclass(frozen=True, kw_only=True)
class BrinkClockDescription(SensorEntityDescription):
    """Describes the unit clock, assembled from four packed settings registers."""

    key: str = "settings_clock"
    translation_key: str = "settings_clock"
    entity_category: EntityCategory = EntityCategory.DIAGNOSTIC
    entity_registry_enabled_default: bool = False


_CLOCK = BrinkClockDescription()


class BrinkClockSensor(BrinkEntity, SensorEntity):
    """The unit's clock, decoded from the four packed settings registers.

    The unit stores the date and time as byte pairs, so the raw values are not
    meaningful on their own. Decoding is deliberately strict: a register that
    does not hold a plausible component makes the whole reading unavailable
    rather than reporting a made-up time, since a wrong clock is worse than a
    missing one when diagnosing a unit.
    """

    _attr_has_entity_name = True
    entity_description = _CLOCK

    def __init__(self, coordinator: BrinkCoordinator) -> None:
        super().__init__(coordinator, _CLOCK.key, "settings")

    @property
    @override
    def native_value(self) -> str | None:
        """Return the decoded clock as ``YYYY-MM-DD HH:MM``, if it is coherent."""
        return self._decoded

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the raw registers, so an implausible decode can be inspected."""
        settings = self._subsystem
        return {
            field: getattr(settings, field)
            for field in _CLOCK_FIELDS
            if getattr(settings, field, None) is not None
        }

    @property
    def _decoded(self) -> str | None:
        """Return the decoded clock, or ``None`` when it cannot be trusted."""
        settings = self._subsystem
        month_day = getattr(settings, "clock_month_day", None)
        year = getattr(settings, "clock_year", None)
        clock_time = getattr(settings, "clock_time", None)
        if month_day is None or year is None or clock_time is None:
            return None

        month = _bcd(month_day >> 8)
        day = _bcd(month_day & 0xFF)
        hour = _bcd(clock_time >> 8)
        minute = _bcd(clock_time & 0xFF)
        if month is None or day is None or hour is None or minute is None:
            return None
        try:
            # date and time validate the decoded parts, rejecting impossible
            # values such as the 30th of February or 25:70.
            decoded_date = date(int(year), month, day)
            decoded_time = time(hour, minute)
        except ValueError:
            return None
        return (
            f"{decoded_date.isoformat()} {decoded_time.isoformat(timespec='minutes')}"
        )


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
