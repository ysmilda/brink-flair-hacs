"""The Brink Flair integration.

Brink Flair is a Modbus device. This integration does not own its connection:
it asks the ``modbus`` integration for a ``ModbusUnit`` on the transport and
unit described by its own config entry, then hands it to the
``brink_flair_modbus`` library. The ``modbus`` integration keeps the shared
connection open as long as a consumer holds a unit on it; this integration
reloads when the connection drops so it re-borrows a unit on the rebuilt
connection.
"""

from brink_flair_modbus import BrinkFlair

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .connection import params_from_data
from .const import CONF_UNIT_ID
from .coordinator import BrinkConfigEntry, BrinkCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: BrinkConfigEntry) -> bool:
    """Set up Brink Flair from a config entry.

    ``async_get_unit`` opens (or reuses) the shared Modbus connection these
    credentials describe and returns a unit bound to it. If the physical link
    is down, the coordinator's first refresh fails and Home Assistant retries
    setup.
    """
    unit = async_get_unit(
        hass, entry, params_from_data(entry.data), int(entry.data[CONF_UNIT_ID])
    )
    device = BrinkFlair(unit)
    coordinator = BrinkCoordinator(hass, entry, device)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # The borrowed unit is bound to the modbus connection that owns it. When
    # that connection drops, modbus rebuilds it; reload so we re-borrow a unit
    # on the fresh connection instead of holding a dead one.
    entry.async_on_unload(
        unit.on_connection_lost(
            lambda: hass.config_entries.async_schedule_reload(entry.entry_id)
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BrinkConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
