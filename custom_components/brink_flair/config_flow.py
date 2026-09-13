"""Config flow for Brink Flair."""

from typing import Any, override

from brink_flair_modbus import BrinkFlair
from modbus_connection import ModbusError
import voluptuous as vol

from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SerialPortSelector,
)

from .connection import params_from_data
from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_UNIT_ID,
    CONNECTION_SERIAL,
    CONNECTION_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_PORT,
    DEFAULT_STOPBITS,
    DEFAULT_UNIT_ID,
    DOMAIN,
)

_UNIT_ID = {
    vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): NumberSelector(
        NumberSelectorConfig(min=1, max=255, step=1, mode=NumberSelectorMode.BOX)
    )
}

STEP_MODBUS_TCP = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        **_UNIT_ID,
    }
)

# SerialPortSelector lists local serial ports and network serial proxies, so a
# Brink Flair behind an ESPHome serial proxy is reachable here too.
STEP_SERIAL = vol.Schema(
    {
        vol.Required(CONF_DEVICE): SerialPortSelector(),
        vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
        vol.Required(CONF_PARITY, default=DEFAULT_PARITY): SelectSelector(
            SelectSelectorConfig(
                options=["n", "e", "o"],
                translation_key="parity",
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_STOPBITS, default=DEFAULT_STOPBITS): vol.In([1, 2]),
        vol.Required(CONF_BYTESIZE, default=DEFAULT_BYTESIZE): vol.In([7, 8]),
        **_UNIT_ID,
    }
)


class BrinkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Brink Flair."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user choose the transport the unit is reached through."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["modbus_tcp", "serial"],
        )

    async def async_step_modbus_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a Modbus TCP connection."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                CONF_TYPE: CONNECTION_TCP,
                **user_input,
                CONF_UNIT_ID: int(user_input[CONF_UNIT_ID]),
            }
            await self._check_not_configured(data)
            if (title := await self._async_title(data)) is None:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=title, data=data)
        return self.async_show_form(
            step_id="modbus_tcp", data_schema=STEP_MODBUS_TCP, errors=errors
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a Modbus serial (RTU) connection, incl. network serial proxies."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                CONF_TYPE: CONNECTION_SERIAL,
                **user_input,
                # Store the uppercase parity code the connection expects.
                CONF_PARITY: user_input[CONF_PARITY].upper(),
                CONF_UNIT_ID: int(user_input[CONF_UNIT_ID]),
            }
            await self._check_not_configured(data)
            if (title := await self._async_title(data)) is None:
                errors["base"] = "cannot_open_serial_port"
            else:
                return self.async_create_entry(title=title, data=data)
        return self.async_show_form(
            step_id="serial", data_schema=STEP_SERIAL, errors=errors
        )

    async def _check_not_configured(self, data: dict[str, Any]) -> None:
        """Abort if this transport + unit already has an entry."""
        params = params_from_data(data)
        await self.async_set_unique_id(f"{params.endpoint[1]}_{data[CONF_UNIT_ID]}")
        self._abort_if_unique_id_configured()

    async def _async_title(self, data: dict[str, Any]) -> str | None:
        """Read the unit model for the entry title, or None if unreachable."""
        try:
            async with async_get_temporary_unit(
                self.hass, params_from_data(data), data[CONF_UNIT_ID]
            ) as unit:
                device = BrinkFlair(unit)
                await device.info.async_update()
        except (ModbusError, OSError, ValueError, HomeAssistantError):
            return None
        return device.info.model
