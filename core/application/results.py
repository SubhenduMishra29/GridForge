# ============================================================
# File: core/application/results.py
# GridForge V2 — Headless Application Results
# ============================================================
"""
GridForge V2
============

Module:
    core.application.results

Purpose
-------
Defines the structured result contract used by the GridForge V2
Headless Application layer.

Application operations must not return UI-specific objects,
Qt objects, widgets, graphics items, or presentation state.

Instead, successful Application operations return an
ApplicationResult containing:

    * success state;
    * optional result value;
    * optional structured metadata.

Architectural Boundary
----------------------
The dependency direction is:

    UI / Plugins
          |
          v
    core.application
          |
          v
    Core Domain / Network / Analysis

This module therefore has no dependency on:

    * PySide6;
    * PyQt;
    * Qt;
    * UI;
    * SLD;
    * canvas;
    * renderers;
    * UI controllers;
    * plugin implementations.

Result objects are immutable.

The Application layer owns the structure of the result, while
the contained ``value`` remains owned by the operation that
produced it.

Design Principle
----------------
The result contract must remain deliberately small.

It must NOT become:

    * a second domain model;
    * a UI state container;
    * a serialization framework;
    * a logging mechanism;
    * an event bus.

The result communicates the outcome of one Application operation.

Typical usage
-------------
A successful operation may return:

    ApplicationResult.success(
        value=created_bus,
        message="Bus created.",
    )

An operation that completed successfully but has no meaningful
return object may return:

    ApplicationResult.success(
        message="Operation completed.",
    )

For operations where the caller needs structured information:

    ApplicationResult.success(
        value={"element_id": element_id},
        metadata={"operation": "create"},
    )

Failure handling
----------------
Expected failures are represented by the Application error
contract in ``core.application.errors``.

A successful ``ApplicationResult`` therefore represents only
successful execution.

Unexpected Python exceptions must not be silently converted
into successful results.

Result semantics
----------------
``success``:
    Indicates successful Application execution.

``value``:
    Optional operation-specific return value.

``message``:
    Optional human-readable outcome description.

``metadata``:
    Optional structured information associated with the result.

No UI assumptions are made about any of these fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class ApplicationResult[T]:
    """
    Immutable result returned by a successful Application operation.

    Parameters
    ----------
    value:
        Optional operation-specific result.

    message:
        Optional human-readable description of the successful
        operation.

    metadata:
        Optional structured metadata associated with the result.

    Notes
    -----
    ``ApplicationResult`` deliberately does not contain an error
    field.

    Expected failures belong to ``ApplicationError`` and its
    subclasses.

    This keeps success and failure semantics explicit rather than
    creating an ambiguous result object that can simultaneously
    represent success and failure.
    """

    value: T | None = None
    message: str | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate the structural integrity of the result."""

        if self.message is not None and not isinstance(
            self.message,
            str,
        ):
            raise ValueError(
                "ApplicationResult message must be a string or None."
            )

        if self.metadata is not None and not isinstance(
            self.metadata,
            Mapping,
        ):
            raise ValueError(
                "ApplicationResult metadata must be a mapping or None."
            )

    @classmethod
    def success(
        cls,
        value: T | None = None,
        *,
        message: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ApplicationResult[T]:
        """
        Construct a successful Application result.

        Parameters
        ----------
        value:
            Optional value produced by the operation.

        message:
            Optional human-readable success message.

        metadata:
            Optional structured operation metadata.

        Returns
        -------
        ApplicationResult[T]
            Immutable successful result.
        """
        return cls(
            value=value,
            message=message,
            metadata=metadata,
        )

    def has_value(self) -> bool:
        """
        Return whether the result contains a non-None value.

        This is a convenience query only.

        ``None`` is a valid operation result, so callers should not
        interpret the absence of a value as a failed operation.
        """
        return self.value is not None

    def get(
        self,
        default: T | None = None,
    ) -> T | None:
        """
        Return the contained value.

        Parameters
        ----------
        default:
            Value returned when ``value`` is ``None``.

        Returns
        -------
        T | None
            The operation result value or the supplied default.
        """
        if self.value is None:
            return default

        return self.value


__all__ = [
    "ApplicationResult",
]
