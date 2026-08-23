# core/model/transformer.py
"""
GridForge V2 Transformer Model
==============================

Author:
    Subhendu Mishra

A Transformer is a static two-terminal electrical equipment model.

Architecture
------------

    Transformer
        |
        +-- Branch
        |
        +-- from_terminal
        +-- to_terminal
        |
        +-- R
        +-- X
        +-- tap ratio
        +-- phase shift
        +-- rating

The Transformer owns its local electrical parameters and two
electrical terminals.

It does NOT:

    - own global network topology
    - add itself to a Grid
    - maintain bus collections
    - build Y-bus matrices
    - solve load flow
    - solve short circuit
    - perform protection studies
    - perform dynamic simulation
    - implement OLTC control logic
    - own SLD geometry
    - own GUI state

Dynamic transformer behavior belongs to the future dynamic-model
architecture.

Tap ratio and phase shift in this class are static electrical
parameters. A controller that changes the tap is a separate
application/domain service.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch
from .terminal import Terminal


class Transformer(Branch):
    """
    Static two-terminal transformer electrical model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Initial from-side electrical endpoint.
        May be None.

    endpoint_to:
        Initial to-side electrical endpoint.
        May be None.

    r:
        Equivalent series resistance in per-unit.

    x:
        Equivalent series reactance in per-unit.

    tap:
        Static magnitude tap ratio.

        1.0 represents nominal ratio.

    shift:
        Static phase shift in radians.

    name:
        Human-readable transformer name.

    rate_mva:
        Optional transformer rating in MVA.

    b:
        Total equivalent shunt susceptance in per-unit.

    Notes
    -----
    The exact transformer equivalent-circuit interpretation is
    determined by the numerical/network layer.

    This model stores the engineering parameters; it does not
    perform network matrix assembly.
    """

    TYPE = "TRANSFORMER"

    def __init__(
        self,
        id: str,
        endpoint_from=None,
        endpoint_to=None,
        *,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = "",
        rate_mva: float | None = None,
    ) -> None:

        # ---------------------------------------------------------
        # Branch creates the authoritative terminals.
        #
        # We do not replace them afterwards.
        # ---------------------------------------------------------

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
            tap=tap,
            shift=shift,
        )

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =============================================================
    # TRANSFORMER ELECTRICAL PARAMETERS
    # =============================================================

    @property
    def turns_ratio(self) -> float:
        """
        Return the effective static magnitude ratio.

        In the simplified per-unit model this corresponds to the
        configured tap ratio.

        Detailed winding/nominal-voltage conversion is handled by
        the transformer numerical model.
        """

        return self.tap

    @property
    def tap_ratio(self) -> float:
        """Return the static tap ratio."""

        return self.tap

    @property
    def phase_shift_rad(self) -> float:
        """Return phase shift in radians."""

        return self.shift

    @property
    def phase_shift_deg(self) -> float:
        """Return phase shift in degrees."""

        return math.degrees(self.shift)

    # =============================================================
    # TAP
    # =============================================================

    def set_tap(
        self,
        tap: float,
    ) -> None:
        """
        Set the static transformer tap ratio.

        This changes the model parameter only.

        It does not implement an OLTC controller.
        """

        tap = self._validate_positive(
            tap,
            "tap",
        )

        self.tap = tap

    # =============================================================
    # PHASE SHIFT
    # =============================================================

    def set_phase_shift(
        self,
        shift: float,
    ) -> None:
        """
        Set static phase shift in radians.

        This is a model parameter, not a controller action.
        """

        self.shift = self._validate_finite(
            shift,
            "shift",
        )

    def set_phase_shift_degrees(
        self,
        degrees: float,
    ) -> None:
        """
        Set static phase shift in degrees.
        """

        degrees = self._validate_finite(
            degrees,
            "degrees",
        )

        self.shift = math.radians(
            degrees
        )

    # =============================================================
    # TRANSFORMER RATING
    # =============================================================

    @property
    def has_rating(self) -> bool:
        """Return whether a transformer rating is defined."""

        return self.rate_mva is not None

    def set_rating(
        self,
        rate_mva: float | None,
    ) -> None:
        """
        Set or clear transformer rating.
        """

        if rate_mva is None:
            self.rate_mva = None
            return

        self.rate_mva = self._validate_positive(
            rate_mva,
            "rate_mva",
        )

    # =============================================================
    # TERMINALS
    # =============================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """Return the two authoritative transformer terminals."""

        return (
            self.from_terminal,
            self.to_terminal,
        )

    @property
    def from_endpoint(self):
        """Return from-side endpoint."""

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """Return to-side endpoint."""

        return self.to_terminal.endpoint

    @property
    def from_bus(self):
        """
        Return bus derived from the from terminal.

        This is a compatibility accessor, not independent topology
        state.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return bus derived from the to terminal.

        This is a compatibility accessor, not independent topology
        state.
        """

        return self.to_terminal.bus

    # =============================================================
    # CONNECTIVITY
    # =============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both transformer terminals have endpoints.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    @property
    def has_from_endpoint(self) -> bool:
        """Return whether the from terminal is connected."""

        return self.from_terminal.is_connected

    @property
    def has_to_endpoint(self) -> bool:
        """Return whether the to terminal is connected."""

        return self.to_terminal.is_connected

    def connect_from(
        self,
        endpoint,
    ) -> None:
        """
        Connect the from-side terminal.

        Global topology is managed elsewhere.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(
        self,
        endpoint,
    ) -> None:
        """
        Connect the to-side terminal.

        Global topology is managed elsewhere.
        """

        self.to_terminal.connect(endpoint)

    def disconnect_from(self) -> None:
        """Disconnect the from-side terminal."""

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """Disconnect the to-side terminal."""

        self.to_terminal.disconnect()

    # =============================================================
    # SERVICE STATE
    # =============================================================

    def connect(self) -> None:
        """
        Place transformer in service.

        This does not modify terminal topology.
        """

        self.in_service = True

    def disconnect(self) -> None:
        """
        Take transformer out of service.

        This does not modify terminal topology.
        """

        self.in_service = False

    def close(self) -> None:
        """Compatibility alias for connect()."""

        self.connect()

    def trip(self) -> None:
        """Compatibility alias for disconnect()."""

        self.disconnect()

    @property
    def is_in_service(self) -> bool:
        """Return whether transformer is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether transformer is out of service."""

        return not self.in_service

    # =============================================================
    # ELECTRICAL MODEL
    # =============================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return transformer equivalent series impedance.

            Z = R + jX
        """

        return complex(
            self.r,
            self.x,
        )

    @property
    def series_admittance(self) -> complex:
        """
        Return transformer series admittance.

            Y = 1 / Z

        Network matrix construction remains outside this model.
        """

        z = self.series_impedance

        if abs(z) <= 1e-15:
            raise ZeroDivisionError(
                f"Transformer '{self.id}' has zero "
                "series impedance."
            )

        return 1.0 / z

    @property
    def shunt_admittance(self) -> complex:
        """
        Return equivalent shunt admittance.

            Ysh = jB
        """

        return complex(
            0.0,
            self.b,
        )

    # =============================================================
    # NUMERICAL REPRESENTATION
    # =============================================================

    def get_electrical_parameters(self) -> dict[str, float]:
        """
        Return the static transformer electrical parameters.

        The numerical layer may use these values to construct its
        selected transformer equivalent circuit.
        """

        return {
            "r_pu": self.r,
            "x_pu": self.x,
            "b_pu": self.b,
            "tap": self.tap,
            "shift_rad": self.shift,
            "rate_mva": (
                self.rate_mva
                if self.rate_mva is not None
                else float("nan")
            ),
        }

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate transformer-local engineering parameters.

        This does not validate network topology.
        """

        self.r = self._validate_finite(
            self.r,
            "r",
        )

        self.x = self._validate_finite(
            self.x,
            "x",
        )

        self.b = self._validate_finite(
            self.b,
            "b",
        )

        if self.r < 0.0:
            raise ValueError(
                f"Transformer '{self.id}' resistance "
                "cannot be negative."
            )

        if (
            math.isclose(
                self.r,
                0.0,
                abs_tol=1e-15,
            )
            and math.isclose(
                self.x,
                0.0,
                abs_tol=1e-15,
            )
        ):
            raise ValueError(
                f"Transformer '{self.id}' cannot have "
                "zero series impedance."
            )

        self.tap = self._validate_positive(
            self.tap,
            "tap",
        )

        self.shift = self._validate_finite(
            self.shift,
            "shift",
        )

        if self.rate_mva is not None:
            self.rate_mva = self._validate_positive(
                self.rate_mva,
                "rate_mva",
            )

        return True

    def validate(self) -> bool:
        """
        Public local validation entry point.

        Network topology and study validity are outside this model.
        """

        return self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return structured transformer diagnostics."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

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

            "is_connected": self.is_connected,
            "in_service": self.in_service,

            "r_pu": self.r,
            "x_pu": self.x,
            "b_pu": self.b,

            "series_impedance": self.series_impedance,
            "series_admittance": self.series_admittance,
            "shunt_admittance": self.shunt_admittance,

            "tap_ratio": self.tap,
            "phase_shift_rad": self.shift,
            "phase_shift_deg": self.phase_shift_deg,

            "rate_mva": self.rate_mva,
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

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
            f"b={self.b:.6f}, "
            f"tap={self.tap:.6f}, "
            f"shift={self.shift:.6f}, "
            f"rate={self.rate_mva}, "
            f"in_service={self.in_service}>"
        )

    # =============================================================
    # VALIDATION HELPERS
    # =============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Return a finite floating-point value."""

        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> float:
        """Return a finite positive floating-point value."""

        value = float(value)

        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{name} must be finite and greater than zero."
            )

        return value
