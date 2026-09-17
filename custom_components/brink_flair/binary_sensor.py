"""Binary sensor platform for the Brink Flair unit.

Covers the filter warning that is always present, the energized state of the
unit's signal output, and the contact/relay inputs of an optional extension
module (which only register while such a module is connected).
"""

from dataclasses import dataclass
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .conditional import ConditionalEntities, extension_connected
from .coordinator import BrinkConfigEntry, BrinkCoordinator
from .entity import BrinkEntity

# State arrives through the coordinator; async_update is not used.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class BrinkBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a binary sensor reading one attribute of one component."""

    component: str
    attribute: str


_FILTER = BrinkBinarySensorDescription(
    key="status_filter_dirty",
    translation_key="status_filter_dirty",
    component="status",
    attribute="filter_dirty",
    device_class=BinarySensorDeviceClass.PROBLEM,
    entity_category=EntityCategory.DIAGNOSTIC,
)

_OUTPUT = BrinkBinarySensorDescription(
    key="status_signal_output",
    translation_key="status_signal_output",
    component="status",
    attribute="signal_output",
    entity_category=EntityCategory.DIAGNOSTIC,
    entity_registry_enabled_default=False,
)

_EXTENSION_ATTRIBUTES = (
    "extension_contact_1",
    "extension_contact_2",
    "extension_relay_1",
    "extension_relay_2",
)


def _extension_descriptions() -> tuple[BrinkBinarySensorDescription, ...]:
    return tuple(
        BrinkBinarySensorDescription(
            key=f"measurements_{attribute}",
            translation_key=f"measurements_{attribute}",
            component="measurements",
            attribute=attribute,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for attribute in _EXTENSION_ATTRIBUTES
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Brink Flair binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            BrinkBinarySensor(coordinator, _FILTER),
            BrinkBinarySensor(coordinator, _OUTPUT),
        ]
    )

    extension_group = ConditionalEntities(
        hass,
        async_add_entities,
        test=extension_connected,
        build=lambda: [
            BrinkBinarySensor(coordinator, d) for d in _extension_descriptions()
        ],
    )
    extension_group.async_update(coordinator.device)

    entry.async_on_unload(
        coordinator.async_add_listener(
            lambda: extension_group.async_update(coordinator.device)
        )
    )


class BrinkBinarySensor(BrinkEntity, BinarySensorEntity):
    """A boolean reading of one attribute of one component."""

    entity_description: BrinkBinarySensorDescription

    def __init__(
        self,
        coordinator: BrinkCoordinator,
        description: BrinkBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the tracked signal is active."""
        value = getattr(self._subsystem, self.entity_description.attribute)
        if value is None:
            return None
        return bool(value)
