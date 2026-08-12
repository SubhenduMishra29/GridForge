# core/model/branch.py

"""
GridForge Branch Model
======================

GridForge Model Layer V2

Defines the common two-terminal electrical Branch model.

Architecture
------------

A Branch represents a generic two-terminal electrical branch:

    Equipment A
         │
      Terminal
         │
       Branch
         │
      Terminal
         │
    Equipment B

Typical implementations include:

- Transmission lines
- Transformers
- Series compensation elements
- FACTS-related branch elements
- Future two-terminal electrical equipment

The Branch owns its two physical Terminal objects:

    from_terminal
    to_terminal

Each Terminal contains the local physical connection endpoint.

The endpoint may be:

- a Bus;
- another Terminal;
- another network-supported endpoint.

The Branch does NOT own global network topology.

The network layer is responsible for:

- registering equipment;
- validating complete connections;
- constructing physical topology;
- deriving electrical topology;
- applying equipment operational state to
  the derived network representation.

Responsibilities
----------------

The Branch model provides:

- Two-terminal physical connectivity.
- Common branch electrical parameters.
- Series impedance representation.
- Series admittance representation.
- Total shunt admittance representation.
- Transformer-compatible tap representation.
- Phase-shift representation.
- Equipment rating storage.
- In-service operational state.
- Local parameter validation.
- Diagnostic information.

The Branch does NOT:

- Build Y-bus matrices.
- Perform load-flow calculations.
- Perform Newton-Raphson iterations.
- Calculate short-circuit currents.
- Perform contingency studies.
- Perform protection calculations.
- Perform dynamic simulation.
- Manage GUI geometry.
- Own global network topology.

Numerical interpretation of branch parameters belongs to the
appropriate network/solver/analysis layers.

Electrical Parameters
---------------------

All electrical parameters use the GridForge established
per-unit conventions:

    r
        Series resistance in per-unit.

    x
        Series reactance in per-unit.

    b
        Total shunt susceptance in per-unit.

        For a standard transmission-line π model, the network/Y-bus
        layer applies B/2 at each terminal.

    tap
        Transformer-compatible magnitude tap ratio.

        Normal transmission-line value: 1.0.

    shift
        Phase-shifting angle in radians.

        Normal transmission-line value: 0.0.

The exact Y-bus stamping convention, including transformer tap-side
and phase-shift sign convention, belongs to the network/solver
contract and is not implemented here.

Operational State
-----------------

``in_service`` represents whether the branch is currently available
to the network study.

``trip()`` and ``close()`` modify only the local operational state.

They do not rebuild Y-bus matrices or execute network studies.

Connectivity
------------

The authoritative local connection references are:

    from_terminal.endpoint
    to_terminal.endpoint

The compatibility properties:

    from_bus
    to_bus

are derived from the Terminal interface and must not be treated as
independent topology state.

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The Branch model intentionally remains generic.

Specialized branch equipment should extend this class rather than
introducing topology or numerical solver responsibilities into it.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# BRANCH MODEL
# =====================================================================

class Branch(ElectricalObject):
    """
    Generic two-terminal electrical branch.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    endpoint_from : object, optional
        From-side electrical endpoint.

        May be a Bus-like object, another Terminal, or another
        network-supported endpoint.

        ``None`` is allowed so that equipment may be created before
        network assembly.

    endpoint_to : object, optional
        To-side electrical endpoint.

        ``None`` is allowed so that equipment may be created before
        network assembly.

    r : float
        Series resistance in per-unit.

    x : float
        Series reactance in per-unit.

    b : float, optional
        Total shunt susceptance in per-unit.

    name : str, optional
        Human-readable branch name.

    rate_mva : float, optional
        Continuous/nominal thermal rating in MVA.

    tap : float, optional
        Transformer-compatible magnitude tap ratio.

        Normal transmission-line value: 1.0.

    shift : float, optional
        Phase-shifting angle in radians.

        Normal transmission-line value: 0.0.

    Notes
    -----
    The two Terminal objects are authoritative.

    The Branch does not maintain a second independent copy of its
    endpoint state.

    ``from_bus`` and ``to_bus`` are derived compatibility accessors.
    """

    def __init__(
        self,
        id: str,
        endpoint_from=None,
        endpoint_to=None,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
        tap: float = 1.0,
        shift: float = 0.0,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # PHYSICAL TERMINALS
        # =============================================================

        self.from_terminal = self._create_terminal(
            endpoint=endpoint_from,
        )

        self.to_terminal = self._create_terminal(
            endpoint=endpoint_to,
        )

        # A branch cannot use the same Terminal object at both ends.
        if self.from_terminal is self.to_terminal:
            raise ValueError(
                f"Branch '{self.id}' cannot use the same "
                "Terminal object for both ends."
            )

        # =============================================================
        # ELECTRICAL PARAMETERS
        # =============================================================

        self.r = float(r)
        self.x = float(x)
        self.b = float(b)

        # =============================================================
        # TRANSFORMER-COMPATIBLE PARAMETERS
        # =============================================================

        self.tap = float(tap)
        self.shift = float(shift)

        # =============================================================
        # EQUIPMENT DATA
        # =============================================================

        self.rate_mva = float(rate_mva)

        # =============================================================
        # OPERATIONAL STATE
        # =============================================================

        self.in_service = True

        # =============================================================
        # LOCAL VALIDATION
        # =============================================================

        self._validate_parameters()

    # =================================================================
    # TERMINAL CREATION
    # =================================================================

    def _create_terminal(
        self,
        endpoint=None,
    ) -> Terminal:
        """
        Create or validate one physical Branch terminal.

        Parameters
        ----------
        endpoint :
            Initial local endpoint.

        Returns
        -------
        Terminal
            Terminal owned by this Branch.

        Notes
        -----
        An existing Terminal may be supplied.

        An existing Terminal must either:

        - have no owner, or
        - already belong to this Branch.

        A Terminal belonging to another equipment object cannot be
        silently reassigned.
        """

        if isinstance(endpoint, Terminal):

            terminal = endpoint

            if (
                terminal.owner is not None
                and terminal.owner is not self
            ):
                raise ValueError(
                    f"Branch '{self.id}' terminal already belongs "
                    "to another equipment object."
                )

            terminal.owner = self

            return terminal

        return Terminal(
            endpoint=endpoint,
            owner=self,
        )

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the physical terminal pair.

        Returns
        -------
        tuple
            ``(from_terminal, to_terminal)``
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the authoritative from-side endpoint.

        The returned object is not assumed to be a Bus.
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """
        Return the authoritative to-side endpoint.

        The returned object is not assumed to be a Bus.
        """

        return self.to_terminal.endpoint

    def endpoints(self) -> tuple:
        """
        Return the authoritative physical endpoint pair.

        Returns
        -------
        tuple
            ``(from_endpoint, to_endpoint)``
        """

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # =================================================================
    # BUS COMPATIBILITY
    # =================================================================

    @property
    def from_bus(self):
        """
        Return the Bus associated with the from-side terminal.

        This is a compatibility accessor derived through
        ``Terminal.bus``.

        The authoritative connection remains:

            self.from_terminal.endpoint
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the Bus associated with the to-side terminal.

        This is a compatibility accessor derived through
        ``Terminal.bus``.

        The authoritative connection remains:

            self.to_terminal.endpoint
        """

        return self.to_terminal.bus

    def buses(self) -> tuple:
        """
        Return the derived endpoint buses.

        Returns
        -------
        tuple
            ``(from_bus, to_bus)``

        Notes
        -----
        This method exists for compatibility with existing
        network/model consumers.

        It does not represent independent stored topology.
        """

        return (
            self.from_bus,
            self.to_bus,
        )

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both physical terminals have endpoints.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    @property
    def is_fully_connected(self) -> bool:
        """
        Alias for ``is_connected``.

        Provided for consistency with other two-terminal equipment.
        """

        return self.is_connected

    # =================================================================
    # TERMINAL CONNECTION
    # =================================================================

    def connect_from(self, endpoint) -> None:
        """
        Connect the from-side terminal locally.

        This changes only the Terminal endpoint reference.

        Global topology remains the responsibility of
        ``core/network``.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint) -> None:
        """
        Connect the to-side terminal locally.

        This changes only the Terminal endpoint reference.

        Global topology remains the responsibility of
        ``core/network``.
        """

        self.to_terminal.connect(endpoint)

    def disconnect_from(self) -> None:
        """
        Disconnect the from-side terminal locally.
        """

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """
        Disconnect the to-side terminal locally.
        """

        self.to_terminal.disconnect()

    # =================================================================
    # ELECTRICAL PROPERTIES
    # =================================================================

    @property
    def impedance(self) -> complex:
        """
        Return the series impedance.

        Z = R + jX
        """

        return complex(
            self.r,
            self.x,
        )

    @property
    def series_impedance(self) -> complex:
        """
        Alias for ``impedance``.
        """

        return self.impedance

    @property
    def admittance(self) -> complex:
        """
        Return the series admittance.

        Y = 1 / Z

        Notes
        -----
        This property exposes the mathematical series admittance.

        It does not perform Y-bus assembly or network stamping.
        """

        z = self.impedance

        if z == 0.0:
            raise ZeroDivisionError(
                f"Branch '{self.id}' has zero series impedance."
            )

        return 1.0 / z

    @property
    def series_admittance(self) -> complex:
        """
        Alias for ``admittance``.
        """

        return self.admittance

    @property
    def shunt_admittance(self) -> complex:
        """
        Return the total branch shunt admittance.

        Y_shunt = jB
        """

        return complex(
            0.0,
            self.b,
        )

    # =================================================================
    # PER-UNIT COMPATIBILITY
    # =================================================================

    @property
    def r_pu(self) -> float:
        """
        Return series resistance in per-unit.
        """

        return self.r

    @property
    def x_pu(self) -> float:
        """
        Return series reactance in per-unit.
        """

        return self.x

    @property
    def b_pu(self) -> float:
        """
        Return total shunt susceptance in per-unit.

        For a π-equivalent line, the network/Y-bus layer is
        responsible for applying B/2 at each terminal.
        """

        return self.b

    # =================================================================
    # TRANSFORMER COMPATIBILITY
    # =================================================================

    @property
    def tap_ratio(self) -> float:
        """
        Return the magnitude tap ratio.
        """

        return self.tap

    @property
    def phase_shift(self) -> float:
        """
        Return the phase-shift angle in radians.
        """

        return self.shift

    # =================================================================
    # OPERATIONAL STATE
    # =================================================================

    def trip(self) -> None:
        """
        Remove the branch from service.

        This changes only the local operational state.
        """

        self.in_service = False

    def close(self) -> None:
        """
        Return the branch to service.

        This changes only the local operational state.
        """

        self.in_service = True

    # =================================================================
    # STATUS
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the branch is in service.
        """

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the branch is out of service.
        """

        return not self.in_service

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_parameters(self) -> None:
        """
        Validate local branch parameters.

        This method performs object-level validation only.

        Network-level rules, electrical compatibility, voltage-level
        compatibility, topology rules, and study-specific limits
        belong to higher GridForge layers.
        """

        # -------------------------------------------------------------
        # Series resistance
        # -------------------------------------------------------------

        if not isfinite(self.r):
            raise ValueError(
                f"Branch '{self.id}' resistance must be finite."
            )

        if self.r < 0.0:
            raise ValueError(
                f"Branch '{self.id}' resistance cannot be negative."
            )

        # -------------------------------------------------------------
        # Series reactance
        # -------------------------------------------------------------

        if not isfinite(self.x):
            raise ValueError(
                f"Branch '{self.id}' reactance must be finite."
            )

        # -------------------------------------------------------------
        # Series impedance
        # -------------------------------------------------------------

        if self.r == 0.0 and self.x == 0.0:
            raise ValueError(
                f"Branch '{self.id}' cannot have zero series impedance."
            )

        # -------------------------------------------------------------
        # Shunt susceptance
        # -------------------------------------------------------------

        if not isfinite(self.b):
            raise ValueError(
                f"Branch '{self.id}' shunt susceptance must be finite."
            )

        # -------------------------------------------------------------
        # Tap ratio
        # -------------------------------------------------------------

        if not isfinite(self.tap):
            raise ValueError(
                f"Branch '{self.id}' tap ratio must be finite."
            )

        if self.tap <= 0.0:
            raise ValueError(
                f"Branch '{self.id}' tap ratio must be greater "
                "than zero."
            )

        # -------------------------------------------------------------
        # Phase shift
        # -------------------------------------------------------------

        if not isfinite(self.shift):
            raise ValueError(
                f"Branch '{self.id}' phase shift must be finite."
            )

        # -------------------------------------------------------------
        # Equipment rating
        # -------------------------------------------------------------

        if not isfinite(self.rate_mva):
            raise ValueError(
                f"Branch '{self.id}' rate_mva must be finite."
            )

        if self.rate_mva <= 0.0:
            raise ValueError(
                f"Branch '{self.id}' rate_mva must be greater "
                "than zero."
            )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Branch information.

        The summary contains both authoritative Terminal information
        and compatibility Bus information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__,

            "from_terminal": (
                self.from_terminal.summary()
            ),

            "to_terminal": (
                self.to_terminal.summary()
            ),

            "from_endpoint": (
                self.from_endpoint.id
                if self.from_endpoint is not None
                else None
            ),

            "to_endpoint": (
                self.to_endpoint.id
                if self.to_endpoint is not None
                else None
            ),

            "from_bus": (
                self.from_bus.id
                if self.from_bus is not None
                else None
            ),

            "to_bus": (
                self.to_bus.id
                if self.to_bus is not None
                else None
            ),

            "connected": self.is_connected,

            "r": self.r,
            "x": self.x,
            "b": self.b,

            "r_pu": self.r_pu,
            "x_pu": self.x_pu,
            "b_pu": self.b_pu,

            "tap": self.tap,
            "shift": self.shift,

            "rate_mva": self.rate_mva,

            "in_service": self.in_service,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_id = (
            self.from_endpoint.id
            if self.from_endpoint is not None
            else None
        )

        to_id = (
            self.to_endpoint.id
            if self.to_endpoint is not None
            else None
        )

        return (
            f"<{self.__class__.__name__} "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"b={self.b:.6f}, "
            f"tap={self.tap:.6f}, "
            f"shift={self.shift:.6f}, "
            f"rate={self.rate_mva:.2f} MVA, "
            f"in_service={self.in_service}>"
        )
