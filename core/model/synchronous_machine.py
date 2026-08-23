"""
GridForge V2 Synchronous Machine Model
======================================

Author:
    Subhendu Mishra

File:
    core/model/synchronous_machine.py

Purpose
-------
Authoritative Core model for a synchronous electrical machine.

The model represents the physical/electrical machine and its
steady-state operating data.

Dynamic control behavior such as AVR, exciter, governor, and PSS
belongs outside core/model.
"""

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class SynchronousMachine(ElectricalObject, Injection):
    """
    Generic synchronous-machine model.

    Positive P/Q values represent injection into the network.
    Negative values represent consumption from the network.

    Dynamic simulation parameters may be stored as machine metadata,
    but their execution belongs to the Control/Simulation layers.
    """

    TYPE = "SYNCHRONOUS_MACHINE"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        terminal: Terminal | None = None,
        bus: Any = None,
        active_power_injection_mw: float = 0.0,
        reactive_power_injection_mvar: float = 0.0,
        rated_power_mva: float | None = None,
        rated_voltage_kv: float | None = None,
        frequency_hz: float = 50.0,
        in_service: bool = True,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )

        self.terminal = (
            terminal
            if terminal is not None
            else Terminal(
                endpoint=bus,
                owner=self,
            )
        )

        if not isinstance(
            self.terminal,
            Terminal,
        ):
            raise TypeError(
                "terminal must be a Terminal."
            )

        if self.terminal.owner is not self:
            raise ValueError(
                "terminal owner must be this "
                "SynchronousMachine."
            )

        self.active_power_injection_mw = float(
            active_power_injection_mw
        )

        self.reactive_power_injection_mvar = float(
            reactive_power_injection_mvar
        )

        self.rated_power_mva = (
            None
            if rated_power_mva is None
            else self._validate_positive(
                rated_power_mva,
                "rated_power_mva",
            )
        )

        self.rated_voltage_kv = (
            None
            if rated_voltage_kv is None
            else self._validate_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.frequency_hz = self._validate_positive(
            frequency_hz,
            "frequency_hz",
        )

        if not isinstance(
            in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        self.in_service = in_service

        self.validate()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # TERMINAL
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal]:
        """Return the machine's authoritative terminal."""

        return (self.terminal,)

    @property
    def bus(self) -> Any:
        """Return the terminal endpoint."""

        return self.terminal.endpoint

    @property
    def is_connected(self) -> bool:
        """Return whether the machine has an electrical endpoint."""

        return self.terminal.is_connected

    # =================================================================
    # INJECTION CONTRACT
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return effective active and reactive network injection.

        Returns
        -------
        tuple[float, float]
            (P_MW, Q_Mvar)
        """

        if not self.in_service:
            return (0.0, 0.0)

        return (
            self.active_power_injection_mw,
            self.reactive_power_injection_mvar,
        )

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the machine is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the machine is out of service."""

        return not self.in_service

    def put_in_service(self) -> None:
        """Place the machine in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the machine out of service."""

        self.in_service = False

    # =================================================================
    # POWER
    # =================================================================

    def set_power(
        self,
        active_power_mw: float,
        reactive_power_mvar: float,
    ) -> None:
        """Set steady-state active and reactive injection."""

        self.active_power_injection_mw = float(
            active_power_mw
        )

        self.reactive_power_injection_mvar = float(
            reactive_power_mvar
        )

        self.validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """Validate machine-local parameters."""

        if not isinstance(
            self.terminal,
            Terminal,
        ):
            raise TypeError(
                "terminal must be a Terminal."
            )

        if self.terminal.owner is not self:
            raise ValueError(
                "terminal owner must be this "
                "SynchronousMachine."
            )

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        if self.rated_power_mva is not None:
            self.rated_power_mva = self._validate_positive(
                self.rated_power_mva,
                "rated_power_mva",
            )

        if self.rated_voltage_kv is not None:
            self.rated_voltage_kv = self._validate_positive(
                self.rated_voltage_kv,
                "rated_voltage_kv",
            )

        self.frequency_hz = self._validate_positive(
            self.frequency_hz,
            "frequency_hz",
        )

        return True

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured machine diagnostics."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "active_power_mw":
                self.active_power_injection_mw,
            "reactive_power_mvar":
                self.reactive_power_injection_mvar,
            "rated_power_mva":
                self.rated_power_mva,
            "rated_voltage_kv":
                self.rated_voltage_kv,
            "frequency_hz":
                self.frequency_hz,
            "in_service":
                self.in_service,
            "is_connected":
                self.is_connected,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        return (
            f"<SynchronousMachine "
            f"id={self.id}, "
            f"P={self.active_power_injection_mw} MW, "
            f"Q={self.reactive_power_injection_mvar} Mvar, "
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
        """Validate a finite numeric value."""

        value = float(value)

        if not __import__("math").isfinite(value):
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
        """Validate a strictly positive finite value."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value


class SyncMachine(SynchronousMachine):
    """
    Compatibility alias for SynchronousMachine.

    The canonical GridForge model name is SynchronousMachine.
    """

    pass


__all__ = [
    "SynchronousMachine",
    "SyncMachine",
]
