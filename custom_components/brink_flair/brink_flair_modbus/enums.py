"""Discrete values reported or accepted by a Brink Flair unit."""

from __future__ import annotations

from enum import IntEnum


class OperatingMode(IntEnum):
    """The ventilation unit's overall operating mode (input register 4020)."""

    STANDBY = 0
    BOOTLOADER = 1
    NON_BLOCKING_ERROR = 2
    BLOCKING_ERROR = 3
    MANUAL = 4
    HOLIDAY = 5
    NIGHT_VENTILATION = 6
    PARTY = 7
    BYPASS_BOOST = 8
    NORMAL_BOOST = 9
    AUTO_CO2 = 10
    AUTO_EBUS = 11
    AUTO_MODBUS = 12
    AUTO_LAN_WLAN_PORTAL = 13
    AUTO_LAN_WLAN_LOCAL = 14


class BypassStatus(IntEnum):
    """The heat-recovery bypass position (input register 4050)."""

    INITIALIZE = 0
    OPENING = 1
    CLOSING = 2
    OPEN = 3
    CLOSED = 4
    ERROR = 255


class FrostStatus(IntEnum):
    """The frost-protection state machine (input register 4070)."""

    INITIALIZE = 0
    POWERUP_DELAY = 1
    NO_FROST = 2
    NO_FROST_DELAY = 3
    FROST_CONTROL_START_DELAY = 4
    WAIT_FOR_ICING = 5
    ICE_DETECTED_DELAY = 6
    HEATING = 7
    WAIT_FOR_FREE_HEATER = 8
    FAN_CONTROL_START_DELAY = 9
    FAN_CONTROL_WAIT_DELAY = 10
    FAN_CONTROL = 11
    FAN_OFF_DELAY = 12
    FAN_OFF = 13
    FAN_RESTARTING = 14
    ERROR = 15
    TEST_MODUS = 16


class VentilationLevel(IntEnum):
    """The manual ventilation level (holding register 8001)."""

    ABSENCE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ControlMode(IntEnum):
    """The control mode (holding register 8000)."""

    OFF = 0
    STEP = 1
    FLOW = 2


class BypassMode(IntEnum):
    """The user-selected bypass state (holding register 6100)."""

    AUTO = 0
    CLOSED = 1
    OPEN = 2
