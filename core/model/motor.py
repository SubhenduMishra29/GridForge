# ============================================================
# File: core/model/motor.py
# GridForge V2 — Motor Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Motor Model
==========================

Authoritative electrical-domain model for a motor load.

Architecture
------------

    ElectricalObject
          │
          ▼
        Motor
          │
          └── Terminal
                └── endpoint

The Motor owns exactly one authoritative Terminal.

The Terminal owns the electrical endpoint reference.

The Motor does not maintain an independent bus or endpoint
state.

Motor operating quantities
--------------------------

The Motor stores:

    p
        Active-power consumption.

    q
        Reactive-power consumption.

    rated_mva
        Rated apparent power.

    rated_kv
        Rated voltage.

    power_factor
        Nameplate / operating power factor.

    efficiency
        Motor efficiency.

    slip
        Motor slip.

    starting_current_pu
        Starting current in per-unit.

    running
        Running state.

    in_service
        Operational service state.

Power convention
----------------

Motor p and q are positive consumption quantities.

Therefore the electrical-network injection is:

    P_network = -p
    Q_network = -q

A stopped or out-of-service Motor contributes:

    (0, 0)

Terminal contract
-----------------

The canonical Terminal contract is:

    Terminal
    ├── owner
    ├── role
    ├── endpoint
    ├── attach()
    ├── detach()
    ├── is_connected
    └── validate()

Therefore:

    connect_endpoint(endpoint)
        -> Terminal.attach(endpoint)

    disconnect_endpoint()
        -> Terminal.detach()

Electrical connectivity and operational state are deliberately
separate.

    connect_endpoint()
    disconnect_endpoint()

operate on electrical connectivity.

    put_in_service()
    take_out_of_service()

operate on service state.

The legacy Motor connect()/disconnect() service aliases are
retained only for compatibility with the existing model API.

Network topology
----------------

Motor does not:

    - register itself with a Network
    - mutate Bus topology
    - construct Y-Bus matrices
    - perform load flow
    - perform short-circuit analysis
    - perform protection analysis
    - perform dynamic integration
    - maintain UI/SLD state

