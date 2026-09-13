"""Exceptions raised by the Brink Flair library."""

from __future__ import annotations


class BrinkValueValidationError(ValueError):
    """A value cannot be written because it is outside the documented limits."""
