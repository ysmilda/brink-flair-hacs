"""Sensor platform — measured values and diagnostic status of the Brink Flair unit."""

from dataclasses import dataclass
from enum import IntEnum
from typing import cast, override

from brink_flair_modbus import BypassStatus, FrostStatus, OperatingMode

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
        "supply_fan_rpm",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
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
        "exhaust_fan_rpm",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
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
        BrinkSensor(coordinator, d) for d in (*_MEASUREMENTS, *_STATUS)
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
