"""
GridForge Transformer Model
===========================

GridForge Model Layer V2

Defines the core two-terminal transformer equipment model.

The authoritative physical connection points are:

    from_terminal
    to_terminal

The connected buses are derived from those terminals.

The core Transformer intentionally provides the stable electrical
interface required by the network and solver layers while leaving
detailed transformer engineering behavior extensible through the
plugin architecture.

Core representation:

    Z_series = R + jX

    tap   = off-nominal magnitude ratio
    shift = phase-shift angle in radians

Detailed transformer capabilities such as:

* winding configuration
* vector group
* grounding
* neutral
* OLTC
* tap-control logic
* magnetizing branch
* core losses
* sequence-specific models
* thermal models

belong to appropriate higher-level/plugin models.

The Transformer does NOT:

* build Y-bus
* perform power flow
* calculate losses
* calculate loading
* perform short circuit
* execute tap control
* perform protection
* perform dynamic simulation
* own global network topology
* manage GUI state

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .branch import Branch
from .terminal import Terminal


# =====================================================================
# TRANSFORMER
# =====================================================================


class Transformer(Branch):
    """
    GridForge core two-terminal transformer model.

    Parameters
    ----------
    id : str
        Unique GridForge transformer identifier.

    endpoint_from :
        From-side electrical endpoint or Terminal.

    endpoint_to :
        To-side electrical endpoint or Terminal.

    r : float
        Series resistance in per-unit.

    x : float
        Series reactance in per-unit.

    tap : float, optional
        Off-nominal magnitude tap ratio.

        Default: 1.0

    shift : float, optional
        Phase-shifting angle in radians.

        Default: 0.0

    name : str, optional
        Human-readable transformer name.

    rate_mva : float, optional
        Transformer equipment rating in MVA.

    Notes
    -----
    ``from_terminal`` and ``to_terminal`` are authoritative.

    ``from_bus`` and ``to_bus`` are derived compatibility accessors.
    """

    def __init__(
        self,
        id: str,
        endpoint_from,
        endpoint_to,
        r: float,
        x: float,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
    ):
        """
        Initialize a GridForge transformer.
        """

        # -------------------------------------------------------------
        # Branch initialization
        #
        # The inherited bus fields are retained only for compatibility
        # with the existing frozen Branch/solver interface. The
        # authoritative physical connection is established below.
        # -------------------------------------------------------------

        super().__init__(
            id=id,
            bus_from=(
                endpoint_from
                if hasattr(endpoint_from, "id")
                else None
            ),
            bus_to=(
                endpoint_to
                if hasattr(endpoint_to, "id")
                else None
            ),
            r=r,
            x=x,
            b=0.0,
            name=name,
            rate_mva=rate_mva,
            tap=tap,
            shift=shift,
        )

        # -------------------------------------------------------------
        # Authoritative physical terminals
        # -------------------------------------------------------------

        self.from_terminal = (
            endpoint_from
            if isinstance(endpoint_from, Terminal)
            else Terminal(endpoint_from, owner=self)
        )

        self.to_terminal = (
            endpoint_to
            if isinstance(endpoint_to, Terminal)
            else Terminal(endpoint_to, owner=self)
        )

        if self.from_terminal is self.to_terminal:
            raise ValueError(
                f"Transformer '{self.id}' cannot connect "
                "a terminal to itself."
            )

        # -------------------------------------------------------------
        # Terminal ownership
        # -------------------------------------------------------------

        if (
            self.from_terminal.owner is not None
            and self.from_terminal.owner is not self
        ):
            raise ValueError(
                f"Transformer '{self.id}' from_terminal already "
                "belongs to another equipment object."
            )

        if (
            self.to_terminal.owner is not None
            and self.to_terminal.owner is not self
        ):
            raise ValueError(
                f"Transformer '{self.id}' to_terminal already "
                "belongs to another equipment object."
            )

        self.from_terminal.owner = self
        self.to_terminal.owner = self

        self._validate_transformer_parameters()

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the physical transformer terminal pair.
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # =================================================================
    # ENDPOINTS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the authoritative from-side endpoint.
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """
        Return the authoritative to-side endpoint.
        """

        return self.to_terminal.endpoint

    def endpoints(self) -> tuple:
        """
        Return the authoritative physical endpoint pair.
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
        Return the bus associated with the from-side terminal.

        This is a derived compatibility property.

        The authoritative connection remains ``from_terminal``.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the bus associated with the to-side terminal.

        This is a derived compatibility property.

        The authoritative connection remains ``to_terminal``.
        """

        return self.to_terminal.bus

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both transformer terminals are connected.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    def connect_from(self, endpoint) -> None:
        """
        Connect the from-side terminal locally.

        Global topology is managed by core/network.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint) -> None:
        """
        Connect the to-side terminal locally.

        Global topology is managed by core/network.
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
    # TRANSFORMER IDENTIFICATION
    # =================================================================

    @property
    def is_transformer(self) -> bool:
        """
        Return True because this equipment is a transformer.
        """

        return True

    # =================================================================
    # TRANSFORMER STATE
    # =================================================================

    @property
    def is_off_nominal(self) -> bool:
        """
        Return True when the tap ratio differs from unity.
        """

        return self.tap != 1.0

    @property
    def has_phase_shift(self) -> bool:
        """
        Return True when a non-zero phase shift is present.

        ``shift`` is expressed in radians.
        """

        return self.shift != 0.0

    # =================================================================
    # LOCAL VALIDATION
    # =================================================================

    def _validate_transformer_parameters(self) -> None:
        """
        Validate local transformer parameters.

        Network compatibility and engineering validation belong to
        higher layers.
        """

        if not isfinite(self.r):
            raise ValueError(
                f"Transformer '{self.id}' resistance must be finite."
            )

        if self.r < 0.0:
            raise ValueError(
                f"Transformer '{self.id}' resistance cannot be negative."
            )

        if not isfinite(self.x):
            raise ValueError(
                f"Transformer '{self.id}' reactance must be finite."
            )

        if self.x == 0.0:
            raise ValueError(
                f"Transformer '{self.id}' reactance cannot be zero."
            )

        if not isfinite(self.tap):
            raise ValueError(
                f"Transformer '{self.id}' tap ratio must be finite."
            )

        if self.tap <= 0.0:
            raise ValueError(
                f"Transformer '{self.id}' tap ratio must be "
                "greater than zero."
            )

        if not isfinite(self.shift):
            raise ValueError(
                f"Transformer '{self.id}' phase shift must be finite."
            )

        if not isfinite(self.rate_mva):
            raise ValueError(
                f"Transformer '{self.id}' MVA rating must be finite."
            )

        if self.rate_mva <= 0.0:
            raise ValueError(
                f"Transformer '{self.id}' MVA rating must be "
                "greater than zero."
            )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured transformer information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "transformer",

            "from_terminal": self.from_terminal.summary(),
            "to_terminal": self.to_terminal.summary(),

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

            "r_pu": self.r,
            "x_pu": self.x,

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
            f"<Transformer "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"tap={self.tap:.6f}, "
            f"shift={self.shift:.6f} rad, "
            f"rate={self.rate_mva:.2f} MVA, "
            f"in_service={self.in_service}>"
        )
