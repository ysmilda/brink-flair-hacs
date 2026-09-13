"""Brink-specific field factories layered on ``modbus_connection.model``."""

from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from typing import Any

from modbus_connection.model import (
    Component,
    PackedBitField,
    bit as _modbus_bit,
    boolean as _modbus_boolean,
    enum as _modbus_enum,
    gauge as _modbus_gauge,
    integer as _modbus_integer,
    uint32 as _modbus_uint32,
)

from .exceptions import BrinkValueValidationError
from .metadata import (
    BooleanMetadata,
    DatapointMetadata,
    EnumMetadata,
    NumberMetadata,
    OptionMetadata,
    attach_metadata,
    step_from_digits,
)

NAN_INT16 = 0x7FFF  # the value the unit returns for an absent sensor


def _number_validator(
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> Callable[[Any], Any]:
    """Return a write validator enforcing the documented value range."""

    def validate(value: Any) -> Any:
        number = float(value)
        if min_value is not None and number < min_value:
            raise BrinkValueValidationError(
                f"Value {value} is below minimum {min_value}"
            )
        if max_value is not None and number > max_value:
            raise BrinkValueValidationError(
                f"Value {value} is above maximum {max_value}"
            )
        return value

    return validate


def _with_number_validator(
    writable: bool | Callable[[Any], Any],
    *,
    min_value: float | None,
    max_value: float | None,
) -> bool | Callable[[Any], Any]:
    """Return ``writable`` or a range-checking validator if bounds are set."""
    if not writable:
        return False
    if callable(writable):
        return writable
    if min_value is None and max_value is None:
        return True
    return _number_validator(min_value=min_value, max_value=max_value)


def _enum_validator(enum_type: type[IntEnum]) -> Callable[[Any], Any]:
    """Return a write validator coercing to a known enum member."""

    def validate(value: Any) -> Any:
        try:
            return enum_type(value)
        except (TypeError, ValueError) as err:
            raise BrinkValueValidationError(
                f"{value!r} is not valid for {enum_type.__name__}"
            ) from err

    return validate


def _with_enum_validator(
    writable: bool | Callable[[Any], Any],
    enum_type: type[IntEnum],
) -> bool | Callable[[Any], Any]:
    """Return ``writable`` or an enum-coercing validator."""
    if not writable:
        return False
    if callable(writable):
        return writable
    return _enum_validator(enum_type)


def integer(
    address: int,
    *,
    signed: bool = True,
    nan: int | None = None,
    stride: int = 0,
    writable: bool | Callable[[Any], Any] = False,
    unit: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float | None = None,
    digits: int | None = None,
    description: str | None = None,
    **kwargs: Any,
):
    """Create an integer field at a protocol register address."""
    effective_step = step if step is not None else step_from_digits(digits)
    effective_writable = _with_number_validator(
        writable,
        min_value=min_value,
        max_value=max_value,
    )
    field = _modbus_integer(
        address,
        signed=signed,
        nan=nan,
        stride=stride,
        writable=effective_writable,
        unit=unit,
        **kwargs,
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            description=description,
            writable=bool(writable),
            number=NumberMetadata(
                min_value=min_value,
                max_value=max_value,
                step=effective_step,
                digits=digits,
                unit=unit,
            ),
        ),
    )


def gauge(
    address: int,
    scale: float,
    *,
    signed: bool = True,
    nan: int | None = None,
    stride: int = 0,
    writable: bool | Callable[[Any], Any] = False,
    unit: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float | None = None,
    digits: int | None = None,
    description: str | None = None,
    **kwargs: Any,
):
    """Create a scaled numeric field at a protocol register address."""
    effective_step = step if step is not None else step_from_digits(digits)
    effective_writable = _with_number_validator(
        writable,
        min_value=min_value,
        max_value=max_value,
    )
    field = _modbus_gauge(
        address,
        scale,
        signed=signed,
        nan=nan,
        stride=stride,
        writable=effective_writable,
        unit=unit,
        **kwargs,
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            description=description,
            writable=bool(writable),
            number=NumberMetadata(
                min_value=min_value,
                max_value=max_value,
                step=effective_step,
                digits=digits,
                unit=unit,
            ),
        ),
    )


def enum(
    address: int,
    enum_type: type[IntEnum],
    *,
    options: tuple[OptionMetadata, ...] | None = None,
    writable: bool | Callable[[Any], Any] = False,
    description: str | None = None,
    **kwargs: Any,
):
    """Create an enum field at a protocol register address."""
    effective_writable = _with_enum_validator(writable, enum_type)
    field = _modbus_enum(
        address,
        enum_type,
        writable=effective_writable,
        **kwargs,
    )
    resolved_options = options or tuple(
        OptionMetadata(member.name.lower(), int(member), member.name)
        for member in enum_type
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="enum",
            description=description,
            writable=bool(writable),
            enum=EnumMetadata(enum_type=enum_type, options=resolved_options),
        ),
    )


def boolean(
    address: int,
    *,
    writable: bool | Callable[[Any], Any] = False,
    description: str | None = None,
    **kwargs: Any,
):
    """Create a 0/1 register field decoding to ``bool``."""
    field = _modbus_boolean(
        address,
        writable=writable,
        **kwargs,
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="boolean",
            description=description,
            writable=bool(writable),
            boolean=BooleanMetadata(),
        ),
    )


def uint32(
    address: int,
    *,
    unit: str | None = None,
    description: str | None = None,
    **kwargs: Any,
):
    """Create a 32-bit unsigned counter field at a protocol address."""
    field = _modbus_uint32(
        address,
        unit=unit,
        **kwargs,
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            description=description,
            writable=False,
            number=NumberMetadata(unit=unit, min_value=0),
        ),
    )


def bit(
    address: int,
    index: int,
    *,
    writable: bool | Callable[[Any], Any] = False,
    description: str | None = None,
    **kwargs: Any,
) -> PackedBitField:
    """Create one bit of a register as ``bool``."""
    field = _modbus_bit(
        address,
        index,
        writable=writable,
        **kwargs,
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="boolean",
            description=description,
            writable=bool(writable),
            boolean=BooleanMetadata(),
        ),
    )


class BrinkComponent(Component):
    """A Brink Flair sub-system: typed fields over readable register ranges."""

    def metadata_for(self, field: str) -> DatapointMetadata | None:
        """Return neutral metadata for a declared field."""
        descriptor = type(self).declared_fields.get(field)
        if descriptor is None:
            return None
        return getattr(descriptor, "brink_metadata", None)

    def require_metadata_for(self, field: str) -> DatapointMetadata:
        """Return metadata for a field or raise."""
        metadata = self.metadata_for(field)
        if metadata is None:
            raise AttributeError(f"unknown or untyped Brink field {field!r}")
        return metadata
