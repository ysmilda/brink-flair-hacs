"""Constants for the Brink Flair integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "brink_flair"

CONF_UNIT_ID: Final = "unit_id"
DEFAULT_UNIT_ID: Final = 20  # the unit's default Modbus station address

# Transport selection (stored under homeassistant.const.CONF_TYPE).
CONNECTION_TCP: Final = "tcp"
CONNECTION_SERIAL: Final = "serial"

# Serial-only options.
CONF_BAUDRATE: Final = "baudrate"
CONF_BYTESIZE: Final = "bytesize"
CONF_PARITY: Final = "parity"
CONF_STOPBITS: Final = "stopbits"

DEFAULT_PORT: Final = 502
DEFAULT_BAUDRATE: Final = 19200  # the unit's factory line setting
DEFAULT_BYTESIZE: Final = 8
DEFAULT_PARITY: Final = "e"  # even parity, stored lowercase from the form
DEFAULT_STOPBITS: Final = 1

# A ventilation unit changes slowly, but we poll aggressively and fixed.
SCAN_INTERVAL: Final = timedelta(seconds=30)
