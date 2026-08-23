# core/model/breaker.py
"""
GridForge V2 Breaker Model
==========================

Author:
    Subhendu Mishra

A Breaker is a static two-terminal switching device.

Architecture
------------

    Breaker
       |
       +-- from_terminal
       +-- to_terminal
       |
       +-- closed
       +-- in_service
       +-- failed
       |
       +-- electrical ratings

The Breaker owns its local physical switching state and its
two electrical terminals.

It does NOT:

    - own global network topology
    - modify Bus objects
    - build Y-bus matrices
    - execute power-flow calculations
    - execute short-circuit studies
    - execute protection algorithms
    - decide when it should trip
    - schedule protection events
    - own SLD geometry
    - own GUI state

Protection/application layers issue commands to the Breaker.
The Breaker changes its local physical state.

State semantics
---------------

    in_service
        Equipment is available for operation.

    closed
        Main current path is physically closed.

    failed
        Breaker has a fault/failure condition.

These states are intentionally independent.

Terminal connectivity is separate from breaker switching state.

A Breaker may therefore exist in the model before it is connected
to network endpoints.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Breaker(ElectricalObject):
    """
    Two-terminal circuit breaker model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Initial from-side electrical endpoint.
        May be None.

    endpoint_to:
        Initial to-side electrical endpoint.
        May be None.

    name:
        Human-readable breaker name.

    rated_voltage_kv:
        Rated voltage in kV.

    rated_current_a:
        Continuous current rating in amperes.

    interrupting_capacity_ka:
        Symmetrical interrupting current rating in kA.

    short_time_withstand_ka:
        Short-time withstand current in kA.

    making_capacity_ka:
        Making current capacity in kA.

    opening_time_s:
        Mechanical/electrical opening time in seconds.

    closing_time_s:
        Mechanical/electrical closing time in seconds.

    Notes
    -----
    ``open()`` and ``close()`` modify only local breaker state.

    Network topology must interpret the resulting breaker state.
    """

    TYPE = "BREAKER"

    def __init__(
        self,
        id: str,
        endpoint_from=None,
        endpoint_to=None,
        *,
        name: str = "",
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        interrupting_capacity_ka: float | None = None,
        short_time_withstand_ka: float | None = None,
        making_capacity_ka: float | None = None,
        opening_time_s: float = 0.0,
        closing_time_s: float = 0.0,
        in_service: bool = True,
        closed: bool = True,
        failed: bool = False,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Authoritative physical terminals.
        #
        # These are created exactly once.
        # ---------------------------------------------------------

        self.from_terminal = Terminal(
            endpoint=endpoint_from,
            owner=self,
        )

        self.to_terminal = Terminal(
            endpoint=endpoint_to,
            owner=self,
        )

        # ---------------------------------------------------------
        # Operational state.
        # ---------------------------------------------------------

        self._in_service = bool(in_service)
        self._closed = bool(closed)
        self._failed = bool(failed)

        # ---------------------------------------------------------
        # Equipment ratings.
        # ---------------------------------------------------------

        self.rated_voltage_kv = (
            self._validate_optional_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.rated_current_a = (
            self._validate_optional_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

        self.interrupting_capacity_ka = (
            self._validate_optional_positive(
                interrupting_capacity_ka,
                "interrupting_capacity_ka",
            )
        )

        self.short_time_withstand_ka = (
            self._validate_optional_positive(
                short_time_withstand_ka,
                "short_time_withstand_ka",
            )
        )

        self.making_capacity_ka = (
            self._validate_optional_positive(
                making_capacity_ka,
                "making_capacity_ka",
            )
        )

        self.opening_time_s = self._validate_non_negative(
            opening_time_s,
            "opening_time_s",
        )

        self.closing_time_s = self._validate_non_negative(
            closing_time_s,
            "closing_time_s",
        )

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =============================================================
    # TERMINALS
    # =============================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """Return the two authoritative breaker terminals."""

        return (
            self.from_terminal,
            self.to_terminal,
        )

    @property
    def endpoint_from(self):
        """Return the from-side endpoint."""

        return self.from_terminal.endpoint

    @property
    def endpoint_to(self):
        """Return the to-side endpoint."""

        return self.to_terminal.endpoint

    @property
    def from_endpoint(self):
        """Compatibility alias for endpoint_from."""

        return self.endpoint_from

    @property
    def to_endpoint(self):
        """Compatibility alias for endpoint_to."""

        return self.endpoint_to

    @property
    def from_bus(self):
        """
        Return the bus derived from the from terminal.

        This is a compatibility accessor only.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the bus derived from the to terminal.

        This is a compatibility accessor only.
        """

        return self.to_terminal.bus

    @property
    def is_connected(self) -> bool:
        """
        Return True when both terminals have endpoints.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    @property
    def has_from_endpoint(self) -> bool:
        """Return whether the from terminal is connected."""

        return self.from_terminal.is_connected

    @property
    def has_to_endpoint(self) -> bool:
        """Return whether the to terminal is connected."""

        return self.to_terminal.is_connected

    # =============================================================
    # TERMINAL CONNECTION
    # =============================================================

    def connect_from(self, endpoint: Any) -> None:
        """
        Assign the from-side endpoint.

        This changes local terminal state only.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint: Any) -> None:
        """
        Assign the to-side endpoint.

        This changes local terminal state only.
        """

        self.to_terminal.connect(endpoint)

    def disconnect_from(self) -> None:
        """Remove the from-side endpoint."""

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """Remove the to-side endpoint."""

        self.to_terminal.disconnect()

    # =============================================================
    # BREAKER STATE
    # =============================================================

    @property
    def closed(self) -> bool:
        """
        Return the physical main-contact state.

        True:
            current path closed

        False:
            current path open
        """

        return self._closed

    @closed.setter
    def closed(self, value: bool) -> None:
        self._closed = bool(value)

    @property
    def is_closed(self) -> bool:
        """Return whether the breaker is physically closed."""

        return self._closed

    @property
    def is_open(self) -> bool:
        """Return whether the breaker is physically open."""

        return not self._closed

    @property
    def failed(self) -> bool:
        """Return whether the breaker is in a failed state."""

        return self._failed

    @failed.setter
    def failed(self, value: bool) -> None:
        self._failed = bool(value)

    @property
    def is_failed(self) -> bool:
        """Return whether the breaker has failed."""

        return self._failed

    @property
    def in_service(self) -> bool:
        """Return whether the breaker is in service."""

        return self._in_service

    @in_service.setter
    def in_service(self, value: bool) -> None:
        self._in_service = bool(value)

    @property
    def is_in_service(self) -> bool:
        """Return whether the breaker is in service."""

        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the breaker is out of service."""

        return not self._in_service

    # =============================================================
    # SWITCHING OPERATIONS
    # =============================================================

    def open(self) -> None:
        """
        Open the breaker.

        Only local physical state is changed.

        This method does not:

            - modify network topology
            - modify Bus objects
            - rebuild Y-bus
            - trigger protection
            - schedule an event
        """

        self._closed = False

    def close(self) -> None:
        """
        Close the breaker.

        Only local physical state is changed.

        A failed breaker cannot be successfully closed.
        """

        if self._failed:
            raise RuntimeError(
                f"Breaker '{self.id}' is failed and "
                "cannot be closed."
            )

        if not self._in_service:
            raise RuntimeError(
                f"Breaker '{self.id}' is out of service "
                "and cannot be closed."
            )

        self._closed = True

    def trip(self) -> None:
        """
        Open the breaker as a physical trip operation.

        Protection logic decides whether a trip should occur;
        this method only applies the physical state change.
        """

        self.open()

    def reset_failure(self) -> None:
        """
        Clear the local failure flag.

        Reset authorization and protection policy belong outside
        this model.
        """

        self._failed = False

    def set_failed(
        self,
        failed: bool = True,
    ) -> None:
        """
        Set or clear breaker failure state.
        """

        self._failed = bool(failed)

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set service state.

        This does not alter terminal connectivity.
        """

        self._in_service = bool(value)

    # =============================================================
    # ELECTRICAL STATE
    # =============================================================

    @property
    def conducts(self) -> bool:
        """
        Return whether the breaker currently provides a closed
        electrical path.

        This is a local state interpretation.

        Network topology decides how this state affects the
        assembled network.
        """

        return (
            self._in_service
            and self._closed
            and not self._failed
            and self.is_connected
        )

    @property
    def is_operable(self) -> bool:
        """
        Return whether the breaker can be operated normally.
        """

        return (
            self._in_service
            and not self._failed
        )

    # =============================================================
    # RATINGS
    # =============================================================

    def set_ratings(
        self,
        *,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        interrupting_capacity_ka: float | None = None,
        short_time_withstand_ka: float | None = None,
        making_capacity_ka: float | None = None,
    ) -> None:
        """
        Update breaker ratings.

        Only supplied values are changed.
        """

        if rated_voltage_kv is not None:
            rated_voltage_kv = (
                self._validate_positive(
                    rated_voltage_kv,
                    "rated_voltage_kv",
                )
            )

        if rated_current_a is not None:
            rated_current_a = (
                self._validate_positive(
                    rated_current_a,
                    "rated_current_a",
                )
            )

        if interrupting_capacity_ka is not None:
            interrupting_capacity_ka = (
                self._validate_positive(
                    interrupting_capacity_ka,
                    "interrupting_capacity_ka",
                )
            )

        if short_time_withstand_ka is not None:
            short_time_withstand_ka = (
                self._validate_positive(
                    short_time_withstand_ka,
                    "short_time_withstand_ka",
                )
            )

        if making_capacity_ka is not None:
            making_capacity_ka = (
                self._validate_positive(
                    making_capacity_ka,
                    "making_capacity_ka",
                )
            )

        if rated_voltage_kv is not None:
            self.rated_voltage_kv = rated_voltage_kv

        if rated_current_a is not None:
            self.rated_current_a = rated_current_a

        if interrupting_capacity_ka is not None:
            self.interrupting_capacity_ka = (
                interrupting_capacity_ka
            )

        if short_time_withstand_ka is not None:
            self.short_time_withstand_ka = (
                short_time_withstand_ka
            )

        if making_capacity_ka is not None:
            self.making_capacity_ka = making_capacity_ka

        self.validate_parameters()

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate breaker-local engineering parameters.

        Network topology and protection-study validity are outside
        this model.
        """

        self.rated_voltage_kv = (
            self._validate_optional_positive(
                self.rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.rated_current_a = (
            self._validate_optional_positive(
                self.rated_current_a,
                "rated_current_a",
            )
        )

        self.interrupting_capacity_ka = (
            self._validate_optional_positive(
                self.interrupting_capacity_ka,
                "interrupting_capacity_ka",
            )
        )

        self.short_time_withstand_ka = (
            self._validate_optional_positive(
                self.short_time_withstand_ka,
                "short_time_withstand_ka",
            )
        )

        self.making_capacity_ka = (
            self._validate_optional_positive(
                self.making_capacity_ka,
                "making_capacity_ka",
            )
        )

        self.opening_time_s = (
            self._validate_non_negative(
                self.opening_time_s,
                "opening_time_s",
            )
        )

        self.closing_time_s = (
            self._validate_non_negative(
                self.closing_time_s,
                "closing_time_s",
            )
        )

        return True

    def validate(self) -> bool:
        """
        Public local validation entry point.
        """

        return self.validate_parameters()

    # Backward-compatible private method.
    def _validate_parameters(self) -> None:
        """
        Compatibility wrapper for older callers.

        New code should use validate_parameters().
        """

        self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured breaker diagnostics.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "from_endpoint": (
                getattr(
                    self.endpoint_from,
                    "id",
                    None,
                )
                if self.endpoint_from is not None
                else None
            ),

            "to_endpoint": (
                getattr(
                    self.endpoint_to,
                    "id",
                    None,
                )
                if self.endpoint_to is not None
                else None
            ),

            "from_bus": (
                getattr(
                    self.from_bus,
                    "id",
                    None,
                )
                if self.from_bus is not None
                else None
            ),

            "to_bus": (
                getattr(
                    self.to_bus,
                    "id",
                    None,
                )
                if self.to_bus is not None
                else None
            ),

            "connected": self.is_connected,

            "in_service": self.in_service,
            "closed": self.closed,
            "failed": self.failed,
            "conducts": self.conducts,
            "operable": self.is_operable,

            "rated_voltage_kv":
                self.rated_voltage_kv,

            "rated_current_a":
                self.rated_current_a,

            "interrupting_capacity_ka":
                self.interrupting_capacity_ka,

            "short_time_withstand_ka":
                self.short_time_withstand_ka,

            "making_capacity_ka":
                self.making_capacity_ka,

            "opening_time_s":
                self.opening_time_s,

            "closing_time_s":
                self.closing_time_s,
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        from_id = getattr(
            self.endpoint_from,
            "id",
            None,
        )

        to_id = getattr(
            self.endpoint_to,
            "id",
            None,
        )

        return (
            f"<Breaker "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"closed={self.closed}, "
            f"in_service={self.in_service}, "
            f"failed={self.failed}>"
        )

    # =============================================================
    # VALIDATION HELPERS
    # =============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Return a finite floating-point value."""

        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite positive value."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @classmethod
    def _validate_optional_positive(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """Validate an optional positive value."""

        if value is None:
            return None

        return cls._validate_positive(
            value,
            name,
        )

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite non-negative value."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value
