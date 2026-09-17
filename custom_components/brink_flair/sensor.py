"""Sensor platform — measured values and diagnostic status of the Brink Flair unit."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from typing import cast, override

from brink_flair_modbus import (
    BypassStatus,
    Co2SensorStatus,
    EBusPowerStatus,
    FanControlType,
    FanStatus,
    FrostStatus,
    GeoExchangerStatus,
    OperatingMode,
    PreheaterStatus,
    SystemErrorStatus,
    VentilationMode,
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
    UnitOfRatio,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .conditional import (
    ConditionalEntities,
    co2_connected,
    dwelling_connected,
    extension_connected,
)
from .coordinator import BrinkConfigEntry, BrinkCoordinator
from .entity import BrinkEntity

# State arrives through the coordinator; async_update is not used.
PARALLEL_UPDATES = 0

_MODES = [mode.name.lower() for mode in OperatingMode]
_BYPASS = [mode.name.lower() for mode in BypassStatus]
_FROST = [mode.name.lower() for mode in FrostStatus]
_FAN_CONTROL = [mode.name.lower() for mode in FanControlType]
_VENT_MODES = [mode.name.lower() for mode in VentilationMode]
_FAN_STATUS = [mode.name.lower() for mode in FanStatus]
_PREHEATER = [mode.name.lower() for mode in PreheaterStatus]
_EBUS = [mode.name.lower() for mode in EBusPowerStatus]
_GEO = [mode.name.lower() for mode in GeoExchangerStatus]
_SYSTEM_ERROR = [mode.name.lower() for mode in SystemErrorStatus]
_CO2 = [mode.name.lower() for mode in Co2SensorStatus]


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
    entity_registry_enabled_default: bool | None = None,
    precision: int | None = None,
    key: str | None = None,
) -> BrinkSensorDescription:
    if entity_registry_enabled_default is None:
        entity_registry_enabled_default = not diagnostic
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
        "supply_mass_flow",
        native_unit_of_measurement="kg/h",
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
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
        diagnostic=True,
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
        diagnostic=True,
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
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "bypass_step_position",
        diagnostic=True,
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
        "preheater_capacity",
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
        "rht_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "filter_used_hours",
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        entity_registry_enabled_default=True,
    ),
    _measurement(
        "measurements",
        "filter_used_volume",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        diagnostic=True,
        entity_registry_enabled_default=True,
    ),
    _measurement(
        "measurements",
        "current_operating_time",
        native_unit_of_measurement="h",
        state_class=SensorStateClass.TOTAL_INCREASING,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "total_flow",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        diagnostic=True,
    ),
    _measurement(
        "device",
        "filter_used_days",
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        entity_registry_enabled_default=True,
        precision=1,
    ),
    _measurement(
        "device",
        "exchange_filter_in",
        state_class=SensorStateClass.MEASUREMENT,
        diagnostic=True,
        entity_registry_enabled_default=True,
        precision=1,
    ),
    _measurement(
        "info",
        "model",
        key="info_device_type",
        diagnostic=True,
    ),
)


def _enum_sensor(
    component: str,
    attribute: str,
    options: list[str],
    *,
    enabled_default: bool = False,
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
        entity_registry_enabled_default=enabled_default,
    )


_STATUS: tuple[BrinkSensorDescription, ...] = (
    _enum_sensor("status", "operation_mode", _MODES, enabled_default=True),
    _enum_sensor("status", "fan_control_type", _FAN_CONTROL),
    _enum_sensor("status", "ventilation_mode", _VENT_MODES),
    _enum_sensor("status", "supply_fan_status", _FAN_STATUS),
    _enum_sensor("status", "exhaust_fan_status", _FAN_STATUS),
    _enum_sensor("status", "bypass_status", _BYPASS),
    _enum_sensor("status", "preheater_status", _PREHEATER),
    _enum_sensor("status", "frost_status", _FROST),
    _enum_sensor("status", "ebus_power_status", _EBUS),
    _enum_sensor("status", "geo_exchanger_status", _GEO),
    _enum_sensor("status", "system_error", _SYSTEM_ERROR),
    _measurement("status", "flow_switch_position", diagnostic=True),
    _measurement("status", "active_incident", diagnostic=True),
)


def _co2_sensor(n: int) -> tuple[BrinkSensorDescription, BrinkSensorDescription]:
    """Return the value and status descriptions of CO2 sensor slot ``n``."""
    return (
        _measurement(
            "status",
            f"co2_{n}_value",
            device_class=SensorDeviceClass.CO2,
            native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=False,
        ),
        _enum_sensor("status", f"co2_{n}_status", _CO2),
    )


_EXTENSION: tuple[BrinkSensorDescription, ...] = (
    _measurement(
        "measurements",
        "extension_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        entity_registry_enabled_default=False,
    ),
    _measurement(
        "measurements",
        "extension_analogue_input_1",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "extension_analogue_input_2",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "extension_analogue_output_1",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        diagnostic=True,
    ),
    _measurement(
        "measurements",
        "extension_analogue_output_2",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
        diagnostic=True,
    ),
)

_DWELLING_TEMPERATURE = _measurement(
    "measurements",
    "dwelling_temperature",
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
    precision=1,
    entity_registry_enabled_default=False,
)


def _conditional_groups(
    hass: HomeAssistant,
    coordinator: BrinkCoordinator,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> tuple[ConditionalEntities, ...]:
    """Create the optional sensor groups whose presence follows the hardware."""

    def build(descriptions: Sequence[BrinkSensorDescription]) -> list[BrinkSensor]:
        return [BrinkSensor(coordinator, d) for d in descriptions]

    groups: list[ConditionalEntities] = []

    for sensor_n in range(1, 5):
        descriptions = _co2_sensor(sensor_n)
        groups.append(
            ConditionalEntities(
                hass,
                async_add_entities,
                test=lambda device, n=sensor_n: co2_connected(device, n),
                build=lambda descriptions=descriptions: build(descriptions),
            )
        )

    groups.append(
        ConditionalEntities(
            hass,
            async_add_entities,
            test=extension_connected,
            build=lambda: build(_EXTENSION),
        )
    )
    groups.append(
        ConditionalEntities(
            hass,
            async_add_entities,
            test=dwelling_connected,
            build=lambda: build((_DWELLING_TEMPERATURE,)),
        )
    )
    return tuple(groups)


@callback
def _reconcile_conditional(
    coordinator: BrinkCoordinator, groups: Sequence[ConditionalEntities]
) -> None:
    """Reconcile every optional group against the current device data."""
    device = coordinator.device
    for group in groups:
        group.async_update(device)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Brink Flair sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [BrinkSensor(coordinator, d) for d in (*_MEASUREMENTS, *_STATUS)]
    )

    groups = _conditional_groups(hass, coordinator, async_add_entities)
    _reconcile_conditional(coordinator, groups)

    entry.async_on_unload(
        coordinator.async_add_listener(
            lambda: _reconcile_conditional(coordinator, groups)
        )
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
