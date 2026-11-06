# ============================================================
# File: core/model/battery.py
# GridForge V2 — Battery Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Battery Model
============================

Authoritative electrical-domain model for a battery energy
storage element.

Architecture
------------

    ElectricalObject
           │
           ▼
        Battery
           │
           ├── Terminal
           │      └── endpoint
           │
           ├── electrical operating state
           │
           └── energy/SOC state

The Battery owns exactly one authoritative Terminal.

The Terminal owns the electrical endpoint reference.

The Battery does not maintain a duplicate bus or endpoint
reference.

Responsibilities
----------------

Battery owns:

    - electrical operating power
    - charge/discharge limits
    - energy capacity
    - state of charge
    - SOC limits
    - service state
    - authoritative Terminal

Battery does NOT own:

    - Network topology resolution
    - bus indexing
    - Y-bus construction
    - load-flow solving
    - short-circuit calculation
    - protection coordination
    - UI/SLD state
    - rendering
    - persistence orchestration
    - dynamic time integration

Dynamic simulation services may update the Battery state through
the appropriate Application/Simulation contracts.

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

Electrical connection therefore uses:

    connect(endpoint) -> Terminal.attach(endpoint)
    disconnect()      -> Terminal.detach()

Service state is deliberately separate:

    put_in_service()
    take_out_of_service()

Power convention
----------------

Positive active power represents injection into the network.

Therefore:

    P > 0  -> battery discharging / injecting power
    P < 0  -> battery charging / absorbing power

Reactive-power sign follows the GridForge injection convention:

    Q > 0  -> reactive-power injection
    Q < 0  -> reactive-power absorption

SOC convention
--------------

SOC is represented as a fraction:

    0.0 <= SOC <= 1.0

The battery energy state is represented by:

    energy_capacity_mwh

The current stored energy is:

    SOC * energy_capacity_mwh

