# ============================================================
# File: core/model/capacitor.py
# GridForge V2 — Shunt Capacitor Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Shunt Capacitor Model
====================================

Authoritative electrical-domain model for a shunt capacitor.

Architecture
------------

    ElectricalObject
           │
           ▼
       Capacitor
           │
           ▼
        Terminal
           │
           ▼
       endpoint

The Capacitor owns exactly one authoritative Terminal.

The Terminal owns the endpoint reference.

The Capacitor does not maintain a duplicate endpoint or bus
reference.

Domain responsibilities
-----------------------

Capacitor owns:

    - rated/operating reactive-power injection
    - in-service state
    - its authoritative electrical Terminal

Capacitor does NOT own:

    - Network topology
    - bus indexing
    - Y-bus construction
    - load-flow solving
    - short-circuit analysis
    - protection logic
    - switching coordination
    - SLD/UI state
    - rendering
    - persistence orchestration

Those responsibilities belong to the appropriate GridForge
Core/Application/UI layers.

Terminal contract
-----------------

The authoritative Terminal contract is:

    Terminal
    ├── owner
    ├── role
    ├── endpoint
    ├── attach()
    ├── detach()
    ├── is_connected
    └── validate()

Endpoint mutation is therefore performed only through:

    Terminal.attach(endpoint)
    Terminal.detach()

The Network layer interprets the Terminal endpoint as topology.
The Capacitor itself does not resolve topology.

Injection convention
--------------------

Positive reactive power represents reactive-power injection
into the electrical network.

For a shunt capacitor:

    P = 0 MW
    Q = reactive_power_injection_mvar

When the capacitor is out of service:

    P = 0 MW
    Q = 0 MVAr

