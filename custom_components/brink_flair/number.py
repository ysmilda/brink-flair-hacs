"""Number platform — writable numeric settings of the Brink Flair unit."""

from dataclasses import dataclass
from typing import cast, override

from brink_flair_modbus import FlowLimits

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BrinkConfigEntry, BrinkCoordinator
from .entity import BrinkEntity

# State arrives through the coordinator; async_update is not used.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class BrinkNumberDescription(NumberEntityDescription):
    """Describes a number reading one writable register field."""

    component: str
    attribute: str


def _flow(
    component: str,
    attribute: str,
    minimum: int,
    maximum: int,
    *,
    config: bool,
) -> BrinkNumberDescription:
    return BrinkNumberDescription(
        key=f"{component}_{attribute}",
        translation_key=f"{component}_{attribute}",
        component=component,
        attribute=attribute,
        native_min_value=minimum,
        native_max_value=maximum,
        native_step=1,
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        entity_category=EntityCategory.CONFIG if config else None,
    )


def _config_gauge(
    component: str,
    attribute: str,
    minimum: float,
    maximum: float,
    step: float,
    unit: str | None,
    *,
    device_class: NumberDeviceClass | None = None,
) -> BrinkNumberDescription:
    return BrinkNumberDescription(
        key=f"{component}_{attribute}",
        translation_key=f"{component}_{attribute}",
        component=component,
        attribute=attribute,
        native_min_value=minimum,
        native_max_value=maximum,
        native_step=step,
        native_unit_of_measurement=unit,
        device_class=device_class
        or (
            NumberDeviceClass.TEMPERATURE if unit == UnitOfTemperature.CELSIUS else None
        ),
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
    )


CONCENTRATION_PARTS_PER_MILLION = "ppm"

# Fixed-range writable registers, mirroring the library's field metadata.
_CONFIG_GAUGES: tuple[
    tuple[str, float, float, float, str | None, NumberDeviceClass | None], ...
] = (
    *(  # PWM fan presets, steps 0-3 for both fans.
        (f"pwm_{fan}_{step}", 15, 100, 1, PERCENTAGE, None)
        for step in range(4)
        for fan in ("inlet", "exhaust")
    ),
    ("switch_default_position", 0, 3, 1, None, None),
    ("imbalance_value", 0, 20, 1, PERCENTAGE, None),
    ("imbalance_intake", -15, 15, 1, PERCENTAGE, None),
    ("imbalance_exhaust", -15, 15, 1, PERCENTAGE, None),
    ("bypass_from_dwelling", 15, 35, 0.5, UnitOfTemperature.CELSIUS, None),
    ("bypass_from_outside", 7, 15, 0.5, UnitOfTemperature.CELSIUS, None),
    ("bypass_hysteresis", 0, 5, 0.5, UnitOfTemperature.CELSIUS, None),
    ("bypass_boost_position", 0, 3, 1, None, None),
    ("frost_control_temperature", -1.5, 1.5, 0.5, UnitOfTemperature.CELSIUS, None),
    ("frost_minimum_inlet_temperature", 7, 17, 0.5, UnitOfTemperature.CELSIUS, None),
    ("filter_change_days", 0, 365, 1, UnitOfTime.DAYS, None),
    ("postheater_setpoint", 15, 30, 0.5, UnitOfTemperature.CELSIUS, None),
    ("rht_sensor_sensitivity", -2, 2, 1, None, None),
    *(  # CO2 thresholds of the four optional sensors.
        (
            f"co2_{sensor}_{bound}_level",
            400,
            2000,
            1,
            CONCENTRATION_PARTS_PER_MILLION,
            None,
        )
        for sensor in range(1, 5)
        for bound in ("low", "high")
    ),
    *(  # Voltage span of the two analogue inputs.
        (f"analogue_input_{port}_v{bound}", 0, 10, 0.5, "V", NumberDeviceClass.VOLTAGE)
        for port in (1, 2)
        for bound in ("min", "max")
    ),
    ("geo_minimum_temperature", 0, 10, 0.5, UnitOfTemperature.CELSIUS, None),
    ("geo_maximum_temperature", 15, 40, 0.5, UnitOfTemperature.CELSIUS, None),
)


def _descriptions_for(limits: FlowLimits) -> tuple[BrinkNumberDescription, ...]:
    """Describe the numbers with the detected model's airflow envelope."""
    descriptions: list[BrinkNumberDescription] = [
        _flow(
            "settings",
            "desired_flow_rate",
            0,
            limits.modbus_flow_rate_max,
            config=False,
        ),
        _flow("settings", "flow_0", 0, limits.flow_max, config=True),
        _flow("settings", "flow_1", 50, limits.flow_max, config=True),
        _flow("settings", "flow_2", 50, limits.flow_max, config=True),
        _flow("settings", "flow_3", 50, limits.flow_max, config=True),
    ]
    descriptions.extend(
        _config_gauge(
            "settings", attribute, minimum, maximum, step, unit, device_class=dc
        )
        for attribute, minimum, maximum, step, unit, dc in _CONFIG_GAUGES
    )
    return tuple(descriptions)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Brink Flair numbers."""
    coordinator = entry.runtime_data
    async_add_entities(
        BrinkFlairNumber(coordinator, description)
        for description in _descriptions_for(coordinator.device.flow_limits)
    )


class BrinkFlairNumber(BrinkEntity, NumberEntity):
    """A writable numeric register exposed as a number."""

    entity_description: BrinkNumberDescription

    def __init__(
        self, coordinator: BrinkCoordinator, description: BrinkNumberDescription
    ) -> None:
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    @override
    def native_value(self) -> float | None:
        pending = self.pending_value
        if pending is not None:
            return pending
        return cast(
            float | None, getattr(self._subsystem, self.entity_description.attribute)
        )

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Write the value, showing it optimistically until confirmed."""
        self._pending_write(value)
        self.async_write_ha_state()
        try:
            await self.coordinator.device.settings.write(
                self.entity_description.attribute, value
            )
        except Exception:
            self._pending_write(None)
            self.async_write_ha_state()
            raise
