"""Config flow for Brink Flair."""

from typing import Any, override
from urllib.parse import urlencode

from brink_flair_modbus import (
    SUPPORTED_MODELS,
    BrinkFlair,
    BrinkProbe,
    is_known_device_type,
    model_name_for_device_type,
)
from modbus_connection import ModbusError
import voluptuous as vol

from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
)
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
    CONF_MODEL,
    CONF_UNIT_ID,
    CONNECTION_SERIAL,
    CONNECTION_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DOMAIN,
)

_GITHUB_ISSUES_NEW = "https://github.com/ysmilda/brink-flair-modbus/issues/new"
_GITHUB_MAPPING_EDIT = (
    "https://github.com/ysmilda/brink-flair-modbus/edit/main/"
    "brink_flair_modbus/device_types.py"
)

def _unit_id_selector(default: int = DEFAULT_UNIT_ID) -> dict[str, Any]:
    """Return the Modbus unit field shared by every connection form."""
    return {
        vol.Required(CONF_UNIT_ID, default=default): NumberSelector(
            NumberSelectorConfig(min=1, max=255, step=1, mode=NumberSelectorMode.BOX)
        )
    }


# Shown only when register 4004 reports an unmapped device type.
STEP_MODEL = vol.Schema(
    {
        vol.Required(CONF_MODEL): SelectSelector(
            SelectSelectorConfig(
                options=[str(model) for model in SUPPORTED_MODELS],
                translation_key="model",
                mode=SelectSelectorMode.LIST,
            )
        )
    }
)


def _mapping_report_url(device_type: str) -> str:
    """Return a prefilled issue URL describing an unmapped device type."""
    params = {
        "title": f"Unmapped Brink Flair device type {device_type}",
        "body": (
            "Detected during setup:\n\n"
            f"- Device type (register 4004): `{device_type}`\n"
            "- Model: the one selected in the setup flow\n\n"
            "The mapping lives in "
            "`brink_flair_modbus/device_types.py`."
        ),
    }
    return f"{_GITHUB_ISSUES_NEW}?{urlencode(params)}"


def _discovered_placeholders(probe: BrinkProbe) -> dict[str, str]:
    """Build the placeholders for the device-discovery step description."""
    reported = str(probe.device_type) if probe.device_type is not None else "unknown"
    if is_known_device_type(probe.device_type):
        return {
            "model": model_name_for_device_type(probe.device_type),
            "device_type": reported,
            "model_help": "",
        }
    return {
        "model": "a Brink Flair unit",
        "device_type": reported,
        "model_help": (
            " This unit's device type isn't mapped to a model yet, so select its "
            "model below to set the correct airflow limits. You can also "
            f"[report this device type]({_mapping_report_url(reported)}) or "
            f"[open a pull request]({_GITHUB_MAPPING_EDIT}) to add the mapping."
        ),
    }


class BrinkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Brink Flair."""

    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._data: dict[str, Any] = {}
        self._probe: BrinkProbe | None = None

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user choose the transport the unit is reached through."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["modbus_tcp", "serial"],
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reconfigure the integration."""
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=["modbus_tcp", "serial"],
        )

    async def async_step_modbus_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a Modbus TCP connection."""
        errors: dict[str, str] = {}
        reconfigure_entry: ConfigEntry | None = None
        defaults: dict[str, Any] = {}
        if self.source == SOURCE_RECONFIGURE:
            reconfigure_entry = self._get_reconfigure_entry()
            defaults = {
                CONF_HOST: reconfigure_entry.data.get(CONF_HOST, ""),
                CONF_PORT: reconfigure_entry.data.get(CONF_PORT, DEFAULT_PORT),
                CONF_UNIT_ID: reconfigure_entry.data.get(
                    CONF_UNIT_ID, DEFAULT_UNIT_ID
                ),
            }
        if user_input is not None:
            data = {
                CONF_TYPE: CONNECTION_TCP,
                **user_input,
                CONF_UNIT_ID: int(user_input[CONF_UNIT_ID]),
            }
            if reconfigure_entry is not None:
                return await self._async_update_reconfigured_entry(
                    reconfigure_entry, data
                )
            await self._check_not_configured(data)
            probe = await self._async_probe(data)
            if probe is None:
                errors["base"] = "cannot_connect"
            else:
                return await self._async_complete(data, probe)
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
                vol.Required(
                    CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                **_unit_id_selector(defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)),
            }
        )
        return self.async_show_form(
            step_id="modbus_tcp", data_schema=schema, errors=errors
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a Modbus serial (RTU) connection, incl. network serial proxies."""
        errors: dict[str, str] = {}
        reconfigure_entry: ConfigEntry | None = None
        defaults: dict[str, Any] = {}
        if self.source == SOURCE_RECONFIGURE:
            reconfigure_entry = self._get_reconfigure_entry()
            defaults = {
                CONF_DEVICE: reconfigure_entry.data.get(CONF_DEVICE, ""),
                CONF_BAUDRATE: reconfigure_entry.data.get(
                    CONF_BAUDRATE, DEFAULT_BAUDRATE
                ),
                CONF_UNIT_ID: reconfigure_entry.data.get(
                    CONF_UNIT_ID, DEFAULT_UNIT_ID
                ),
            }
        if user_input is not None:
            data = {
                CONF_TYPE: CONNECTION_SERIAL,
                **user_input,
                CONF_UNIT_ID: int(user_input[CONF_UNIT_ID]),
            }
            if reconfigure_entry is not None:
                return await self._async_update_reconfigured_entry(
                    reconfigure_entry, data
                )
            await self._check_not_configured(data)
            probe = await self._async_probe(data)
            if probe is None:
                errors["base"] = "device_not_found"
            else:
                return await self._async_complete(data, probe)
        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE, default=defaults.get(CONF_DEVICE, "")): (
                    SerialPortSelector()
                ),
                vol.Required(
                    CONF_BAUDRATE, default=defaults.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                **_unit_id_selector(defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)),
            }
        )
        return self.async_show_form(
            step_id="serial", data_schema=schema, errors=errors
        )

    async def async_step_discovered(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the discovered unit, asking for a model when the type is unmapped."""
        errors: dict[str, str] = {}
        probe = self._probe
        assert probe is not None
        if user_input is not None:
            data = {**self._data}
            if is_known_device_type(probe.device_type):
                return self.async_create_entry(
                    title=model_name_for_device_type(probe.device_type), data=data
                )
            try:
                model = int(user_input[CONF_MODEL])
            except TypeError, ValueError:
                errors["base"] = "invalid_model"
            else:
                data[CONF_MODEL] = model
                return self.async_create_entry(
                    title=f"Brink Flair {model}", data=data
                )
        schema = (
            STEP_MODEL
            if not is_known_device_type(probe.device_type)
            else vol.Schema({})
        )
        return self.async_show_form(
            step_id="discovered",
            data_schema=schema,
            errors=errors,
            description_placeholders=_discovered_placeholders(probe),
        )

    async def _check_not_configured(self, data: dict[str, Any]) -> None:
        """Abort if this transport + unit already has an entry."""
        params = params_from_data(data)
        # Endpoint identifies the device: transport, address, and TCP port.
        endpoint = "-".join(str(part) for part in params.endpoint)
        await self.async_set_unique_id(f"{endpoint}_{data[CONF_UNIT_ID]}")
        self._abort_if_unique_id_configured()

    async def _async_update_reconfigured_entry(
        self, entry: ConfigEntry, data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Update a reconfigured entry, aborting if it duplicates another entry."""
        endpoint = "-".join(str(part) for part in params_from_data(data).endpoint)
        new_unique_id = f"{endpoint}_{data[CONF_UNIT_ID]}"
        await self.async_set_unique_id(new_unique_id)
        existing = self.hass.config_entries.async_entry_for_domain_unique_id(
            self.handler, new_unique_id
        )
        if existing is not None and existing.entry_id != entry.entry_id:
            return self.async_abort(reason="already_configured")
        return self.async_update_reload_and_abort(
            entry=entry, data={**entry.data, **data}, unique_id=new_unique_id
        )

    async def _async_probe(self, data: dict[str, Any]) -> BrinkProbe | None:
        """Read the identity register through a temporary connection."""
        try:
            async with async_get_temporary_unit(
                self.hass, params_from_data(data), data[CONF_UNIT_ID]
            ) as unit:
                probe = await BrinkFlair.async_probe(unit)
        except ModbusError, OSError, ValueError, HomeAssistantError:
            return None
        # No code read means unreachable unit (wrong address, flaky link).
        if probe.device_type is None:
            return None
        return probe

    async def _async_complete(
        self, data: dict[str, Any], probe: BrinkProbe
    ) -> ConfigFlowResult:
        """Store the probe and let the user confirm the discovered device."""
        self._data = data
        self._probe = probe
        return await self.async_step_discovered()
