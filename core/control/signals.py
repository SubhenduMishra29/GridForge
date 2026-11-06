"""
GridForge V2 - Control Signal Runtime Contracts
================================================

Author:
    Subhendu Mishra

File:
    core/control/signals.py

Purpose
-------
Defines runtime signal containers for the Control domain.

The Control domain has two branches:

    Dynamic Control
        AVR, Governor, PSS, inverter controllers, plant controllers, etc.

    Logic Control
        Contacts, coils, gates, timers, latches, interlocks,
        sequences, comparators, and related discrete control.

This module provides the runtime signal boundary shared by both.

Architectural Rules
-------------------
1. SignalSet contains signal values, not electrical/network truth.
2. SignalSet does not query Core Model or Network.
3. SignalSet does not execute control equations.
4. SignalSet does not perform numerical integration.
5. SignalSet does not import plugins.
6. Signal definitions come from core.control.base.
7. Signal ordering is deterministic.
8. Boolean values remain Boolean.
9. Numeric values must be finite.
10. SignalSet is a value-transfer object between Control components
    and the surrounding application/simulation layer.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
import math
from typing import Sequence

from .base import (
    ControlInputError,
    ControlOutputError,
    ControlSignal,
    SignalRole,
    SignalValue,
)


# ============================================================================
# ERRORS
# ============================================================================


class SignalError(ValueError):
    """Base exception for runtime signal errors."""


class SignalNameError(SignalError):
    """Raised when a signal name is invalid or unknown."""


class SignalValueError(SignalError):
    """Raised when a signal value is invalid."""


class SignalDefinitionError(SignalError):
    """Raised when signal definitions are invalid."""


# ============================================================================
# RUNTIME SIGNAL VALUE
# ============================================================================


@dataclass(frozen=True)
class ControlSignalValue:
    """
    Runtime value of one Control signal.

    Parameters
    ----------
    definition:
        Authoritative signal definition.

    value:
        Current runtime value.

    Notes
    -----
    This object contains a value and its definition.

    It does not represent ownership of the underlying engineering
    quantity. For example, a ``Vt`` signal may originate from a
    machine/network calculation, but SignalValue merely transports
    the already-resolved value into Control.
    """

    definition: ControlSignal
    value: SignalValue

    def __post_init__(self) -> None:
        if not isinstance(
            self.definition,
            ControlSignal,
        ):
            raise SignalDefinitionError(
                "definition must be a ControlSignal."
            )

        _validate_signal_value(
            self.definition,
            self.value,
        )

    @property
    def name(self) -> str:
        """Return the signal name."""

        return self.definition.name

    @property
    def role(self) -> SignalRole:
        """Return the signal semantic role."""

        return self.definition.role

    @property
    def unit(self) -> str:
        """Return the engineering unit."""

        return self.definition.unit


# ============================================================================
# SIGNAL SET
# ============================================================================


class SignalSet(Mapping[str, SignalValue]):
    """
    Deterministic runtime collection of Control signals.

    SignalSet is intentionally read-only after construction.

    Example
    -------
    Dynamic control:

        signals = SignalSet(
            definitions=[
                ControlSignal(
                    "Vt",
                    role=SignalRole.MEASUREMENT,
                    unit="pu",
                ),
                ControlSignal(
                    "Vref",
                    role=SignalRole.REFERENCE,
                    unit="pu",
                ),
            ],
            values={
                "Vt": 1.02,
                "Vref": 1.00,
            },
        )

    Logic control:

        signals = SignalSet(
            definitions=[
                ControlSignal(
                    "breaker_closed",
                    role=SignalRole.STATUS,
                    value_type=bool,
                ),
                ControlSignal(
                    "trip",
                    role=SignalRole.COMMAND,
                    value_type=bool,
                ),
            ],
            values={
                "breaker_closed": True,
                "trip": False,
            },
        )
    """

    __slots__ = (
        "_definitions",
        "_values",
        "_index",
    )

    def __init__(
        self,
        definitions: Sequence[ControlSignal] = (),
        values: Mapping[str, SignalValue] | None = None,
        *,
        allow_optional_missing: bool = False,
    ) -> None:
        definitions = tuple(definitions)

        self._validate_definitions(
            definitions
        )

        self._definitions = definitions

        self._index = {
            signal.name: index
            for index, signal
            in enumerate(definitions)
        }

        supplied = {
            str(name): value
            for name, value
            in dict(values or {}).items()
        }

        expected = set(
            self._index
        )

        actual = set(
            supplied
        )

        unknown = actual - expected

        if unknown:
            raise SignalNameError(
                "Unknown signals: "
                f"{sorted(unknown)}"
            )

        if allow_optional_missing:
            missing = {
                signal.name
                for signal in definitions
                if signal.required
            } - actual
        else:
            missing = expected - actual

        if missing:
            raise SignalValueError(
                "Missing signals: "
                f"{sorted(missing)}"
            )

        normalized: dict[str, SignalValue] = {}

        for signal in definitions:
            if signal.name not in supplied:
                continue

            value = supplied[
                signal.name
            ]

            _validate_signal_value(
                signal,
                value,
            )

            normalized[
                signal.name
            ] = value

        self._values = normalized

    # ========================================================================
    # MAPPING INTERFACE
    # ========================================================================

    def __getitem__(
        self,
        name: str,
    ) -> SignalValue:
        try:
            return self._values[name]
        except KeyError as exc:
            raise SignalNameError(
                f"Unknown signal '{name}'."
            ) from exc

    def __iter__(self) -> Iterator[str]:
        return iter(
            signal.name
            for signal in self._definitions
            if signal.name in self._values
        )

    def __len__(self) -> int:
        return len(
            self._values
        )

    # ========================================================================
    # DEFINITIONS
    # ========================================================================

    @property
    def definitions(
        self,
    ) -> tuple[ControlSignal, ...]:
        """
        Return all signal definitions in authoritative order.
        """

        return self._definitions

    @property
    def names(
        self,
    ) -> tuple[str, ...]:
        """
        Return names of currently supplied signals in definition order.
        """

        return tuple(
            signal.name
            for signal in self._definitions
            if signal.name in self._values
        )

    @property
    def all_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return names of all defined signals.
        """

        return tuple(
            signal.name
            for signal in self._definitions
        )

    @property
    def size(
        self,
    ) -> int:
        """Return number of currently supplied signals."""

        return len(
            self._values
        )

    # ========================================================================
    # SIGNAL ACCESS
    # ========================================================================

    def get_value(
        self,
        name: str,
        default: SignalValue | None = None,
    ) -> SignalValue | None:
        """
        Return a signal value or a default.
        """

        return self._values.get(
            name,
            default,
        )

    def contains(
        self,
        name: str,
    ) -> bool:
        """
        Return True when a runtime value is present.
        """

        return name in self._values

    def definition(
        self,
        name: str,
    ) -> ControlSignal:
        """
        Return the definition for a named signal.
        """

        try:
            return self._definitions[
                self._index[name]
            ]
        except KeyError as exc:
            raise SignalNameError(
                f"Unknown signal '{name}'."
            ) from exc

    def value(
        self,
        name: str,
    ) -> ControlSignalValue:
        """
        Return a runtime signal-value object.
        """

        definition = self.definition(
            name
        )

        if name not in self._values:
            raise SignalValueError(
                f"Signal '{name}' has no runtime value."
            )

        return ControlSignalValue(
            definition=definition,
            value=self._values[name],
        )

    def values(
        self,
    ) -> dict[str, SignalValue]:
        """
        Return a detached mapping of runtime values.
        """

        return dict(
            self._values
        )

    # ========================================================================
    # ROLE FILTERING
    # ========================================================================

    def by_role(
        self,
        role: SignalRole,
    ) -> dict[str, SignalValue]:
        """
        Return all supplied signals matching a semantic role.
        """

        if not isinstance(
            role,
            SignalRole,
        ):
            role = SignalRole(role)

        return {
            signal.name: self._values[
                signal.name
            ]
            for signal in self._definitions
            if signal.name in self._values
            and signal.role is role
        }

    def measurements(
        self,
    ) -> dict[str, SignalValue]:
        """Return measurement signals."""

        return self.by_role(
            SignalRole.MEASUREMENT
        )

    def references(
        self,
    ) -> dict[str, SignalValue]:
        """Return reference signals."""

        return self.by_role(
            SignalRole.REFERENCE
        )

    def feedback(
        self,
    ) -> dict[str, SignalValue]:
        """Return feedback signals."""

        return self.by_role(
            SignalRole.FEEDBACK
        )

    def commands(
        self,
    ) -> dict[str, SignalValue]:
        """Return command signals."""

        return self.by_role(
            SignalRole.COMMAND
        )

    def statuses(
        self,
    ) -> dict[str, SignalValue]:
        """Return status signals."""

        return self.by_role(
            SignalRole.STATUS
        )

    # ========================================================================
    # VALUE TRANSFORMATION
    # ========================================================================

    def with_values(
        self,
        values: Mapping[str, SignalValue],
        *,
        allow_optional_missing: bool = True,
    ) -> "SignalSet":
        """
        Return a new SignalSet with selected values replaced or added.

        The existing SignalSet is never mutated.
        """

        merged = self.values()
        merged.update(
            {
                str(name): value
                for name, value in values.items()
            }
        )

        return SignalSet(
            definitions=self._definitions,
            values=merged,
            allow_optional_missing=allow_optional_missing,
        )

    def subset(
        self,
        names: Sequence[str],
    ) -> "SignalSet":
        """
        Return a SignalSet containing the requested runtime signals.

        The returned definitions retain their original ordering.
        """

        requested = {
            str(name)
            for name in names
        }

        unknown = requested - set(
            self._values
        )

        if unknown:
            raise SignalNameError(
                "Cannot create signal subset; "
                f"unknown signals: {sorted(unknown)}"
            )

        definitions = tuple(
            signal
            for signal in self._definitions
            if signal.name in requested
        )

        values = {
            signal.name: self._values[
                signal.name
            ]
            for signal in definitions
        }

        return SignalSet(
            definitions=definitions,
            values=values,
        )

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate(
        self,
        *,
        require_all: bool = True,
    ) -> None:
        """
        Validate all runtime values against their definitions.

        Parameters
        ----------
        require_all:
            If True, every required/defined signal must have a value.
        """

        expected = set(
            self._index
        )

        actual = set(
            self._values
        )

        if require_all:
            missing = expected - actual

            if missing:
                raise SignalValueError(
                    "Missing signal values: "
                    f"{sorted(missing)}"
                )

        for signal in self._definitions:
            if signal.name not in self._values:
                continue

            _validate_signal_value(
                signal,
                self._values[
                    signal.name
                ],
            )

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(
        self,
    ) -> dict[str, SignalValue]:
        """
        Return runtime values in deterministic definition order.
        """

        return {
            signal.name: self._values[
                signal.name
            ]
            for signal in self._definitions
            if signal.name in self._values
        }

    def to_value_objects(
        self,
    ) -> tuple[ControlSignalValue, ...]:
        """
        Return runtime signal-value objects in definition order.
        """

        return tuple(
            ControlSignalValue(
                definition=signal,
                value=self._values[
                    signal.name
                ],
            )
            for signal in self._definitions
            if signal.name in self._values
        )

    # ========================================================================
    # REPRESENTATION
    # ========================================================================

    def __repr__(self) -> str:
        values = ", ".join(
            f"{name}={value!r}"
            for name, value
            in self._values.items()
        )

        return (
            f"SignalSet("
            f"{values})"
        )


