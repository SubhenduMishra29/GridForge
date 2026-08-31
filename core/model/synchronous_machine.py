# ============================================================
# File: core/model/synchronous_machine.py
# GridForge V2 — Synchronous Machine Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Synchronous Machine Model
=========================================

Authoritative Core model for a synchronous electrical machine.

The model represents physical/electrical machine data and
steady-state operating information.

Dynamic control behavior such as AVR, exciter, governor, and
PSS belongs to the Control / Simulation layers.

Terminal Contract
-----------------

The machine owns exactly one authoritative Terminal.

    SynchronousMachine
          |
          +-- _terminal
                 |
                 +-- owner
                 +-- role
                 +-- endpoint
                 +-- attach()
                 +-- detach()
                 +-- is_connected
                 +-- validate()

The machine never maintains a duplicate authoritative endpoint
or bus reference.

Network topology remains the responsibility of the Network layer.

Power Convention
----------------

Positive P/Q values represent injection into the network.

Negative P/Q values represent consumption from the network.

When the machine is out of service:

    get_power() -> (0.0, 0.0)
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class SynchronousMachine(ElectricalObject, Injection):
    """
    Generic synchronous-machine model.

    Positive active/reactive power represents injection into the
    electrical network.

    Dynamic simulation and control execution are deliberately
    outside this model.
    """

    TYPE = "SYNCHRONOUS_MACHINE"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        terminal: Terminal | None = None,
        endpoint: Any = None,
        bus: Any = None,
        active_power_injection_mw: float = 0.0,
        reactive_power_injection_mvar: float = 0.0,
        rated_power_mva: float | None = None,
        rated_voltage_kv: float | None = None,
        frequency_hz: float = 50.0,
        in_service: bool = True,
    ) -> None:
        """
        Construct a synchronous machine.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable machine name.

        terminal:
            Optional pre-created authoritative Terminal.

        endpoint:
            Initial electrical endpoint.

        bus:
            Compatibility alias for endpoint.

        active_power_injection_mw:
            Steady-state active-power injection.

        reactive_power_injection_mvar:
            Steady-state reactive-power injection.

        rated_power_mva:
            Optional machine rated apparent power.

        rated_voltage_kv:
            Optional machine rated voltage.

        frequency_hz:
            Nominal machine/system frequency.

        in_service:
            Initial operational service state.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Endpoint / bus compatibility
        # --------------------------------------------------------

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"SynchronousMachine '{self.id}' received "
                "both 'endpoint' and 'bus' with different values."
            )

        if endpoint is None:
            endpoint = bus

        # --------------------------------------------------------
        # Electrical operating state
        # --------------------------------------------------------

        self.active_power_injection_mw = (
            self._validate_finite(
                active_power_injection_mw,
                "active_power_injection_mw",
            )
        )

        self.reactive_power_injection_mvar = (
            self._validate_finite(
                reactive_power_injection_mvar,
                "reactive_power_injection_mvar",
            )
        )

        # --------------------------------------------------------
        # Nameplate parameters
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Operational state
        # --------------------------------------------------------

        if not isinstance(
            in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        self.in_service = in_service

        # --------------------------------------------------------
        # Authoritative Terminal
        # --------------------------------------------------------

        if terminal is None:
            self._terminal = Terminal(
                owner=self,
                role="terminal",
            )
        else:
            if not isinstance(
                terminal,
                Terminal,
            ):
                raise TypeError(
                    "terminal must be a Terminal."
                )

            if terminal.owner is not self:
                raise ValueError(
                    "terminal owner must be this "
                    "SynchronousMachine."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "SynchronousMachine terminal role must "
                    "be 'terminal'."
                )

            self._terminal = terminal

        # --------------------------------------------------------
        # Initial endpoint attachment
        # --------------------------------------------------------

        if endpoint is not None:
            self._terminal.attach(
                endpoint
            )

        self.validate()

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return canonical GridForge element type.
        """

        return self.TYPE

    # ============================================================
    # TERMINAL
    # ============================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative machine Terminal.

        The Terminal itself owns endpoint state.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return the machine's terminal collection.

        A synchronous machine has exactly one terminal.
        """

        return (
            self._terminal,
        )

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    @property
    def endpoint(self) -> Any | None:
        """
        Return the authoritative Terminal endpoint.

        This is derived from Terminal and is not independent
        machine state.
        """

        return self._terminal.endpoint

    @property
    def bus(self) -> Any | None:
        """
        Compatibility accessor for the Terminal endpoint.

        Bus is derived state and is never stored independently.
        """

        return self._terminal.endpoint

    @property
    def is_connected(self) -> bool:
        """
        Return whether the machine Terminal is connected.
        """

        return self._terminal.is_connected

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach the machine Terminal to an electrical endpoint.

        This changes only local Terminal state.

        Network topology interpretation remains the responsibility
        of the Network layer.
        """

        if endpoint is None:
            raise ValueError(
                f"SynchronousMachine '{self.id}' endpoint "
                "cannot be None."
            )

        self._terminal.attach(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Detach the machine Terminal from its endpoint.
        """

        self._terminal.detach()

    # ============================================================
    # INJECTION CONTRACT
    # ============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return effective network injection.

        Returns
        -------
        tuple[float, float]
            (P_MW, Q_Mvar)

        An out-of-service machine contributes zero injection.
        """

        if not self.in_service:
            return (
                0.0,
                0.0,
            )

        return (
            self.active_power_injection_mw,
            self.reactive_power_injection_mvar,
        )

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return whether the machine is in service.
        """

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return whether the machine is out of service.
        """

        return not self.in_service

    def put_in_service(self) -> None:
        """
        Place the machine in service.

        Terminal connectivity is unchanged.
        """

        self.in_service = True

    def take_out_of_service(self) -> None:
        """
        Take the machine out of service.

        Terminal connectivity is unchanged.
        """

        self.in_service = False

    # ============================================================
    # POWER
    # ============================================================

    def set_power(
        self,
        active_power_mw: float,
        reactive_power_mvar: float,
    ) -> None:
        """
        Set steady-state active and reactive injection.
        """

        self.active_power_injection_mw = (
            self._validate_finite(
                active_power_mw,
                "active_power_mw",
            )
        )

        self.reactive_power_injection_mvar = (
            self._validate_finite(
                reactive_power_mvar,
                "reactive_power_mvar",
            )
        )

        self.validate()

    def set_active_power(
        self,
        active_power_mw: float,
    ) -> None:
        """
        Set active-power injection.
        """

        self.active_power_injection_mw = (
            self._validate_finite(
                active_power_mw,
                "active_power_mw",
            )
        )

    def set_reactive_power(
        self,
        reactive_power_mvar: float,
    ) -> None:
        """
        Set reactive-power injection.
        """

        self.reactive_power_injection_mvar = (
            self._validate_finite(
                reactive_power_mvar,
                "reactive_power_mvar",
            )
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate machine-local parameters and Terminal invariants.

        Network-wide topology validation is intentionally outside
        this method.
        """

        self.active_power_injection_mw = (
            self._validate_finite(
                self.active_power_injection_mw,
                "active_power_injection_mw",
            )
        )

        self.reactive_power_injection_mvar = (
            self._validate_finite(
                self.reactive_power_injection_mvar,
                "reactive_power_injection_mvar",
            )
        )

        if self.rated_power_mva is not None:
            self.rated_power_mva = (
                self._validate_positive(
                    self.rated_power_mva,
                    "rated_power_mva",
                )
            )

        if self.rated_voltage_kv is not None:
            self.rated_voltage_kv = (
                self._validate_positive(
                    self.rated_voltage_kv,
                    "rated_voltage_kv",
                )
            )

        self.frequency_hz = self._validate_positive(
            self.frequency_hz,
            "frequency_hz",
        )

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                "terminal owner must be this "
                "SynchronousMachine."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "SynchronousMachine terminal role must "
                "be 'terminal'."
            )

        self._terminal.validate()

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured machine diagnostics.
        """

        endpoint = self._terminal.endpoint

        endpoint_id = (
            endpoint.id
            if endpoint is not None
            and hasattr(endpoint, "id")
            else endpoint
        )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal,
            "endpoint": endpoint_id,
            "bus": endpoint_id,
            "is_connected":
                self._terminal.is_connected,

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

            "injection":
                self.get_power(),
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        endpoint = self._terminal.endpoint

        endpoint_id = (
            endpoint.id
            if endpoint is not None
            and hasattr(endpoint, "id")
            else endpoint
        )

        return (
            f"<SynchronousMachine "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"P={self.active_power_injection_mw} MW, "
            f"Q={self.reactive_power_injection_mvar} Mvar, "
            f"in_service={self.in_service}>"
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """
        Validate and return a finite numeric value.
        """

        try:
            numeric = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(numeric):
            raise ValueError(
                f"{name} must be finite."
            )

        return numeric

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Validate and return a strictly positive value.
        """

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return numeric


class SyncMachine(SynchronousMachine):
    """
    Backward-compatible alias/subclass.

    SynchronousMachine remains the canonical model class.
    """

    pass


__all__ = [
    "SynchronousMachine",
    "SyncMachine",
]
