"""Brink Flair over Modbus.

Borrows a ``ModbusUnit`` from the ``modbus`` integration (which owns the shared
connection), hands it to the ``brink_flair_modbus`` library, and reloads when
the connection drops so a fresh unit is borrowed on the rebuilt link.
"""

from brink_flair_modbus import BrinkFlair

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .connection import params_from_data
from .const import CONF_MODEL, CONF_UNIT_ID
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
    """Set up Brink Flair from a config entry."""
    unit = async_get_unit(
        hass, entry, params_from_data(entry.data), int(entry.data[CONF_UNIT_ID])
    )
    device = BrinkFlair(unit, model_override=entry.data.get(CONF_MODEL))
    coordinator = BrinkCoordinator(hass, entry, device)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # Reload on connection loss so a fresh unit is borrowed from modbus.
    entry.async_on_unload(
        unit.on_connection_lost(
            lambda: hass.config_entries.async_schedule_reload(entry.entry_id)
        )
    )

    # Adopt an interval changed through the options flow without reloading.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: BrinkConfigEntry) -> None:
    """Apply the polling interval whenever the config entry is updated."""
    entry.runtime_data.apply_options()


async def async_unload_entry(hass: HomeAssistant, entry: BrinkConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