# ============================================================================
# INPUT / OUTPUT HELPERS
# ============================================================================


def build_input_signals(
    definitions: Sequence[ControlSignal],
    values: Mapping[str, SignalValue],
) -> SignalSet:
    """
    Build and validate an input SignalSet.

    Intended for Control-component inputs.
    """

    signal_set = SignalSet(
        definitions=definitions,
        values=values,
    )

    _ensure_roles(
        definitions,
        allowed_roles={
            SignalRole.MEASUREMENT,
            SignalRole.REFERENCE,
            SignalRole.INPUT,
            SignalRole.FEEDBACK,
            SignalRole.STATUS,
        },
        error_type=ControlInputError,
    )

    return signal_set


def build_output_signals(
    definitions: Sequence[ControlSignal],
    values: Mapping[str, SignalValue],
) -> SignalSet:
    """
    Build and validate an output SignalSet.

    Intended for Control-component outputs.
    """

    signal_set = SignalSet(
        definitions=definitions,
        values=values,
    )

    _ensure_roles(
        definitions,
        allowed_roles={
            SignalRole.OUTPUT,
            SignalRole.COMMAND,
            SignalRole.STATUS,
            SignalRole.FEEDBACK,
        },
        error_type=ControlOutputError,
    )

    return signal_set


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def _validate_definitions(
    definitions: Sequence[ControlSignal],
) -> None:
    """
    Validate signal definitions.
    """

    names: list[str] = []

    for signal in definitions:
        if not isinstance(
            signal,
            ControlSignal,
        ):
            raise SignalDefinitionError(
                "All signal definitions must "
                "be ControlSignal instances."
            )

        if signal.name in names:
            raise SignalDefinitionError(
                "Duplicate signal name: "
                f"'{signal.name}'."
            )

        names.append(
            signal.name
        )


