"""Switch platform — bypass boost and the optimistic standby toggle.

Standby (register 8003) is never read back, so its switch mirrors the last request.
"""

from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BrinkConfigEntry, BrinkCoordinator
from .entity import BrinkEntity

# State arrives through the coordinator; async_update is not used.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class BrinkSwitchDescription(SwitchEntityDescription):
    """Describes a switch reading one register field."""

    component: str
    attribute: str | None


_SWITCHES: tuple[BrinkSwitchDescription, ...] = (
    BrinkSwitchDescription(
        key="settings_bypass_boost",
        translation_key="settings_bypass_boost",
        component="settings",
        attribute="bypass_boost",
    ),
    BrinkSwitchDescription(
        key="standby",
        translation_key="standby",
        component="settings",
        attribute=None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Brink Flair switches."""
    coordinator = entry.runtime_data
    async_add_entities(
        BrinkFlairSwitch(coordinator, description) for description in _SWITCHES
    )


class BrinkFlairSwitch(BrinkEntity, SwitchEntity):
    """A switch for a settings field, or the optimistic standby mirror."""

    entity_description: BrinkSwitchDescription

    def __init__(
        self, coordinator: BrinkCoordinator, description: BrinkSwitchDescription
    ) -> None:
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the field state, or the hopeful standby mirror."""
        attribute = self.entity_description.attribute
        if attribute is None:
            return self._attr_is_on
        value = getattr(self._subsystem, attribute)
        if value is None:
            return None
        return bool(value)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the field or set the unit to standby."""
        attribute = self.entity_description.attribute
        if attribute is None:
            await self.coordinator.device.async_set_standby(True)
            self._attr_is_on = True
            self.async_write_ha_state()
            return
        await self.coordinator.device.settings.write(attribute, True)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the field or return the unit to normal operation."""
        attribute = self.entity_description.attribute
        if attribute is None:
            await self.coordinator.device.async_set_standby(False)
            self._attr_is_on = False
            self.async_write_ha_state()
            return
        await self.coordinator.device.settings.write(attribute, False)
