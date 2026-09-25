"""Tests for turning a config entry's transport fields into Modbus params."""

from __future__ import annotations

from typing import Any

from modbus_connection import ModbusSerialParams, ModbusTcpParams

from custom_components.brink_flair.connection import params_from_data
from custom_components.brink_flair.const import (
    CONF_BAUDRATE,
    CONF_PARITY,
    CONF_UNIT_ID,
    CONNECTION_SERIAL,
    CONNECTION_TCP,
    DEFAULT_PARITY,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
)
from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT, CONF_TYPE


def test_tcp_params() -> None:
    """TCP data maps to ModbusTcpParams with the given host and port."""
    data: dict[str, Any] = {
        CONF_TYPE: CONNECTION_TCP,
        CONF_HOST: "192.168.1.5",
        CONF_PORT: 5020,
        CONF_UNIT_ID: DEFAULT_UNIT_ID,
    }
    params = params_from_data(data)
    assert isinstance(params, ModbusTcpParams)
    assert params.host == "192.168.1.5"
    assert params.port == 5020


def test_serial_params() -> None:
    """Serial data maps to ModbusSerialParams with the documented RS-485 line."""
    data: dict[str, Any] = {
        CONF_TYPE: CONNECTION_SERIAL,
        CONF_DEVICE: "/dev/ttyUSB0",
        CONF_BAUDRATE: 19200,
        CONF_UNIT_ID: DEFAULT_UNIT_ID,
    }
    params = params_from_data(data)
    assert isinstance(params, ModbusSerialParams)
    assert params.device == "/dev/ttyUSB0"
    assert params.baudrate == 19200
    assert params.bytesize == 8
    assert params.parity == "E"
    assert params.stopbits == 1
    assert params.framer == "rtu"


def test_serial_params_honour_configured_parity() -> None:
    """The unit's configured parity drives the serial port, not a hardcoded 'E'."""
    data: dict[str, Any] = {
        CONF_TYPE: CONNECTION_SERIAL,
        CONF_DEVICE: "/dev/ttyUSB0",
        CONF_BAUDRATE: 9600,
        CONF_PARITY: "O",
        CONF_UNIT_ID: DEFAULT_UNIT_ID,
    }
    params = params_from_data(data)
    assert isinstance(params, ModbusSerialParams)
    assert params.parity == "O"
    assert params.baudrate == 9600


def test_serial_params_fall_back_for_legacy_entries() -> None:
    """Entries written before the line settings existed still build valid params."""
    data: dict[str, Any] = {
        CONF_TYPE: CONNECTION_SERIAL,
        CONF_DEVICE: "/dev/ttyUSB0",
        CONF_BAUDRATE: 19200,
        CONF_UNIT_ID: DEFAULT_UNIT_ID,
    }
    params = params_from_data(data)
    assert isinstance(params, ModbusSerialParams)
    assert params.parity == DEFAULT_PARITY


def test_tcp_params_defaults_framer() -> None:
    """TCP data keeps the socket framer from the connection library."""
    data: dict[str, Any] = {
        CONF_TYPE: CONNECTION_TCP,
        CONF_HOST: "127.0.0.1",
        CONF_PORT: DEFAULT_PORT,
        CONF_UNIT_ID: DEFAULT_UNIT_ID,
    }
    params = params_from_data(data)
    assert isinstance(params, ModbusTcpParams)
    assert params.framer == "socket"
