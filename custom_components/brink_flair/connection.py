"""Turn a config entry's transport fields into a Modbus params object."""

from collections.abc import Mapping
from typing import Any

from modbus_connection import ModbusSerialParams, ModbusTcpParams

from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT, CONF_TYPE

from .const import (
    CONF_BAUDRATE,
    CONF_PARITY,
    CONNECTION_SERIAL,
    DEFAULT_BAUDRATE,
    DEFAULT_PARITY,
)


def params_from_data(data: Mapping[str, Any]) -> ModbusTcpParams | ModbusSerialParams:
    """Return the Modbus connection params described by ``data``.

    Only a serial link is parameterised by the unit's line settings; over TCP
    the gateway has already absorbed them. The fallbacks keep entries written
    before these fields existed usable.
    """
    if data[CONF_TYPE] == CONNECTION_SERIAL:
        return ModbusSerialParams(
            device=data[CONF_DEVICE],
            baudrate=data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
            bytesize=8,
            parity=data.get(CONF_PARITY, DEFAULT_PARITY),
            stopbits=1,
            framer="rtu",
        )
    return ModbusTcpParams(host=data[CONF_HOST], port=data[CONF_PORT])
