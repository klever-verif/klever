"""Common types for the framework."""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class SupportsCopy(Protocol):
    """Object that supports copying."""

    def copy(self) -> Self:
        """Return a copy of the object."""
        ...
