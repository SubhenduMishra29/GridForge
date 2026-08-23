# core/model/reactor.py
"""
GridForge V2 Reactor Model
==========================

Author:
    Subhendu Mishra

File:
    core/model/reactor.py

Purpose
-------
Defines the canonical GridForge V2 static shunt-reactor model.

Architectural role
------------------
A Reactor is a passive shunt electrical element that absorbs reactive
power from the network.

The Reactor owns:

    - persistent identity
    - reactive-power rating
    - operating state
    - electrical terminal
    - local engineering validation

The Reactor does NOT own:

    - network topology
    - graph state
    - bus collections
    - Y-bus construction
    - power-flow solving
    - short-circuit solving
    - protection logic
    - switching coordination
    - SLD geometry
    - GUI state
    - numerical study orchestration

Power convention
----------------
GridForge uses the injection convention:

    Q > 0  -> reactive power injected into the network
    Q < 0  -> reactive power absorbed by the network

A shunt reactor therefore normally has:

    Q < 0

The engineering rating ``q_mvar`` is stored as a positive magnitude
of reactive absorption. The effective network injection is therefore:

    Q_injection = -q_mvar

The numerical/network layers are responsible for converting the
engineering representation into the appropriate network matrix
representation.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal

class Reactor(ElectricalObject, Injection):
    """
    Static shunt reactor model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    endpoint:
        Electrical endpoint. May be None until connected.

    q_mvar:
        Rated reactive-power absorption magnitude in MVAr.

        This value is stored as a positive engineering magnitude.

    in_service:
        Whether the reactor is electrically active.

    bus:
        Backward-compatible endpoint alias.
    """

    TYPE = "REACTOR"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint: Any = None,
        q_mvar: float = 0.0,
        in_service: bool = True,
        bus: Any = None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # ENDPOINT COMPATIBILITY
        # =============================================================

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Reactor '{self.id}' received both endpoint and bus "
                "with different values."
            )

        if endpoint is None:
            endpoint = bus

        # =============================================================
        # ELECTRICAL RATING
        # =============================================================

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        if self.q_mvar < 0.0:
            raise ValueError(
                "Reactor q_mvar must be non-negative."
            )

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self._validate_bool(
            in_service,
            "in_service",
        )

        self.in_service = in_service

        # =============================================================
        # AUTHORITATIVE TERMINAL
        # =============================================================

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # =============================================================
        # VALIDATION
        # =============================================================

        self.validate()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the authoritative reactor terminal."""

        return (
            self.terminal,
        )

    @property
    def endpoint(self) -> Any:
        """Return the authoritative electrical endpoint."""

        return self.terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor for the historical bus API.

        The Terminal remains authoritative.
        """

        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return whether the reactor terminal is connected."""

        return self.terminal.is_connected

    # =================================================================
    # ENDPOINT CONNECTIVITY
    # =================================================================

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the reactor terminal.

        Network topology remains owned by core/network.
        """

        if endpoint is None:
            raise ValueError(
                f"Reactor '{self.id}' endpoint cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the reactor terminal.

        This does not change service state.
        """

        self.terminal.disconnect()

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the reactor is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the reactor is out of service."""

        return not self.in_service

    @property
    def is_available(self) -> bool:
        """Return whether the reactor is electrically available."""

        return self.in_service

    def put_in_service(self) -> None:
        """Place the reactor in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the reactor out of service."""

        self.in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """Set service state without silent boolean coercion."""

        self._validate_bool(
            value,
            "in_service",
        )

        self.in_service = value

    # Compatibility aliases.
    #
    # These are service-state operations only and do not create or
    # remove network topology.

    def connect(self) -> None:
        """Compatibility alias for put_in_service()."""

        self.put_in_service()

    def disconnect(self) -> None:
        """Compatibility alias for take_out_of_service()."""

        self.take_out_of_service()

    def close(self) -> None:
        """Place the reactor in service."""

        self.put_in_service()

    def trip(self) -> None:
        """Take the reactor out of service."""

        self.take_out_of_service()

    # =================================================================
    # REACTIVE POWER
    # =================================================================

    @property
    def reactive_power_absorption_mvar(self) -> float:
        """
        Return effective reactive-power absorption magnitude.

        An out-of-service reactor absorbs zero reactive power.
        """

        if not self.in_service:
            return 0.0

        return self.q_mvar

    @property
    def reactive_power_injection_mvar(self) -> float:
        """
        Return effective network reactive-power injection.

        Reactor absorption is represented as negative Q.
        """

        return -self.reactive_power_absorption_mvar

    @property
    def q_absorption_mvar(self) -> float:
        """Compatibility alias for reactive absorption magnitude."""

        return self.reactive_power_absorption_mvar

    @property
    def q_injection_mvar(self) -> float:
        """Compatibility alias for effective network Q injection."""

        return self.reactive_power_injection_mvar

    @property
    def reactive_power_mvar(self) -> float:
        """Return effective network reactive-power injection."""

        return self.reactive_power_injection_mvar

    def set_reactive_power_rating(
        self,
        q_mvar: float,
    ) -> None:
        """
        Set the reactor reactive-power absorption rating.

        The stored engineering rating is always non-negative.
        """

        q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        if q_mvar < 0.0:
            raise ValueError(
                "Reactor q_mvar must be non-negative."
            )

        self.q_mvar = q_mvar

    def set_q(
        self,
        q_mvar: float,
    ) -> None:
        """Compatibility alias for set_reactive_power_rating()."""

        self.set_reactive_power_rating(
            q_mvar
        )

    # =================================================================
    # POWER INJECTION
    # =================================================================

    def injection(self) -> tuple[float, float]:
        """
        Return the reactor's effective P/Q network injection.

        A passive shunt reactor has no active-power injection:

            P = 0
            Q < 0
        """

        return (
            0.0,
            self.reactive_power_injection_mvar,
        )

    # =================================================================
    # ADMITTANCE
    # =================================================================

    @property
    def admittance(self) -> complex:
        """
        Return a normalized shunt-admittance representation.

        The model stores an engineering MVAr rating and deliberately
        does not invent a voltage base.

        Therefore the normalized representation is:

            Y_normalized = -j * Q_absorption

        Numerical layers requiring physical siemens values must use
        their authoritative voltage-base/study data.
        """

        return complex(
            0.0,
            -self.reactive_power_absorption_mvar,
        )

    @property
    def y(self) -> complex:
        """Compatibility alias for admittance."""

        return self.admittance

    # =================================================================
    # CLASSIFICATION
    # =================================================================

    @property
    def is_inductive(self) -> bool:
        """Return True because the reactor is inductive."""

        return self.q_mvar > 0.0

    @property
    def is_zero_reactive_rating(self) -> bool:
        """Return True when the reactor rating is effectively zero."""

        return math.isclose(
            self.q_mvar,
            0.0,
            abs_tol=1e-12,
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate reactor-local engineering parameters.

        Network topology and numerical study validation are excluded.
        """

        self.q_mvar = self._validate_finite(
            self.q_mvar,
            "q_mvar",
        )

        if self.q_mvar < 0.0:
            raise ValueError(
                "Reactor q_mvar must be non-negative."
            )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        if self.terminal.owner is not self:
            raise ValueError(
                f"Reactor '{self.id}' terminal ownership is invalid."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Reactor model through the common
        ElectricalObject contract.
        """

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured reactor diagnostics."""

        endpoint_id = None

        if self.endpoint is not None:
            endpoint_id = getattr(
                self.endpoint,
                "id",
                self.endpoint,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "q_mvar": self.q_mvar,

            "reactive_power_absorption_mvar":
                self.reactive_power_absorption_mvar,

            "reactive_power_injection_mvar":
                self.reactive_power_injection_mvar,

            "admittance":
                self.admittance,

            "in_service": self.in_service,
            "is_available": self.is_available,

            "endpoint": endpoint_id,
            "is_connected": self.is_connected,

            "is_inductive": self.is_inductive,
            "is_zero_reactive_rating":
                self.is_zero_reactive_rating,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Reactor "
            f"id={self.id}, "
            f"Q_abs={self.q_mvar:.6f} MVAr, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require a finite value."""

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> None:
        """Require an actual boolean."""

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )


__all__ = [
    "Reactor",
]