No time-based SOC integration is performed by this model.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Battery(ElectricalObject, Injection):
    """
    Battery energy-storage electrical-domain model.

    The Battery is a one-terminal electrical injection/storage
    element.

    Electrical connectivity is represented exclusively by the
    authoritative Terminal.

    SOC and energy are local battery state; their time evolution
    belongs to the appropriate simulation/application layer.
    """

    TYPE = "BATTERY"

    __slots__ = (
        "_terminal",
        "_p_mw",
        "_q_mvar",
        "_max_charge_mw",
        "_max_discharge_mw",
        "_energy_capacity_mwh",
        "_soc",
        "_soc_min",
        "_soc_max",
        "_in_service",
    )

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        terminal: Terminal | None = None,
        endpoint: Any = None,
        bus: Any = None,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        max_charge_mw: float = 0.0,
        max_discharge_mw: float = 0.0,
        energy_capacity_mwh: float = 0.0,
        soc: float = 1.0,
        soc_min: float = 0.0,
        soc_max: float = 1.0,
        in_service: bool = True,
    ) -> None:
        """
        Construct a Battery.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable battery name.

        terminal:
            Optional pre-created Terminal owned by this Battery.

        endpoint:
            Optional initial electrical endpoint.

            This is attached through Terminal.attach() and is not
            stored independently.

        bus:
            Compatibility alias for endpoint.

            `endpoint` takes precedence if both are supplied.

        p_mw:
            Active-power injection in MW.

            Positive = discharge/injection.
            Negative = charge/absorption.

        q_mvar:
            Reactive-power injection in MVAr.

        max_charge_mw:
            Maximum charging power magnitude in MW.

        max_discharge_mw:
            Maximum discharging/injection power in MW.

        energy_capacity_mwh:
            Battery energy capacity in MWh.

        soc:
            State of charge as a fraction from 0.0 to 1.0.

        soc_min:
            Minimum permitted SOC.

        soc_max:
            Maximum permitted SOC.

        in_service:
            Whether the battery is in service.
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
            if not isinstance(
                terminal,
                Terminal,
            ):
                raise TypeError(
                    "terminal must be a Terminal."
                )

            if terminal.owner is not self:
                raise ValueError(
                    "terminal owner must be this Battery."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "Battery terminal role must be 'terminal'."
                )

            self._terminal = terminal

        # --------------------------------------------------------
        # Initial endpoint
        # --------------------------------------------------------

        if endpoint is not None and bus is not None:
            if endpoint is not bus:
                raise ValueError(
                    "Specify either endpoint or bus, not two "
                    "different electrical endpoints."
                )

        initial_endpoint = (
            endpoint
            if endpoint is not None
            else bus
        )

        if initial_endpoint is not None:
            self._terminal.attach(initial_endpoint)

        # --------------------------------------------------------
        # Electrical operating state
        # --------------------------------------------------------

        self._p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self._q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        self._max_charge_mw = self._validate_non_negative(
            max_charge_mw,
            "max_charge_mw",
        )

        self._max_discharge_mw = self._validate_non_negative(
            max_discharge_mw,
            "max_discharge_mw",
        )

        # --------------------------------------------------------
        # Energy / SOC state
        # --------------------------------------------------------

        self._energy_capacity_mwh = (
            self._validate_non_negative(
                energy_capacity_mwh,
                "energy_capacity_mwh",
            )
        )

        self._soc_min = self._validate_soc(
            soc_min,
            "soc_min",
        )

        self._soc_max = self._validate_soc(
            soc_max,
            "soc_max",
        )

        if self._soc_min > self._soc_max:
            raise ValueError(
                "soc_min must be less than or equal to soc_max."
            )

        self._soc = self._validate_soc(
            soc,
            "soc",
        )

        if not (
            self._soc_min
            <= self._soc
            <= self._soc_max
        ):
            raise ValueError(
                "soc must be between soc_min and soc_max."
            )

        # --------------------------------------------------------
        # Service state
        # --------------------------------------------------------

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
        Return the authoritative Battery Terminal.
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

        Compatibility/convenience read-only alias.

        No separate bus state is maintained by Battery.
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
        Electrically connect the Battery.

        This operation modifies Terminal connectivity only.
        It does not change Battery service state.
        """
        self._terminal.attach(endpoint)

    def disconnect(self) -> None:
        """
        Electrically disconnect the Battery.

        This operation modifies Terminal connectivity only.
        It does not change Battery service state.
        """
        self._terminal.detach()

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Battery Terminal is connected.
        """
        return self._terminal.is_connected

    # ============================================================
    # ACTIVE POWER
    # ============================================================

    @property
    def p_mw(self) -> float:
        """
        Return active-power injection in MW.

        Positive = discharge/injection.
        Negative = charge/absorption.
        """
        return self._p_mw

    @p_mw.setter
    def p_mw(
        self,
        value: float,
    ) -> None:
        numeric = self._validate_finite(
            value,
            "p_mw",
        )

        self._validate_power_limit(
            numeric,
            "p_mw",
        )

        self._p_mw = numeric

    @property
    def active_power_mw(self) -> float:
        """
        Return active-power injection in MW.
        """
        return self._p_mw

    @active_power_mw.setter
    def active_power_mw(
        self,
        value: float,
    ) -> None:
        self.p_mw = value

    # ============================================================
    # REACTIVE POWER
    # ============================================================

    @property
    def q_mvar(self) -> float:
        """
        Return reactive-power injection in MVAr.
        """
        return self._q_mvar

    @q_mvar.setter
    def q_mvar(
        self,
        value: float,
    ) -> None:
        self._q_mvar = self._validate_finite(
            value,
            "q_mvar",
        )

    @property
    def reactive_power_mvar(self) -> float:
        """
        Return reactive-power injection in MVAr.
        """
        return self._q_mvar

    @reactive_power_mvar.setter
    def reactive_power_mvar(
        self,
        value: float,
    ) -> None:
        self.q_mvar = value

    # ============================================================
    # CHARGE / DISCHARGE LIMITS
    # ============================================================

    @property
    def max_charge_mw(self) -> float:
        """
        Return maximum charging-power magnitude in MW.
        """
        return self._max_charge_mw

    @max_charge_mw.setter
    def max_charge_mw(
        self,
        value: float,
    ) -> None:
        numeric = self._validate_non_negative(
            value,
            "max_charge_mw",
        )

        self._max_charge_mw = numeric
        self._validate_power_limit(
            self._p_mw,
            "p_mw",
        )

    @property
    def max_discharge_mw(self) -> float:
        """
        Return maximum discharging-power magnitude in MW.
        """
        return self._max_discharge_mw

    @max_discharge_mw.setter
    def max_discharge_mw(
        self,
        value: float,
    ) -> None:
        numeric = self._validate_non_negative(
            value,
            "max_discharge_mw",
        )

        self._max_discharge_mw = numeric
        self._validate_power_limit(
            self._p_mw,
            "p_mw",
        )

    # ============================================================
    # ENERGY CAPACITY
    # ============================================================

    @property
    def energy_capacity_mwh(self) -> float:
        """
        Return nominal energy capacity in MWh.
        """
        return self._energy_capacity_mwh

    @energy_capacity_mwh.setter
    def energy_capacity_mwh(
        self,
        value: float,
    ) -> None:
        self._energy_capacity_mwh = (
            self._validate_non_negative(
                value,
                "energy_capacity_mwh",
            )
        )

    # ============================================================
    # STATE OF CHARGE
    # ============================================================

    @property
    def soc(self) -> float:
        """
        Return state of charge as a fraction.
        """
        return self._soc

    @soc.setter
    def soc(
        self,
        value: float,
    ) -> None:
        numeric = self._validate_soc(
            value,
            "soc",
        )

        if not (
            self._soc_min
            <= numeric
            <= self._soc_max
        ):
            raise ValueError(
                "soc must be between soc_min and soc_max."
            )

        self._soc = numeric

    @property
    def state_of_charge(self) -> float:
        """
        Return state of charge as a fraction.
        """
        return self._soc

    @state_of_charge.setter
    def state_of_charge(
        self,
        value: float,
    ) -> None:
        self.soc = value

    @property
    def soc_percent(self) -> float:
        """
        Return state of charge as a percentage.
        """
        return self._soc * 100.0

    @property
    def stored_energy_mwh(self) -> float:
        """
        Return current stored energy in MWh.

        Calculated from SOC and nominal energy capacity.
        """
        return (
            self._soc
            * self._energy_capacity_mwh
        )

    @property
    def available_energy_mwh(self) -> float:
        """
        Return energy available above minimum SOC.
        """
        return (
            max(
                0.0,
                self._soc - self._soc_min,
            )
            * self._energy_capacity_mwh
        )

    @property
    def remaining_capacity_mwh(self) -> float:
        """
        Return remaining storage capacity below maximum SOC.
        """
        return (
            max(
                0.0,
                self._soc_max - self._soc,
            )
            * self._energy_capacity_mwh
        )

    @property
    def soc_min(self) -> float:
        """
        Return minimum permitted SOC.
        """
        return self._soc_min

    @soc_min.setter
    def soc_min(
        self,
        value: float,
    ) -> None:
        numeric = self._validate_soc(
            value,
            "soc_min",
        )

        if numeric > self._soc_max:
            raise ValueError(
                "soc_min must be less than or equal to soc_max."
            )

        if numeric > self._soc:
            raise ValueError(
                "soc_min cannot be greater than the current soc."
            )

        self._soc_min = numeric

    @property
    def soc_max(self) -> float:
        """
        Return maximum permitted SOC.
        """
        return self._soc_max

    @soc_max.setter
    def soc_max(
        self,
        value: float,
    ) -> None:
        numeric = self._validate_soc(
            value,
            "soc_max",
        )

        if numeric < self._soc_min:
            raise ValueError(
                "soc_max must be greater than or equal to soc_min."
            )

        if numeric < self._soc:
            raise ValueError(
                "soc_max cannot be less than the current soc."
            )

        self._soc_max = numeric

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the Battery is in service.
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
        Return True when the Battery is in service.
        """
        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the Battery is out of service.
        """
        return not self._in_service

    def put_in_service(self) -> None:
        """
        Place the Battery in service.

        This is deliberately separate from electrical connection.
        """
        self._in_service = True

    def take_out_of_service(self) -> None:
        """
        Take the Battery out of service.

        This is deliberately separate from electrical connection.
        """
        self._in_service = False

    # ============================================================
    # ELECTRICAL ACTIVITY
    # ============================================================

    @property
    def conducts(self) -> bool:
        """
        Return whether the Battery is electrically active.

        Service state and terminal connectivity are independent
        concepts.

        A Battery is electrically active only when it is in service
        and connected to an endpoint.
        """
        return (
            self._in_service
            and self._terminal.is_connected
        )

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

        An out-of-service Battery contributes zero injection.

        The Network/solver layer remains responsible for deciding
        how this injection participates in the solved network.
        """

        if not self._in_service:
            return (0.0, 0.0)

        return (
            self._p_mw,
            self._q_mvar,
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Battery-specific domain invariants.

        Network topology is deliberately not resolved here.
        """

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Battery terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                "Battery terminal owner must be this Battery."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "Battery terminal role must be 'terminal'."
            )

        self._terminal.validate()

        self._p_mw = self._validate_finite(
            self._p_mw,
            "p_mw",
        )

        self._q_mvar = self._validate_finite(
            self._q_mvar,
            "q_mvar",
        )

        self._max_charge_mw = (
            self._validate_non_negative(
                self._max_charge_mw,
                "max_charge_mw",
            )
        )

        self._max_discharge_mw = (
            self._validate_non_negative(
                self._max_discharge_mw,
                "max_discharge_mw",
            )
        )

        self._energy_capacity_mwh = (
            self._validate_non_negative(
                self._energy_capacity_mwh,
                "energy_capacity_mwh",
            )
        )

        self._soc_min = self._validate_soc(
            self._soc_min,
            "soc_min",
        )

        self._soc_max = self._validate_soc(
            self._soc_max,
            "soc_max",
        )

        self._soc = self._validate_soc(
            self._soc,
            "soc",
        )

        if self._soc_min > self._soc_max:
            raise ValueError(
                "soc_min must be less than or equal to soc_max."
            )

        if not (
            self._soc_min
            <= self._soc
            <= self._soc_max
        ):
            raise ValueError(
                "soc must be between soc_min and soc_max."
            )

        self._validate_power_limit(
            self._p_mw,
            "p_mw",
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
        Return structured Battery diagnostic information.

        Endpoint information is obtained from Terminal.
        """

        endpoint = self._terminal.endpoint

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "p_mw": self._p_mw,
            "q_mvar": self._q_mvar,
            "max_charge_mw": self._max_charge_mw,
            "max_discharge_mw": self._max_discharge_mw,
            "energy_capacity_mwh":
                self._energy_capacity_mwh,
            "soc": self._soc,
            "soc_percent": self.soc_percent,
            "stored_energy_mwh":
                self.stored_energy_mwh,
            "soc_min": self._soc_min,
            "soc_max": self._soc_max,
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
            f"<Battery "
            f"id={self.id}, "
            f"p={self._p_mw}, "
            f"q={self._q_mvar}, "
            f"soc={self._soc}, "
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

        if not math.isfinite(numeric):
            raise ValueError(
                f"{name} must be finite."
            )

        return numeric

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite non-negative numeric value.
        """

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric < 0.0:
            raise ValueError(
                f"{name} must be greater than or equal to zero."
            )

        return numeric

    @classmethod
    def _validate_soc(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Validate SOC as a fraction in [0.0, 1.0].
        """

        numeric = cls._validate_finite(
            value,
            name,
        )

        if not 0.0 <= numeric <= 1.0:
            raise ValueError(
                f"{name} must be between 0.0 and 1.0."
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

    def _validate_power_limit(
        self,
        value: float,
        name: str,
    ) -> float:
        """
        Validate active power against the Battery limits.

        Positive P is discharge.
        Negative P is charge.

        A zero configured limit means that direction is disabled.
        """

        numeric = self._validate_finite(
            value,
            name,
        )

        if numeric > self._max_discharge_mw:
            raise ValueError(
                f"{name} exceeds max_discharge_mw."
            )

        if numeric < -self._max_charge_mw:
            raise ValueError(
                f"{name} exceeds max_charge_mw."
            )

        return numeric


__all__ = [
    "Battery",
]