def _validate_signal_value(
    definition: ControlSignal,
    value: SignalValue,
) -> None:
    """
    Validate one runtime value against a signal definition.
    """

    expected = definition.value_type

    if expected is bool:
        if not isinstance(
            value,
            bool,
        ):
            raise SignalValueError(
                f"Signal '{definition.name}' "
                "must be Boolean."
            )

        return

    if expected is int:
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise SignalValueError(
                f"Signal '{definition.name}' "
                "must be an integer."
            )

        return

    if expected is float:
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise SignalValueError(
                f"Signal '{definition.name}' "
                "must be numeric."
            )

        if not math.isfinite(
            float(value)
        ):
            raise SignalValueError(
                f"Signal '{definition.name}' "
                "must be finite."
            )

        return

    raise SignalDefinitionError(
        f"Unsupported signal value type "
        f"for '{definition.name}'."
    )


def _ensure_roles(
    definitions: Sequence[ControlSignal],
    *,
    allowed_roles: set[SignalRole],
    error_type: type[Exception],
) -> None:
    """
    Validate that signal definitions use roles appropriate for the
    requested input/output boundary.
    """

    for signal in definitions:
        if signal.role not in allowed_roles:
            raise error_type(
                f"Signal '{signal.name}' uses role "
                f"'{signal.role.value}', which is not valid "
                "for this boundary."
            )


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "ControlSignalValue",
    "SignalSet",
    "SignalError",
    "SignalNameError",
    "SignalValueError",
    "SignalDefinitionError",
    "build_input_signals",
    "build_output_signals",
]
