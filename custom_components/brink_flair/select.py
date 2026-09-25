"""Select platform — writable enum settings of the Brink Flair unit."""

from dataclasses import dataclass
from enum import IntEnum
from typing import cast, override

from brink_flair_modbus import (
    BypassMode,
    ControlMode,
    DateFormat,
    DigitalInputFunction,
    ExternalHeaterMode,
    FanFunction,
    FlowType,
    GeoValveOutput,
    GeoValvePosition,
    Language,
    SignalOutputFunction,
    TimeNotation,
    VentilationLevel,
)

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BrinkConfigEntry, BrinkCoordinator
from .entity import BrinkEntity
from .exceptions import BypassOverrideBlockedError

# State arrives through the coordinator; async_update is not used.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class BrinkSelectDescription(SelectEntityDescription):
    """Describes a select reading one writable enum field."""

    component: str
    attribute: str
    enum_type: type[IntEnum]


def _select(
    component: str,
    attribute: str,
    enum_type: type[IntEnum],
) -> BrinkSelectDescription:
    key = f"{component}_{attribute}"
    return BrinkSelectDescription(
        key=key,
        translation_key=key,
        component=component,
        attribute=attribute,
        enum_type=enum_type,
        options=[option.name.lower() for option in enum_type],
        entity_category=EntityCategory.CONFIG,
    )


_DESCRIPTIONS: tuple[BrinkSelectDescription, ...] = (
    _select("settings", "control_mode", ControlMode),
    _select("settings", "level", VentilationLevel),
    _select("settings", "bypass_mode", BypassMode),
    _select("settings", "flow_type", FlowType),
    _select("settings", "external_heater_mode", ExternalHeaterMode),
    _select("settings", "signal_output_function", SignalOutputFunction),
    _select("settings", "digital_input_1_function", DigitalInputFunction),
    _select("settings", "digital_input_1_supply_fan", FanFunction),
    _select("settings", "digital_input_1_exhaust_fan", FanFunction),
    _select("settings", "digital_input_2_function", DigitalInputFunction),
    _select("settings", "digital_input_2_supply_fan", FanFunction),
    _select("settings", "digital_input_2_exhaust_fan", FanFunction),
    _select("settings", "geo_valve_default_position", GeoValvePosition),
    _select("settings", "geo_valve_output", GeoValveOutput),
    _select("settings", "language", Language),
    _select("settings", "date_format", DateFormat),
    _select("settings", "time_notation", TimeNotation),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Brink Flair selects."""
    coordinator = entry.runtime_data
    async_add_entities(
        BrinkFlairSelect(coordinator, description) for description in _DESCRIPTIONS
    )


class BrinkFlairSelect(BrinkEntity, SelectEntity):
    """A dropdown for one writable mode field."""

    entity_description: BrinkSelectDescription

    def __init__(
        self, coordinator: BrinkCoordinator, description: BrinkSelectDescription
    ) -> None:
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    @override
    def current_option(self) -> str | None:
        """Return the current mode as a lowercase option name."""
        pending = self.pending_value
        if pending is not None:
            return pending
        value = cast(
            IntEnum | None, getattr(self._subsystem, self.entity_description.attribute)
        )
        if value is None:
            return None
        return value.name.lower()

    @override
    async def async_select_option(self, option: str) -> None:
        """Write the selected mode, showing it optimistically until confirmed."""
        if self.entity_description.attribute == "bypass_mode":
            await self._guard_bypass_override()
        enum_type = self.entity_description.enum_type
        self._pending_write(option)
        self.async_write_ha_state()
        try:
            await self.coordinator.device.settings.write(
                self.entity_description.attribute, enum_type[option.upper()]
            )
        except Exception:
            self._pending_write(None)
            self.async_write_ha_state()
            raise

    async def _guard_bypass_override(self) -> None:
        """Block a forced bypass above 200 m³/h supply flow (it would draw cold air in)."""
        supply_volume = self.coordinator.device.measurements.supply_volume
        if supply_volume is not None and supply_volume > 200:
            raise BypassOverrideBlockedError(supply_volume)
