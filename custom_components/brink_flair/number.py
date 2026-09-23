"""Number platform — numeric airflow and filter settings of the Brink Flair unit."""

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
        device_class=(
            NumberDeviceClass.TEMPERATURE if unit == UnitOfTemperature.CELSIUS else None
        ),
        entity_category=EntityCategory.CONFIG,
    )


def _descriptions_for(limits: FlowLimits) -> tuple[BrinkNumberDescription, ...]:
    """Describe the numbers with the detected model's airflow envelope."""
    return (
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
        _config_gauge("settings", "bypass_boost_position", 0, 3, 1, None),
        _config_gauge("settings", "imbalance_intake", -15, 15, 1, PERCENTAGE),
        _config_gauge("settings", "imbalance_exhaust", -15, 15, 1, PERCENTAGE),
        _config_gauge(
            "settings",
            "bypass_from_dwelling",
            15,
            35,
            0.5,
            UnitOfTemperature.CELSIUS,
        ),
        _config_gauge(
            "settings",
            "bypass_from_outside",
            7,
            15,
            0.5,
            UnitOfTemperature.CELSIUS,
        ),
        _config_gauge(
            "settings",
            "bypass_hysteresis",
            0,
            5,
            0.5,
            UnitOfTemperature.CELSIUS,
        ),
        _config_gauge(
            "settings",
            "frost_control_temperature",
            -1.5,
            1.5,
            0.5,
            UnitOfTemperature.CELSIUS,
        ),
        _config_gauge(
            "settings",
            "frost_minimum_inlet_temperature",
            7,
            17,
            0.5,
            UnitOfTemperature.CELSIUS,
        ),
        BrinkNumberDescription(
            key="settings_filter_change_days",
            translation_key="settings_filter_change_days",
            component="settings",
            attribute="filter_change_days",
            native_min_value=0,
            native_max_value=365,
            native_step=1,
            entity_category=EntityCategory.CONFIG,
        ),
    )


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