No numerical network calculation is performed here.
"""

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Capacitor(ElectricalObject, Injection):
    """
    Shunt capacitor electrical-domain model.

    A Capacitor is a one-terminal shunt injection element.

    The single Terminal is the authoritative connection point.
    Its endpoint is interpreted by the Network layer.
    """

    TYPE = "CAPACITOR"

    __slots__ = (
        "_terminal",
        "_reactive_power_injection_mvar",
        "_in_service",
    )

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        terminal: Terminal | None = None,
        reactive_power_injection_mvar: float = 0.0,
        bus: Any = None,
        in_service: bool = True,
    ) -> None:
        """
        Construct a shunt capacitor.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable capacitor name.

        terminal:
            Optional pre-created Terminal owned by this Capacitor.

        reactive_power_injection_mvar:
            Reactive-power injection in MVAr.

        bus:
            Optional initial electrical endpoint.

            This parameter is retained as an engineering/API
            compatibility convenience. It is attached through the
            authoritative Terminal and is never stored independently.

        in_service:
            Whether the capacitor is in service.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Authoritative Terminal
        # --------------------------------------------------------

        if terminal is None:
            self._terminal = Terminal(
                owner=self,
                role="terminal",
            )
        else:
            if not isinstance(terminal, Terminal):
                raise TypeError(
                    "terminal must be a Terminal."
                )

            if terminal.owner is not self:
                raise ValueError(
                    "terminal owner must be this Capacitor."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "Capacitor terminal role must be 'terminal'."
                )

            self._terminal = terminal

        # --------------------------------------------------------
        # Initial endpoint
        # --------------------------------------------------------

        if bus is not None:
            self._terminal.attach(bus)

        # --------------------------------------------------------
        # Electrical parameters
        # --------------------------------------------------------

        self._reactive_power_injection_mvar = (
            self._validate_finite(
                reactive_power_injection_mvar,
                "reactive_power_injection_mvar",
            )
        )

        self._in_service = self._validate_bool(
            in_service,
            "in_service",
        )

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """
        return self.TYPE

    # ============================================================
    # TERMINAL
    # ============================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative Capacitor Terminal.

        The returned Terminal object is the connection authority.
        """
        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return the authoritative terminal collection.
        """
        return (self._terminal,)

    # ============================================================
    # ENDPOINT / BUS
    # ============================================================

    @property
    def endpoint(self) -> Any | None:
        """
        Return the endpoint currently owned by the Terminal.
        """
        return self._terminal.endpoint

    @property
    def bus(self) -> Any | None:
        """
        Return the current electrical endpoint.

        This is a read-only convenience alias.

        The Capacitor does not store a separate bus reference.
        """
        return self._terminal.endpoint

    # ============================================================
    # CONNECTION
    # ============================================================

    def connect(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach the Capacitor Terminal to an endpoint.

        Endpoint mutation is delegated to Terminal.attach().
        """
        self._terminal.attach(endpoint)

    def disconnect(self) -> None:
        """
        Detach the Capacitor Terminal.

        Endpoint mutation is delegated to Terminal.detach().
        """
        self._terminal.detach()

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Capacitor Terminal is connected.
        """
        return self._terminal.is_connected

    # ============================================================
    # REACTIVE POWER
    # ============================================================

    @property
    def reactive_power_injection_mvar(self) -> float:
        """
        Return reactive-power injection in MVAr.

        Positive values represent injection into the network.
        """
        return self._reactive_power_injection_mvar

    @reactive_power_injection_mvar.setter
    def reactive_power_injection_mvar(
        self,
        value: float,
    ) -> None:
        self._reactive_power_injection_mvar = (
            self._validate_finite(
                value,
                "reactive_power_injection_mvar",
            )
        )

    @property
    def q_injection_mvar(self) -> float:
        """
        Return reactive-power injection in MVAr.

        Compatibility/convenience alias.
        """
        return self._reactive_power_injection_mvar

    @q_injection_mvar.setter
    def q_injection_mvar(
        self,
        value: float,
    ) -> None:
        self.reactive_power_injection_mvar = value

    @property
    def reactive_power_mvar(self) -> float:
        """
        Return reactive-power injection in MVAr.

        Engineering convenience alias.
        """
        return self._reactive_power_injection_mvar

    @reactive_power_mvar.setter
    def reactive_power_mvar(
        self,
        value: float,
    ) -> None:
        self.reactive_power_injection_mvar = value

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the capacitor is in service.
        """
        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = self._validate_bool(
            value,
            "in_service",
        )

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the capacitor is in service.
        """
        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the capacitor is out of service.
        """
        return not self._in_service

    def put_in_service(self) -> None:
        """
        Place the capacitor in service.
        """
        self._in_service = True

    def take_out_of_service(self) -> None:
        """
        Take the capacitor out of service.
        """
        self._in_service = False

    # ============================================================
    # CONDUCTION / AVAILABILITY
    # ============================================================

    @property
    def conducts(self) -> bool:
        """
        Return whether the capacitor is electrically active.

        A capacitor is considered active when it is in service.
        Connectivity/topology is independently represented by
        Terminal.is_connected.
        """
        return self._in_service

    # ============================================================
    # INJECTION INTERFACE
    # ============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return active and reactive network injection.

        Returns
        -------
        tuple[float, float]
            (P_MW, Q_MVAr)

        The capacitor injects no active power.

        When in service:

            (0.0, reactive_power_injection_mvar)

        When out of service:

            (0.0, 0.0)
        """

        if not self._in_service:
            return (0.0, 0.0)

        return (
            0.0,
            self._reactive_power_injection_mvar,
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Capacitor-specific domain invariants.

        Network topology is deliberately not validated here.
        """

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Capacitor terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                "Capacitor terminal owner must be this Capacitor."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "Capacitor terminal role must be 'terminal'."
            )

        self._terminal.validate()

        self._reactive_power_injection_mvar = (
            self._validate_finite(
                self._reactive_power_injection_mvar,
                "reactive_power_injection_mvar",
            )
        )

        self._in_service = self._validate_bool(
            self._in_service,
            "in_service",
        )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Capacitor diagnostic information.

        Endpoint information is obtained from Terminal.
        """

        endpoint = self._terminal.endpoint

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "reactive_power_injection_mvar":
                self._reactive_power_injection_mvar,
            "in_service": self._in_service,
            "terminal_role": self._terminal.role,
            "endpoint":
                getattr(endpoint, "id", None)
                if endpoint is not None
                else None,
            "is_connected":
                self._terminal.is_connected,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Capacitor "
            f"id={self.id}, "
            f"q={self._reactive_power_injection_mvar}, "
            f"in_service={self._in_service}>"
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
        Convert a value to float and require it to be finite.
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

        if not numeric == numeric:
            raise ValueError(
                f"{name} must be finite."
            )

        if numeric in (
            float("inf"),
            float("-inf"),
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return numeric

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a strict boolean.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Capacitor",
]