Those responsibilities belong to the appropriate Core
subsystems and Application layer.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Motor(ElectricalObject, Injection):
    """
    Electrical-domain motor model.

    Motor power values represent positive consumption.

    Network injection is therefore negative while the motor is
    operating.

    The Motor has exactly one authoritative Terminal.
    """

    TYPE = "MOTOR"

    def __init__(
        self,
        id: str,
        endpoint: Any = None,
        *,
        bus: Any = None,
        terminal: Terminal | None = None,
        rated_mva: float = 1.0,
        rated_kv: float = 1.0,
        power_factor: float = 0.9,
        p: float = 0.0,
        q: float = 0.0,
        efficiency: float = 1.0,
        slip: float = 0.0,
        starting_current_pu: float = 0.0,
        running: bool = False,
        in_service: bool = True,
        name: str = "",
    ) -> None:
        """
        Construct a Motor.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint:
            Initial electrical endpoint.

        bus:
            Compatibility alias for endpoint.

        terminal:
            Optional pre-created Terminal. If supplied, it must
            belong to this Motor and have role ``"terminal"``.

        rated_mva:
            Motor rated apparent power.

        rated_kv:
            Motor rated voltage.

        power_factor:
            Motor power factor.

        p:
            Active-power consumption.

        q:
            Reactive-power consumption.

        efficiency:
            Motor efficiency.

        slip:
            Motor slip.

        starting_current_pu:
            Starting current in per-unit.

        running:
            Initial running state.

        in_service:
            Initial service state.

        name:
            Human-readable Motor name.
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
                f"Motor '{self.id}' received both "
                "'endpoint' and 'bus' with different values."
            )

        if endpoint is None:
            endpoint = bus

        # --------------------------------------------------------
        # NAMEPLATE / ELECTRICAL PARAMETERS
        # --------------------------------------------------------

        self.rated_mva = self._validate_positive(
            rated_mva,
            "rated_mva",
        )

        self.rated_kv = self._validate_positive(
            rated_kv,
            "rated_kv",
        )

        self.power_factor = (
            self._validate_power_factor(
                power_factor,
            )
        )

        # --------------------------------------------------------
        # OPERATING ELECTRICAL STATE
        # --------------------------------------------------------

        self.p = self._validate_non_negative(
            p,
            "p",
        )

        self.q = self._validate_non_negative(
            q,
            "q",
        )

        self.efficiency = (
            self._validate_efficiency(
                efficiency,
            )
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

        # --------------------------------------------------------
        # SERVICE / RUNNING STATE
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # AUTHORITATIVE TERMINAL
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
                    f"Motor '{self.id}' terminal owner "
                    "must be this Motor."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "Motor terminal role must be "
                    "'terminal'."
                )

            self._terminal = terminal

        # --------------------------------------------------------
        # INITIAL ELECTRICAL CONNECTION
        # --------------------------------------------------------

        if endpoint is not None:
            self._terminal.attach(
                endpoint
            )

        # --------------------------------------------------------
        # COMMON VALIDATION CONTRACT
        # --------------------------------------------------------

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
        Return the authoritative Motor Terminal.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return the Motor's authoritative terminal collection.
        """

        return (
            self._terminal,
        )

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    @property
    def endpoint(self) -> Any:
        """
        Return the authoritative physical endpoint.

        Terminal.endpoint is the source of truth.
        """

        return self._terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor for the terminal endpoint.

        This is derived state and is not authoritative.
        """

        return self._terminal.endpoint

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Motor terminal is connected.
        """

        return self._terminal.is_connected

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the Motor Terminal to an electrical endpoint.

        Global network topology is not modified here.
        """

        if endpoint is None:
            raise ValueError(
                f"Motor '{self.id}' endpoint cannot be None."
            )

        self._terminal.attach(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Motor Terminal locally.
        """

        self._terminal.detach()

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the Motor is in service.
        """

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the Motor is out of service.
        """

        return not self.in_service

    def put_in_service(self) -> None:
        """
        Place the Motor in service.

        Terminal connectivity is unchanged.
        """

        self.in_service = True

    def take_out_of_service(self) -> None:
        """
        Take the Motor out of service.

        Terminal connectivity is unchanged.
        """

        self.in_service = False

    # ------------------------------------------------------------
    # Compatibility aliases
    # ------------------------------------------------------------

    def connect(self) -> None:
        """
        Compatibility alias for put_in_service().

        This method changes service state only.

        New code should use:

            connect_endpoint(endpoint)

        for electrical connectivity.
        """

        self.put_in_service()

    def disconnect(self) -> None:
        """
        Compatibility alias for take_out_of_service().

        This method changes service state only.

        New code should use:

            disconnect_endpoint()

        for electrical connectivity.
        """

        self.take_out_of_service()

    # ============================================================
    # RUNNING STATE
    # ============================================================

    @property
    def is_running(self) -> bool:
        """
        Return True when the Motor is running.
        """

        return self.running

    @property
    def is_stopped(self) -> bool:
        """
        Return True when the Motor is stopped.
        """

        return not self.running

    def start(self) -> None:
        """
        Start the Motor.

        A Motor cannot start while out of service.
        """

        if not self.in_service:
            raise RuntimeError(
                f"Motor '{self.id}' cannot start "
                "while out of service."
            )

        self.running = True

    def stop(self) -> None:
        """
        Stop the Motor.
        """

        self.running = False

    # ============================================================
    # INJECTION CONTRACT
    # ============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network injection.

        Motor p/q represent positive consumption.

        Therefore:

            operating Motor -> (-p, -q)

        A stopped or out-of-service Motor returns:

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

    # ============================================================
    # POWER STATE
    # ============================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set active/reactive motor consumption.
        """

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
        """
        Set active motor consumption.
        """

        self.p = self._validate_non_negative(
            p,
            "p",
        )

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set reactive motor consumption.
        """

        self.q = self._validate_non_negative(
            q,
            "q",
        )

    @property
    def active_power(self) -> float:
        """
        Return active-power consumption.
        """

        return self.p

    @property
    def reactive_power(self) -> float:
        """
        Return reactive-power consumption.
        """

        return self.q

    # ============================================================
    # NAMEPLATE / OPERATING PARAMETERS
    # ============================================================

    def set_power_factor(
        self,
        power_factor: float,
    ) -> None:
        """
        Set operating power factor.
        """

        self.power_factor = (
            self._validate_power_factor(
                power_factor,
            )
        )

    def set_efficiency(
        self,
        efficiency: float,
    ) -> None:
        """
        Set motor efficiency.
        """

        self.efficiency = (
            self._validate_efficiency(
                efficiency,
            )
        )

    def set_slip(
        self,
        slip: float,
    ) -> None:
        """
        Set motor slip.
        """

        self.slip = self._validate_slip(
            slip,
        )

    def set_starting_current(
        self,
        starting_current_pu: float,
    ) -> None:
        """
        Set starting current in per-unit.
        """

        self.starting_current_pu = (
            self._validate_non_negative(
                starting_current_pu,
                "starting_current_pu",
            )
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Motor-local engineering invariants.

        Network topology resolution remains outside the Motor.
        """

        self.rated_mva = self._validate_positive(
            self.rated_mva,
            "rated_mva",
        )

        self.rated_kv = self._validate_positive(
            self.rated_kv,
            "rated_kv",
        )

        self.power_factor = (
            self._validate_power_factor(
                self.power_factor,
            )
        )

        self.p = self._validate_non_negative(
            self.p,
            "p",
        )

        self.q = self._validate_non_negative(
            self.q,
            "q",
        )

        self.efficiency = (
            self._validate_efficiency(
                self.efficiency,
            )
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

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Motor terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Motor '{self.id}' terminal owner "
                "must be this Motor."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "Motor terminal role must be "
                "'terminal'."
            )

        self._terminal.validate()

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Motor diagnostics.

        Endpoint information is obtained exclusively from the
        authoritative Terminal.
        """

        endpoint = self._terminal.endpoint

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal,

            "endpoint": (
                endpoint.id
                if endpoint is not None
                and hasattr(endpoint, "id")
                else endpoint
            ),

            "bus": (
                endpoint.id
                if endpoint is not None
                and hasattr(endpoint, "id")
                else endpoint
            ),

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

            "is_connected":
                self._terminal.is_connected,

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
            f"<Motor "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"running={self.running}, "
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
        Convert value to float and require it to be finite.
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
        Validate a strictly positive finite value.
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

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite non-negative value.
        """

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric < 0.0:
            raise ValueError(
                f"{name} must be greater than or equal "
                "to zero."
            )

        return numeric

    @classmethod
    def _validate_power_factor(
        cls,
        value: float,
    ) -> float:
        """
        Validate power factor.

        Power factor is represented as a positive fraction
        between 0 and 1 inclusive.
        """

        numeric = cls._validate_finite(
            value,
            "power_factor",
        )

        if not 0.0 < numeric <= 1.0:
            raise ValueError(
                "power_factor must be greater than "
                "zero and less than or equal to 1.0."
            )

        return numeric

    @classmethod
    def _validate_efficiency(
        cls,
        value: float,
    ) -> float:
        """
        Validate motor efficiency as a fraction.
        """

        numeric = cls._validate_finite(
            value,
            "efficiency",
        )

        if not 0.0 < numeric <= 1.0:
            raise ValueError(
                "efficiency must be greater than "
                "zero and less than or equal to 1.0."
            )

        return numeric

    @classmethod
    def _validate_slip(
        cls,
        value: float,
    ) -> float:
        """
        Validate motor slip.

        Slip is represented as a fraction and must be within
        the physical interval [0, 1).
        """

        numeric = cls._validate_finite(
            value,
            "slip",
        )

        if not 0.0 <= numeric < 1.0:
            raise ValueError(
                "slip must be greater than or equal to "
                "zero and less than 1.0."
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
    "Motor",
]
