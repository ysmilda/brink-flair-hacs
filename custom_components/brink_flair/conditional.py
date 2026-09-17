"""Dynamic entities that exist only while their optional hardware is connected.

The optional accessories of a Flair unit (CO2 sensors, extension module,
dwelling-temperature probe) advertise their presence through specific registers.
The platforms poll that state through the coordinator and reconcile their live
entity set on every update: entities are added when the hardware reports in and
removed again — registry entry included — when it drops out, so optional
sensors never linger in the UI as permanently unavailable.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from brink_flair_modbus import Co2SensorStatus

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

#: CO2 sensor states that prove the sensor is connected to the unit.
_CO2_CONNECTED = frozenset(
    {
        Co2SensorStatus.IDLE,
        Co2SensorStatus.WARMING_UP,
        Co2SensorStatus.RUNNING,
        Co2SensorStatus.CALIBRATING,
        Co2SensorStatus.SELF_TEST,
    }
)


def co2_connected(device: Any, sensor_n: int) -> bool:
    """Return whether CO2 sensor slot ``sensor_n`` reports a connected state."""
    return getattr(device.status, f"co2_{sensor_n}_status") in _CO2_CONNECTED


def extension_connected(device: Any) -> bool:
    """Return whether an extension module is present."""
    return bool(device.info.extension_device_type)


def dwelling_connected(device: Any) -> bool:
    """Return whether the dwelling temperature probe reports a reading."""
    return device.measurements.dwelling_temperature is not None


@callback
def _remove_entity(hass: HomeAssistant, entity: Entity) -> None:
    """Fully remove an entity and its registry entry."""
    registry = er.async_get(hass)
    if (entry := entity.registry_entry) is not None and registry.async_get(
        entry.entity_id
    ):
        registry.async_remove(entry.entity_id)
    if entity.platform is not None:
        hass.async_create_task(entity.async_remove(force_remove=True))


class ConditionalEntities:
    """Adds and removes a group of entities as their hardware connects.

    Each instance covers one atomic group: either every entity it builds is live
    or none. ``async_update`` is meant to be called from the coordinator's
    update listener (and once after platform setup) with the current device.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        async_add_entities: AddConfigEntryEntitiesCallback,
        *,
        test: Callable[[Any], bool],
        build: Callable[[], Sequence[Entity]],
    ) -> None:
        self._hass = hass
        self._async_add_entities = async_add_entities
        self._test = test
        self._build = build
        self._live: dict[str, Entity] = {}

    @callback
    def async_update(self, device: Any) -> None:
        """Reconcile the live entities with the current connection state."""
        if not self._live and self._test(device):
            entities = {entity.unique_id: entity for entity in self._build()}
            self._live = entities
            self._async_add_entities(list(entities.values()))
        elif self._live and not self._test(device):
            entities = self._live
            self._live = {}
            for entity in entities.values():
                _remove_entity(self._hass, entity)
