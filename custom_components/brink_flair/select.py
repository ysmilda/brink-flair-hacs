"""Select platform — control mode and ventilation level of the Brink Flair unit."""

from dataclasses import dataclass
from enum import IntEnum
from typing import cast, override

from brink_flair_modbus import BypassMode, ControlMode, VentilationLevel

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
    )


_DESCRIPTIONS: tuple[BrinkSelectDescription, ...] = (
    _select("settings", "control_mode", ControlMode),
    _select("settings", "level", VentilationLevel),
    _select("settings", "bypass_mode", BypassMode),
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
        value = cast(
            IntEnum | None, getattr(self._subsystem, self.entity_description.attribute)
        )
        if value is None:
            return None
        return value.name.lower()

    @override
    async def async_select_option(self, option: str) -> None:
        """Write the selected mode to the unit."""
        if self.entity_description.attribute == "bypass_mode":
            await self._guard_bypass_override()
        enum_type = self.entity_description.enum_type
        await self.coordinator.device.settings.write(
            self.entity_description.attribute, enum_type[option.upper()]
        )

    async def _guard_bypass_override(self) -> None:
        """Block a forced bypass above 200 m³/h supply flow (it would draw cold air in)."""
        supply_volume = self.coordinator.device.measurements.supply_volume
        if supply_volume is not None and supply_volume > 200:
            raise BypassOverrideBlockedError(supply_volume)
