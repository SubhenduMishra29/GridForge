# core/model/motor.py
"""
GridForge V2 Motor Model
========================

Author:
    Subhendu Mishra

A Motor is an electrical power-consumption element.

Architecture
------------

    ElectricalObject
          +
      Injection
          |
          v
        Motor
          |
          v
       Terminal
          |
          v
    Network / Topology

The Motor owns:

    - motor identity
    - rated apparent power
    - rated voltage
    - power factor
    - active/reactive operating state
    - efficiency
    - slip
    - starting current
    - running state
    - service state
    - one authoritative Terminal

The Motor does NOT own:

    - network topology
    - Bus collections
    - network graph
    - load-flow solving
    - motor dynamic simulation
    - protection coordination
    - SLD geometry
    - GUI state

Power convention
----------------

Motor consumption is represented internally as positive
consumption values:

    p > 0  -> active power consumed
    q > 0  -> reactive power consumed

Therefore the network injection returned by get_power() is:

    (-p, -q)

When the Motor is stopped or out of service:

    (0, 0)

The p/q operating values are per-unit.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Motor(ElectricalObject, Injection):
    """
    Electrical motor model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable motor name.

    endpoint:
        Initial electrical endpoint. May be None.

    rated_mva:
        Motor rated apparent power in MVA.

    rated_kv:
        Motor rated voltage in kV.

    power_factor:
        Operating power factor, 0 < PF <= 1.

    p:
        Active power consumption in per-unit.

    q:
        Reactive power consumption in per-unit.

    efficiency:
        Motor efficiency, 0 < efficiency <= 1.

    slip:
        Per-unit motor slip, 0 <= slip < 1.

    starting_current_pu:
        Starting current in per-unit.

    running:
        Initial motor running state.

    in_service:
        Initial equipment service state.

    bus:
        Backward-compatible endpoint alias.
    """

    TYPE = "MOTOR"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint: Any = None,
        rated_mva: float = 1.0,
        rated_kv: float = 11.0,
        power_factor: float = 0.9,
        p: float = 1.0,
        q: float = 0.0,
        efficiency: float = 0.95,
        slip: float = 0.02,
        starting_current_pu: float = 6.0,
        running: bool = True,
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
                f"Motor '{self.id}' received both endpoint and bus "
                "with different values."
            )

        if endpoint is None:
            endpoint = bus

        # =============================================================
        # NAMEPLATE DATA
        # =============================================================

        self.rated_mva = self._validate_positive(
            rated_mva,
            "rated_mva",
        )

        self.rated_kv = self._validate_positive(
            rated_kv,
            "rated_kv",
        )

        self.power_factor = self._validate_power_factor(
            power_factor,
        )

        # =============================================================
        # OPERATING ELECTRICAL STATE
        # =============================================================

        self.p = self._validate_non_negative(
            p,
            "p",
        )

        self.q = self._validate_non_negative(
            q,
            "q",
        )

        self.efficiency = self._validate_efficiency(
            efficiency,
        )

        self.slip = self._validate_slip(
            slip,
        )

        self.starting_current_pu = (
            self._validate_non_negative(
                starting_current_pu,
                "starting_current_pu",
            )
        )

        # =============================================================
        # SERVICE / RUNNING STATE
        # =============================================================

        if not isinstance(
            running,
            bool,
        ):
            raise TypeError(
                "running must be boolean."
            )

        if not isinstance(
            in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        self.running = running
        self.in_service = in_service

        # =============================================================
        # AUTHORITATIVE TERMINAL
        # =============================================================

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # =============================================================
        # COMMON VALIDATION CONTRACT
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
        """Return the Motor's authoritative terminal."""

        return (
            self.terminal,
        )

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def endpoint(self) -> Any:
        """
        Return the authoritative physical endpoint.

        Terminal.endpoint is the source of truth.
        """

        return self.terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor for the terminal bus.

        This is derived state and is not authoritative.
        """

        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return True when the Motor terminal is connected."""

        return self.terminal.is_connected

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the Motor terminal locally.

        Global network topology is not modified here.
        """

        if endpoint is None:
            raise ValueError(
                f"Motor '{self.id}' endpoint cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Motor terminal locally.
        """

        self.terminal.disconnect()

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return True when the Motor is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return True when the Motor is out of service."""

        return not self.in_service

    def put_in_service(self) -> None:
        """Place the Motor in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the Motor out of service."""

        self.in_service = False

    # Compatibility aliases.
    #
    # These operate on service state, not terminal connectivity.

    def connect(self) -> None:
        """Compatibility alias for put_in_service()."""

        self.put_in_service()

    def disconnect(self) -> None:
        """Compatibility alias for take_out_of_service()."""

        self.take_out_of_service()

    # =================================================================
    # RUNNING STATE
    # =================================================================

    @property
    def is_running(self) -> bool:
        """Return True when the motor is running."""

        return self.running

    @property
    def is_stopped(self) -> bool:
        """Return True when the motor is stopped."""

        return not self.running

    def start(self) -> None:
        """Start the Motor."""

        if not self.in_service:
            raise RuntimeError(
                f"Motor '{self.id}' cannot start while out of service."
            )

        self.running = True

    def stop(self) -> None:
        """Stop the Motor."""

        self.running = False

    # =================================================================
    # INJECTION CONTRACT
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network injection.

        Motor p/q represent positive consumption.

        Therefore an operating Motor injects:

            (-p, -q)

        A stopped or out-of-service Motor injects:

            (0, 0)
        """

        if (
            not self.in_service
            or not self.running
        ):
            return (
                0.0,
                0.0,
            )

        return (
            -self.p,
            -self.q,
        )

    # =================================================================
    # POWER STATE
    # =================================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """Set active/reactive motor consumption in per-unit."""

        self.p = self._validate_non_negative(
            p,
            "p",
        )

        self.q = self._validate_non_negative(
            q,
            "q",
        )

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """Set active motor consumption in per-unit."""

        self.p = self._validate_non_negative(
            p,
            "p",
        )

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """Set reactive motor consumption in per-unit."""

        self.q = self._validate_non_negative(
            q,
            "q",
        )

    @property
    def active_power(self) -> float:
        """Return active power consumption in per-unit."""

        return self.p

    @property
    def reactive_power(self) -> float:
        """Return reactive power consumption in per-unit."""

        return self.q

    # =================================================================
    # NAMEPLATE / OPERATING PARAMETERS
    # =================================================================

    def set_power_factor(
        self,
        power_factor: float,
    ) -> None:
        """Set operating power factor."""

        self.power_factor = self._validate_power_factor(
            power_factor,
        )

    def set_efficiency(
        self,
        efficiency: float,
    ) -> None:
        """Set motor efficiency."""

        self.efficiency = self._validate_efficiency(
            efficiency,
        )

    def set_slip(
        self,
        slip: float,
    ) -> None:
        """Set motor slip."""

        self.slip = self._validate_slip(
            slip,
        )

    def set_starting_current(
        self,
        starting_current_pu: float,
    ) -> None:
        """Set starting current in per-unit."""

        self.starting_current_pu = (
            self._validate_non_negative(
                starting_current_pu,
                "starting_current_pu",
            )
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Motor-local engineering invariants.

        Network topology is deliberately outside this method.
        """

        self.rated_mva = self._validate_positive(
            self.rated_mva,
            "rated_mva",
        )

        self.rated_kv = self._validate_positive(
            self.rated_kv,
            "rated_kv",
        )

        self.power_factor = self._validate_power_factor(
            self.power_factor,
        )

        self.p = self._validate_non_negative(
            self.p,
            "p",
        )

        self.q = self._validate_non_negative(
            self.q,
            "q",
        )

        self.efficiency = self._validate_efficiency(
            self.efficiency,
        )

        self.slip = self._validate_slip(
            self.slip,
        )

        self.starting_current_pu = (
            self._validate_non_negative(
                self.starting_current_pu,
                "starting_current_pu",
            )
        )

        if not isinstance(
            self.running,
            bool,
        ):
            raise TypeError(
                "running must be boolean."
            )

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        if self.terminal.owner is not self:
            raise ValueError(
                f"Motor '{self.id}' terminal ownership is invalid."
            )

        return True

    def validate(self) -> bool:
        """
        Validate complete Motor model through the common contract.
        """

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured Motor diagnostics."""

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

            "terminal": self.terminal.id,

            "endpoint": endpoint_id,
            "is_connected": self.is_connected,

            "rated_mva": self.rated_mva,
            "rated_kv": self.rated_kv,

            "power_factor": self.power_factor,

            "p": self.p,
            "q": self.q,

            "efficiency": self.efficiency,
            "slip": self.slip,

            "starting_current_pu":
                self.starting_current_pu,

            "running": self.running,
            "in_service": self.in_service,

            "injection": self.get_power(),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        endpoint_id = None

        if self.endpoint is not None:
            endpoint_id = getattr(
                self.endpoint,
                "id",
                self.endpoint,
            )

        return (
            f"<Motor "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"P={self.p:.6f} pu, "
            f"Q={self.q:.6f} pu, "
            f"running={self.running}, "
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
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

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
        """Convert to float and require value > 0."""

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
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require value >= 0."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value

    @classmethod
    def _validate_power_factor(
        cls,
        value: float,
    ) -> float:
        """Validate 0 < power factor <= 1."""

        value = cls._validate_finite(
            value,
            "power_factor",
        )

        if not (
            0.0 < value <= 1.0
        ):
            raise ValueError(
                "power_factor must satisfy "
                "0 < power_factor <= 1."
            )

        return value

    @classmethod
    def _validate_efficiency(
        cls,
        value: float,
    ) -> float:
        """Validate 0 < efficiency <= 1."""

        value = cls._validate_finite(
            value,
            "efficiency",
        )

        if not (
            0.0 < value <= 1.0
        ):
            raise ValueError(
                "efficiency must satisfy "
                "0 < efficiency <= 1."
            )

        return value

    @classmethod
    def _validate_slip(
        cls,
        value: float,
    ) -> float:
        """Validate 0 <= slip < 1."""

        value = cls._validate_finite(
            value,
            "slip",
        )

        if not (
            0.0 <= value < 1.0
        ):
            raise ValueError(
                "slip must satisfy "
                "0 <= slip < 1."
            )

        return value


__all__ = [
    "Motor",
]
