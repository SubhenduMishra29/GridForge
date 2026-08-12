# core/model/cable.py

"""
GridForge Cable Model
=====================

GridForge Model Layer V2

Defines the physical electrical cable model.

Architecture
------------

A Cable is a two-terminal, impedance-bearing electrical branch.

    Equipment / Node A
          │
       Terminal
          │
        Cable
          │
       Terminal
          │
    Equipment / Node B

The Cable owns its physical terminals.

The terminals identify local physical connection points. The
network/topology layer is responsible for assembling those terminals
into the global physical and electrical topology.

The Cable is deliberately different from a Line:

    Cable
        - represents a physical cable installation.
        - carries physical cable construction and electrical
          parameters.
        - may be used for underground, industrial, tray, duct,
          or other cable installations.

    Line
        - represents an electrical line/branch model.
        - may represent overhead or other line-specific construction.

Both may ultimately become impedance-bearing branches in the derived
Electrical Topology / Study Model, but their physical model semantics
remain distinct.

Responsibilities
----------------

The Cable model provides:

- Physical two-terminal electrical equipment.
- Cable identity.
- Local terminal ownership.
- Rated voltage.
- Continuous current rating.
- Cable length.
- Positive-sequence resistance/reactance.
- Zero-sequence resistance/reactance.
- Positive-sequence shunt susceptance.
- Zero-sequence shunt susceptance.
- Service state.
- Basic local parameter validation.
- Diagnostic information.

The Cable model does NOT:

- Build global topology.
- Register terminals with the network.
- Determine bus connectivity.
- Build Y-bus matrices.
- Perform load-flow calculations.
- Perform short-circuit calculations.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic simulation.
- Determine cable thermal loading.
- Determine fault current.
- Store simulation event history.
- Store GUI geometry.

Those responsibilities belong to the appropriate GridForge layers.

Electrical Parameter Convention
-------------------------------

All impedance/admittance parameters are specified per kilometre.

Positive-sequence:

    r1_ohm_per_km
    x1_ohm_per_km
    b1_us_per_km

Zero-sequence:

    r0_ohm_per_km
    x0_ohm_per_km
    b0_us_per_km

The Cable model stores physical electrical parameters.

Conversion to per-unit and construction of the numerical branch
representation belong to ``core/network`` and the numerical study
layers.

The shunt susceptance values are stored as positive magnitudes in
microSiemens/km. The numerical network representation determines the
appropriate admittance formulation.

Topology
--------

The authoritative local connection points are:

    from_terminal
    to_terminal

The Cable itself does not decide what those terminals connect to.

The network layer discovers/assembles the physical connection graph and
later derives the electrical topology used by studies and simulation.

Service State
-------------

A Cable has an authoritative ``in_service`` state.

Conceptually:

    in_service = True
        Cable is available to participate in the derived topology.

    in_service = False
        Cable is excluded from the active electrical topology.

Changing this state modifies only the physical model state. The
network/topology layer is responsible for deriving the resulting
network representation.

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The Cable is a fundamental impedance-bearing physical electrical model
and therefore belongs in ``core/model``.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# CABLE
# =====================================================================

class Cable(ElectricalObject):
    """
    GridForge physical electrical cable.

    Parameters
    ----------
    id : str
        Unique GridForge cable identifier.

    voltage_kv : float
        Rated operating voltage in kV.

    rated_current_a : float
        Continuous current rating in amperes.

    length_km : float
        Physical cable length in kilometres.

    r1_ohm_per_km : float
        Positive-sequence resistance in ohm/km.

    x1_ohm_per_km : float
        Positive-sequence reactance in ohm/km.

    b1_us_per_km : float, optional
        Positive-sequence shunt susceptance in microSiemens/km.

    r0_ohm_per_km : float or None, optional
        Zero-sequence resistance in ohm/km.

        If omitted, zero-sequence resistance defaults to the
        positive-sequence resistance.

    x0_ohm_per_km : float or None, optional
        Zero-sequence reactance in ohm/km.

        If omitted, zero-sequence reactance defaults to the
        positive-sequence reactance.

    b0_us_per_km : float or None, optional
        Zero-sequence shunt susceptance in microSiemens/km.

        If omitted, zero-sequence susceptance defaults to the
        positive-sequence susceptance.

    endpoint_from : optional
        Initial from-side electrical endpoint.

    endpoint_to : optional
        Initial to-side electrical endpoint.

    in_service : bool, optional
        Equipment service state.

    name : str, optional
        Human-readable cable name.

    Notes
    -----
    The Cable owns its physical terminals.

    The endpoints may initially be ``None``. This is intentional:
    equipment may be created before physical network assembly.

    Global connectivity is established by the network/topology layer.
    """

    def __init__(
        self,
        id: str,
        voltage_kv: float,
        rated_current_a: float,
        length_km: float,
        r1_ohm_per_km: float,
        x1_ohm_per_km: float,
        b1_us_per_km: float = 0.0,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        endpoint_from=None,
        endpoint_to=None,
        in_service: bool = True,
        name: str = "",
    ):
        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # PHYSICAL TERMINALS
        # =============================================================

        self.from_terminal = Terminal(
            endpoint=endpoint_from,
            owner=self,
        )

        self.to_terminal = Terminal(
            endpoint=endpoint_to,
            owner=self,
        )

        # =============================================================
        # EQUIPMENT RATINGS
        # =============================================================

        self.voltage_kv = float(voltage_kv)

        self.rated_current_a = float(
            rated_current_a
        )

        # =============================================================
        # PHYSICAL LENGTH
        # =============================================================

        self.length_km = float(length_km)

        # =============================================================
        # POSITIVE-SEQUENCE PARAMETERS
        # =============================================================

        self.r1_ohm_per_km = float(
            r1_ohm_per_km
        )

        self.x1_ohm_per_km = float(
            x1_ohm_per_km
        )

        self.b1_us_per_km = float(
            b1_us_per_km
        )

        # =============================================================
        # ZERO-SEQUENCE PARAMETERS
        # =============================================================

        if r0_ohm_per_km is None:
            r0_ohm_per_km = self.r1_ohm_per_km

        if x0_ohm_per_km is None:
            x0_ohm_per_km = self.x1_ohm_per_km

        if b0_us_per_km is None:
            b0_us_per_km = self.b1_us_per_km

        self.r0_ohm_per_km = float(
            r0_ohm_per_km
        )

        self.x0_ohm_per_km = float(
            x0_ohm_per_km
        )

        self.b0_us_per_km = float(
            b0_us_per_km
        )

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self.in_service = bool(in_service)

        # =============================================================
        # VALIDATION
        # =============================================================

        self._validate_parameters()

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the local from-side endpoint.
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """
        Return the local to-side endpoint.
        """

        return self.to_terminal.endpoint

    def endpoints(self):
        """
        Return the local endpoint pair.

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
    # TERMINAL CONNECTION
    # =================================================================

    def connect_from(self, endpoint) -> None:
        """
        Connect the from-side terminal locally.

        Global topology remains the responsibility of
        ``core/network``.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint) -> None:
        """
        Connect the to-side terminal locally.

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

    # =================================================================
    # TOTAL ELECTRICAL PARAMETERS
    # =================================================================

    @property
    def r1_ohm(self) -> float:
        """
        Return total positive-sequence resistance in ohms.
        """

        return (
            self.r1_ohm_per_km
            * self.length_km
        )

    @property
    def x1_ohm(self) -> float:
        """
        Return total positive-sequence reactance in ohms.
        """

        return (
            self.x1_ohm_per_km
            * self.length_km
        )

    @property
    def b1_us(self) -> float:
        """
        Return total positive-sequence shunt susceptance
        in microSiemens.
        """

        return (
            self.b1_us_per_km
            * self.length_km
        )

    @property
    def r0_ohm(self) -> float:
        """
        Return total zero-sequence resistance in ohms.
        """

        return (
            self.r0_ohm_per_km
            * self.length_km
        )

    @property
    def x0_ohm(self) -> float:
        """
        Return total zero-sequence reactance in ohms.
        """

        return (
            self.x0_ohm_per_km
            * self.length_km
        )

    @property
    def b0_us(self) -> float:
        """
        Return total zero-sequence shunt susceptance
        in microSiemens.
        """

        return (
            self.b0_us_per_km
            * self.length_km
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_parameters(self) -> None:
        """
        Validate local cable parameters.

        This performs object-level validation only.

        Network-wide electrical compatibility and engineering rules
        belong to ``core/network`` and ``core/validation``.
        """

        # -------------------------------------------------------------
        # Voltage
        # -------------------------------------------------------------

        if not isfinite(self.voltage_kv):
            raise ValueError(
                f"Cable '{self.id}' voltage rating "
                "must be finite."
            )

        if self.voltage_kv <= 0.0:
            raise ValueError(
                f"Cable '{self.id}' voltage rating "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Current
        # -------------------------------------------------------------

        if not isfinite(self.rated_current_a):
            raise ValueError(
                f"Cable '{self.id}' rated current "
                "must be finite."
            )

        if self.rated_current_a <= 0.0:
            raise ValueError(
                f"Cable '{self.id}' rated current "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Length
        # -------------------------------------------------------------

        if not isfinite(self.length_km):
            raise ValueError(
                f"Cable '{self.id}' length must be finite."
            )

        if self.length_km <= 0.0:
            raise ValueError(
                f"Cable '{self.id}' length must be "
                "greater than zero."
            )

        # -------------------------------------------------------------
        # Positive-sequence resistance
        # -------------------------------------------------------------

        if not isfinite(self.r1_ohm_per_km):
            raise ValueError(
                f"Cable '{self.id}' positive-sequence "
                "resistance must be finite."
            )

        if self.r1_ohm_per_km < 0.0:
            raise ValueError(
                f"Cable '{self.id}' positive-sequence "
                "resistance cannot be negative."
            )

        # -------------------------------------------------------------
        # Positive-sequence reactance
        # -------------------------------------------------------------

        if not isfinite(self.x1_ohm_per_km):
            raise ValueError(
                f"Cable '{self.id}' positive-sequence "
                "reactance must be finite."
            )

        if self.x1_ohm_per_km < 0.0:
            raise ValueError(
                f"Cable '{self.id}' positive-sequence "
                "reactance cannot be negative."
            )

        # -------------------------------------------------------------
        # Positive-sequence susceptance
        # -------------------------------------------------------------

        if not isfinite(self.b1_us_per_km):
            raise ValueError(
                f"Cable '{self.id}' positive-sequence "
                "susceptance must be finite."
            )

        if self.b1_us_per_km < 0.0:
            raise ValueError(
                f"Cable '{self.id}' positive-sequence "
                "susceptance cannot be negative."
            )

        # -------------------------------------------------------------
        # Zero-sequence resistance
        # -------------------------------------------------------------

        if not isfinite(self.r0_ohm_per_km):
            raise ValueError(
                f"Cable '{self.id}' zero-sequence "
                "resistance must be finite."
            )

        if self.r0_ohm_per_km < 0.0:
            raise ValueError(
                f"Cable '{self.id}' zero-sequence "
                "resistance cannot be negative."
            )

        # -------------------------------------------------------------
        # Zero-sequence reactance
        # -------------------------------------------------------------

        if not isfinite(self.x0_ohm_per_km):
            raise ValueError(
                f"Cable '{self.id}' zero-sequence "
                "reactance must be finite."
            )

        if self.x0_ohm_per_km < 0.0:
            raise ValueError(
                f"Cable '{self.id}' zero-sequence "
                "reactance cannot be negative."
            )

        # -------------------------------------------------------------
        # Zero-sequence susceptance
        # -------------------------------------------------------------

        if not isfinite(self.b0_us_per_km):
            raise ValueError(
                f"Cable '{self.id}' zero-sequence "
                "susceptance must be finite."
            )

        if self.b0_us_per_km < 0.0:
            raise ValueError(
                f"Cable '{self.id}' zero-sequence "
                "susceptance cannot be negative."
            )

        # -------------------------------------------------------------
        # Degenerate impedance check
        #
        # A zero R and zero X cable is not a meaningful impedance
        # bearing branch.
        # -------------------------------------------------------------

        if (
            self.r1_ohm_per_km == 0.0
            and self.x1_ohm_per_km == 0.0
        ):
            raise ValueError(
                f"Cable '{self.id}' must have non-zero "
                "positive-sequence impedance."
            )

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the cable is in service.
        """

        return self.in_service

    def put_in_service(self) -> None:
        """
        Mark the cable as in service.

        This changes only local model state.
        """

        self.in_service = True

    def take_out_of_service(self) -> None:
        """
        Mark the cable as out of service.

        The network/topology layer is responsible for applying this
        state to the derived electrical topology.
        """

        self.in_service = False

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured cable information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "from_endpoint": (
                self.from_terminal.endpoint_id
            ),
            "to_endpoint": (
                self.to_terminal.endpoint_id
            ),
            "from_connected": (
                self.from_terminal.is_connected
            ),
            "to_connected": (
                self.to_terminal.is_connected
            ),
            "voltage_kv": self.voltage_kv,
            "rated_current_a": self.rated_current_a,
            "length_km": self.length_km,
            "r1_ohm_per_km": self.r1_ohm_per_km,
            "x1_ohm_per_km": self.x1_ohm_per_km,
            "b1_us_per_km": self.b1_us_per_km,
            "r0_ohm_per_km": self.r0_ohm_per_km,
            "x0_ohm_per_km": self.x0_ohm_per_km,
            "b0_us_per_km": self.b0_us_per_km,
            "r1_ohm": self.r1_ohm,
            "x1_ohm": self.x1_ohm,
            "b1_us": self.b1_us,
            "r0_ohm": self.r0_ohm,
            "x0_ohm": self.x0_ohm,
            "b0_us": self.b0_us,
            "in_service": self.in_service,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_id = self.from_terminal.endpoint_id
        to_id = self.to_terminal.endpoint_id

        return (
            f"<Cable "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"length={self.length_km:.6f} km, "
            f"voltage={self.voltage_kv:.3f} kV, "
            f"rated={self.rated_current_a:.2f} A, "
            f"R1={self.r1_ohm:.6f} ohm, "
            f"X1={self.x1_ohm:.6f} ohm, "
            f"in_service={self.in_service}>"
        )
```
