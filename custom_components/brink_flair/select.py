"""Select platform — control mode and ventilation level of the Brink Flair unit."""

from dataclasses import dataclass
from enum import IntEnum
from typing import override

from brink_flair_modbus import BypassMode, ControlMode, VentilationLevel

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BrinkConfigEntry, BrinkCoordinator
from .entity import BrinkEntity


@dataclass(frozen=True, kw_only=True)
class BrinkSelectDescription(SelectEntityDescription):
    """Describes a select reading one writable enum field."""

    component: str
    attribute: str
    enum_type: type[IntEnum]


def _select(
    component: str,
    attribute: str,
    name: str,
    enum_type: type[IntEnum],
) -> BrinkSelectDescription:
    return BrinkSelectDescription(
        key=f"{component}_{attribute}",
        name=name,
        component=component,
        attribute=attribute,
        enum_type=enum_type,
        options=[option.name.lower() for option in enum_type],
    )


_DESCRIPTIONS: tuple[BrinkSelectDescription, ...] = (
    _select("settings", "control_mode", "Control mode", ControlMode),
    _select("settings", "level", "Ventilation level", VentilationLevel),
    _select("settings", "bypass_mode", "Bypass mode", BypassMode),
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
        """Initialize the select."""
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    @override
    def current_option(self) -> str | None:
        """Return the current mode as a lowercase option name."""
        value = getattr(self._subsystem, self.entity_description.attribute)
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
        """Refuse a forced bypass while the supply flow is too high.

        The unit can draw cold outside air through an open bypass, so the
        reference config blocks any user override above 200 m³/h.
        """
        supply_volume = self.coordinator.device.measurements.supply_volume
        if supply_volume is not None and supply_volume > 200:
            raise HomeAssistantError(
                f"Bypass override blocked while supply volume is {supply_volume} m³/h"
            )
