# core/model/capacitor.py
"""
GridForge V2 Capacitor Model
============================

Author:
    Subhendu Mishra

File:
    core/model/capacitor.py

Purpose
-------
Defines the canonical GridForge V2 static shunt capacitor model.

Architectural role
------------------
A Capacitor is a physical passive electrical apparatus represented
at the model layer by a single electrical terminal and its shunt
reactive-power/admittance characteristics.

The Capacitor owns:

    - persistent identity
    - electrical rating
    - operating state
    - energised step state
    - electrical terminal
    - local validation

The Capacitor does NOT own:

    - global network topology
    - network graph state
    - Y-bus construction
    - power-flow solving
    - short-circuit solving
    - protection algorithms
    - switching coordination
    - GUI/SLD geometry
    - rendering
    - study orchestration

Power convention
----------------
GridForge uses the injection convention:

    Q > 0  -> reactive power injected into the network
    Q < 0  -> reactive power absorbed from the network

A capacitor therefore normally has:

    Q > 0

For a capacitor bank:

    Q_total = Q_step * energized_steps

The numerical/network layers are responsible for converting this
model state into the appropriate network representation.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal

class Capacitor(ElectricalObject, Injection):
    """
    Static shunt capacitor-bank model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    endpoint:
        Electrical endpoint. May be None until connected.

    q_mvar:
        Total rated reactive-power injection when all configured
        steps are energized.

    steps:
        Number of capacitor steps.

    energized_steps:
        Number of currently energized steps.

    in_service:
        Whether the capacitor bank is electrically available.

    bus:
        Backward-compatible endpoint alias.
    """

    TYPE = "CAPACITOR"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint: Any = None,
        q_mvar: float = 0.0,
        steps: int = 1,
        energized_steps: int | None = None,
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
                f"Capacitor '{self.id}' received both endpoint and bus "
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
                "Capacitor q_mvar must be non-negative."
            )

        self.steps = self._validate_steps(
            steps
        )

        if energized_steps is None:
            energized_steps = self.steps

        self.energized_steps = self._validate_energized_steps(
            energized_steps,
            self.steps,
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
        """Return the authoritative capacitor terminal."""

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
        """Return whether the capacitor terminal is connected."""

        return self.terminal.is_connected

    # =================================================================
    # ENDPOINT CONNECTIVITY
    # =================================================================

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the capacitor terminal.

        Global network topology remains owned by core/network.
        """

        if endpoint is None:
            raise ValueError(
                f"Capacitor '{self.id}' endpoint cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the capacitor terminal.

        This does not change service state.
        """

        self.terminal.disconnect()

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the capacitor is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the capacitor is out of service."""

        return not self.in_service

    @property
    def is_available(self) -> bool:
        """Return whether the capacitor is electrically available."""

        return self.in_service

    def put_in_service(self) -> None:
        """Place the capacitor in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the capacitor out of service."""

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

    # Compatibility service-state aliases.

    def connect(self) -> None:
        """
        Compatibility alias for put_in_service().

        This does not create network topology.
        """

        self.put_in_service()

    def disconnect(self) -> None:
        """
        Compatibility alias for take_out_of_service().

        This does not remove network topology.
        """

        self.take_out_of_service()

    def close(self) -> None:
        """Place the capacitor in service."""

        self.put_in_service()

    def trip(self) -> None:
        """Take the capacitor out of service."""

        self.take_out_of_service()

    # =================================================================
    # STEP CONTROL
    # =================================================================

    @property
    def available_steps(self) -> int:
        """Return the number of currently available non-energized steps."""

        return self.steps - self.energized_steps

    @property
    def all_steps_energized(self) -> bool:
        """Return True when all capacitor steps are energized."""

        return self.energized_steps == self.steps

    @property
    def all_steps_deenergized(self) -> bool:
        """Return True when no capacitor steps are energized."""

        return self.energized_steps == 0

    def set_energized_steps(
        self,
        energized_steps: int,
    ) -> None:
        """Set the number of energized capacitor steps."""

        self.energized_steps = self._validate_energized_steps(
            energized_steps,
            self.steps,
        )

    def energize_step(self) -> None:
        """Energize one additional capacitor step."""

        if self.energized_steps >= self.steps:
            raise ValueError(
                f"Capacitor '{self.id}' has no available step to energize."
            )

        self.energized_steps += 1

    def deenergize_step(self) -> None:
        """De-energize one capacitor step."""

        if self.energized_steps <= 0:
            raise ValueError(
                f"Capacitor '{self.id}' has no energized step to remove."
            )

        self.energized_steps -= 1

    def energize_all(self) -> None:
        """Energize all configured capacitor steps."""

        self.energized_steps = self.steps

    def deenergize_all(self) -> None:
        """De-energize all capacitor steps."""

        self.energized_steps = 0

    # =================================================================
    # REACTIVE POWER
    # =================================================================

    @property
    def q_per_step_mvar(self) -> float:
        """
        Return rated reactive-power injection per capacitor step.
        """

        if self.steps <= 0:
            return 0.0

        return self.q_mvar / self.steps

    @property
    def reactive_power_injection_mvar(self) -> float:
        """
        Return effective reactive-power injection.

        An out-of-service capacitor contributes zero injection.
        """

        if not self.in_service:
            return 0.0

        return (
            self.q_per_step_mvar
            * self.energized_steps
        )

    @property
    def q_injection_mvar(self) -> float:
        """Compatibility alias for effective reactive injection."""

        return self.reactive_power_injection_mvar

    @property
    def reactive_power_mvar(self) -> float:
        """Compatibility alias for effective reactive injection."""

        return self.reactive_power_injection_mvar

    def set_reactive_power_rating(
        self,
        q_mvar: float,
    ) -> None:
        """
        Set total rated reactive-power injection.

        The rating is distributed equally among the configured
        steps.
        """

        q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        if q_mvar < 0.0:
            raise ValueError(
                "Capacitor q_mvar must be non-negative."
            )

        self.q_mvar = q_mvar

    # =================================================================
    # ADMITTANCE
    # =================================================================

    @property
    def admittance(self) -> complex:
        """
        Return an effective normalized shunt admittance representation.

        The capacitor model stores its engineering rating in MVAr.
        It deliberately does not invent a voltage base in order to
        calculate physical siemens values.

        Therefore this property exposes a normalized susceptance
        representation:

            Y_normalized = j * Q_effective

        Numerical layers requiring physical admittance must perform
        the voltage-base conversion using their authoritative study
        data.
        """

        return complex(
            0.0,
            self.reactive_power_injection_mvar,
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate capacitor-local engineering parameters.

        No network topology or numerical study validation occurs here.
        """

        self.q_mvar = self._validate_finite(
            self.q_mvar,
            "q_mvar",
        )

        if self.q_mvar < 0.0:
            raise ValueError(
                "Capacitor q_mvar must be non-negative."
            )

        self.steps = self._validate_steps(
            self.steps
        )

        self.energized_steps = self._validate_energized_steps(
            self.energized_steps,
            self.steps,
        )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        if self.terminal.owner is not self:
            raise ValueError(
                f"Capacitor '{self.id}' terminal ownership is invalid."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Capacitor model through the common
        ElectricalObject contract.
        """

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured capacitor diagnostics."""

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
            "steps": self.steps,
            "energized_steps": self.energized_steps,
            "available_steps": self.available_steps,

            "q_per_step_mvar":
                self.q_per_step_mvar,

            "reactive_power_injection_mvar":
                self.reactive_power_injection_mvar,

            "admittance":
                self.admittance,

            "in_service": self.in_service,
            "is_available": self.is_available,

            "endpoint": endpoint_id,
            "is_connected": self.is_connected,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Capacitor "
            f"id={self.id}, "
            f"Q={self.q_mvar:.6f} MVAr, "
            f"steps={self.energized_steps}/{self.steps}, "
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

    @staticmethod
    def _validate_steps(
        steps: int,
    ) -> int:
        """Validate total capacitor step count."""

        if isinstance(
            steps,
            bool,
        ):
            raise TypeError(
                "steps must be an integer."
            )

        if not isinstance(
            steps,
            int,
        ):
            raise TypeError(
                "steps must be an integer."
            )

        if steps < 1:
            raise ValueError(
                "steps must be at least 1."
            )

        return steps
    def get_power(self) -> tuple[float, float]:
            """Return network injection using the GridForge P/Q convention."""
        return (0.0, self.reactive_power_injection_mvar)
    @staticmethod
    def _validate_energized_steps(
        energized_steps: int,
        steps: int,
    ) -> int:
        """Validate energized step count against total steps."""

        if isinstance(
            energized_steps,
            bool,
        ):
            raise TypeError(
                "energized_steps must be an integer."
            )

        if not isinstance(
            energized_steps,
            int,
        ):
            raise TypeError(
                "energized_steps must be an integer."
            )

        if energized_steps < 0:
            raise ValueError(
                "energized_steps cannot be negative."
            )

        if energized_steps > steps:
            raise ValueError(
                "energized_steps cannot exceed steps."
            )

        return energized_steps


__all__ = [
    "Capacitor",
]
