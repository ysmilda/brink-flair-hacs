"""Neutral metadata for Brink Flair datapoints."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Literal

ValueKind = Literal["number", "enum", "boolean", "raw"]


@dataclass(frozen=True)
class NumberMetadata:
    """Metadata for a numeric Brink Flair value."""

    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None
    digits: int | None = None
    unit: str | None = None


@dataclass(frozen=True)
class OptionMetadata:
    """Metadata for one discrete option."""

    key: str
    value: int
    label: str | None = None


@dataclass(frozen=True)
class EnumMetadata:
    """Metadata for a selectable / discrete register value."""

    enum_type: type[IntEnum]
    options: tuple[OptionMetadata, ...]


@dataclass(frozen=True)
class BooleanMetadata:
    """Metadata for a boolean value."""

    false_key: str = "off"
    true_key: str = "on"
    false_label: str | None = None
    true_label: str | None = None
    inverted: bool = False


@dataclass(frozen=True)
class DatapointMetadata:
    """Neutral metadata for one Brink Flair datapoint."""

    value_kind: ValueKind
    description: str | None = None
    writable: bool = False
    number: NumberMetadata | None = None
    enum: EnumMetadata | None = None
    boolean: BooleanMetadata | None = None


def step_from_digits(digits: int | None) -> float | int | None:
    """Return the natural write/UI step from decimal precision."""

    if digits is None:
        return None
    if digits <= 0:
        return 1
    return 10**-digits


def attach_metadata[T](field: T, metadata: DatapointMetadata) -> T:
    """Attach Brink metadata to a modbus-connection field."""

    field.brink_metadata = metadata  # type: ignore[attr-defined]
    return field
