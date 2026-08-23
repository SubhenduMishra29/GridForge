# core/model/branch.py
"""
GridForge V2 Branch Model
=========================

Author:
    Subhendu Mishra

A Branch is the generic two-terminal electrical model used as the
common foundation for branch-type network equipment.

Architecture
------------

    Equipment A
         |
    from_terminal
         |
       Branch
         |
     to_terminal
         |
    Equipment B

Branch represents electrical connectivity between two endpoints and
stores common branch electrical parameters.

Typical specialized equipment includes:

    - Line
    - Transformer
    - Series compensation equipment
    - Future two-terminal electrical equipment

The Branch owns exactly two physical Terminal objects.

The Terminal endpoints are the authoritative local connectivity
references.

The Branch does NOT own global network topology.

Network topology is managed by the Core network/application layer.

The Branch does NOT:

    - add itself to a Grid
    - maintain bus collections
    - build Y-bus matrices
    - solve load flow
    - solve short circuit
    - perform protection studies
    - perform dynamic simulation
    - manage SLD geometry
    - manage GUI state

Electrical parameters
---------------------

    r
        Series resistance, per-unit.

    x
        Series reactance, per-unit.

    b
        Total shunt susceptance, per-unit.

    tap
        Transformer-compatible magnitude tap ratio.

    shift
        Transformer-compatible phase-shift angle in radians.

The exact numerical interpretation and Y-bus stamping convention
belong to the Network/Numerical/Analysis layers.

Lifecycle
---------

Physical connectivity:

    connect_from()
    connect_to()
    disconnect_from()
    disconnect_to()

Operational state:

    connect()
    disconnect()
    trip()
    close()

These are deliberately separate concepts.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Branch(ElectricalObject):
    """
    Generic two-terminal electrical branch.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Initial from-side endpoint. Optional.

    endpoint_to:
        Initial to-side endpoint. Optional.

    r:
        Series resistance in per-unit.

    x:
        Series reactance in per-unit.

    b:
        Total shunt susceptance in per-unit.

    name:
        Human-readable name.

    rate_mva:
        Optional continuous/nominal thermal rating in MVA.

    tap:
        Transformer-compatible magnitude tap ratio.
        Default is 1.0.

    shift:
        Transformer-compatible phase-shift angle in radians.
        Default is 0.0.
    """

    TYPE = "BRANCH"

    def __init__(
        self,
        id: str,
        endpoint_from=None,
        endpoint_to=None,
        *,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        name: str = "",
        rate_mva: float | None = None,
        tap: float = 1.0,
        shift: float = 0.0,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =========================================================
        # PHYSICAL TERMINALS
        # =========================================================

        self.from_terminal = self._create_terminal(
            endpoint_from
        )

        self.to_terminal = self._create_terminal(
            endpoint_to
        )

        if self.from_terminal is self.to_terminal:
            raise ValueError(
                f"Branch '{self.id}' cannot use the same "
                "Terminal object for both ends."
            )

        # =========================================================
        # ELECTRICAL PARAMETERS
        # =========================================================

        self.r = self._validate_finite(
            r,
            "r",
        )

        self.x = self._validate_finite(
            x,
            "x",
        )

        self.b = self._validate_finite(
            b,
            "b",
        )

        # =========================================================
        # TRANSFORMER-COMPATIBLE PARAMETERS
        # =========================================================

        self.tap = self._validate_positive(
            tap,
            "tap",
        )

        self.shift = self._validate_finite(
            shift,
            "shift",
        )

        # =========================================================
        # EQUIPMENT RATING
        # =========================================================

        if rate_mva is None:
            self.rate_mva = None
        else:
            self.rate_mva = self._validate_positive(
                rate_mva,
                "rate_mva",
            )

        # =========================================================
        # OPERATIONAL STATE
        # =========================================================

        self.in_service = True

        # =========================================================
        # EXTENSIONS
        # =========================================================

        self._extensions: dict[str, Any] = {}

        # =========================================================
        # LOCAL VALIDATION
        # =========================================================

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return the canonical GridForge element type."""
        return self.TYPE

    # =============================================================
    # TERMINAL CREATION
    # =============================================================

    def _create_terminal(
        self,
        endpoint=None,
    ) -> Terminal:
        """
        Create the Branch terminal.

        An existing Terminal may be supplied only when it is
        unowned or already owned by this Branch.
        """

        if isinstance(endpoint, Terminal):

            terminal = endpoint

            if (
                terminal.owner is not None
                and terminal.owner is not self
            ):
                raise ValueError(
                    f"Branch '{self.id}' cannot take ownership "
                    "of a Terminal belonging to another object."
                )

            terminal.owner = self
            return terminal

        return Terminal(
            endpoint=endpoint,
            owner=self,
        )

    # =============================================================
    # TERMINALS
    # =============================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """Return the two authoritative physical terminals."""

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # =============================================================
    # ENDPOINTS
    # =============================================================

    @property
    def from_endpoint(self):
        """Return the authoritative from-side endpoint."""

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """Return the authoritative to-side endpoint."""

        return self.to_terminal.endpoint

    def endpoints(self) -> tuple:
        """Return the authoritative endpoint pair."""

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # =============================================================
    # BUS COMPATIBILITY
    # =============================================================

    @property
    def from_bus(self):
        """
        Return the bus derived by the Terminal interface.

        This is a compatibility accessor only.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the bus derived by the Terminal interface.

        This is a compatibility accessor only.
        """

        return self.to_terminal.bus

    def buses(self) -> tuple:
        """
        Return derived bus references.

        These are not independent topology state.
        """

        return (
            self.from_bus,
            self.to_bus,
        )

    # =============================================================
    # CONNECTIVITY STATE
    # =============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both branch terminals have endpoints.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    @property
    def is_fully_connected(self) -> bool:
        """Alias for is_connected."""

        return self.is_connected

    @property
    def has_from_endpoint(self) -> bool:
        """Return True when the from terminal is connected."""

        return self.from_terminal.is_connected

    @property
    def has_to_endpoint(self) -> bool:
        """Return True when the to terminal is connected."""

        return self.to_terminal.is_connected

    # =============================================================
    # TERMINAL CONNECTION
    # =============================================================

    def connect_from(
        self,
        endpoint,
    ) -> None:
        """
        Assign the from-side physical endpoint.

        This modifies only local terminal state.

        Global network topology is not modified here.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(
        self,
        endpoint,
    ) -> None:
        """
        Assign the to-side physical endpoint.

        This modifies only local terminal state.

        Global network topology is not modified here.
        """

        self.to_terminal.connect(endpoint)

    def disconnect_from(self) -> None:
        """Remove the from-side physical endpoint."""

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """Remove the to-side physical endpoint."""

        self.to_terminal.disconnect()

    # =============================================================
    # ELECTRICAL PARAMETERS
    # =============================================================

    @property
    def impedance(self) -> complex:
        """
        Return series impedance.

            Z = R + jX
        """

        return complex(
            self.r,
            self.x,
        )

    @property
    def series_impedance(self) -> complex:
        """Alias for impedance."""

        return self.impedance

    @property
    def admittance(self) -> complex:
        """
        Return series admittance.

            Y = 1 / Z

        Y-bus construction is not performed here.
        """

        z = self.impedance

        if z == 0.0 + 0.0j:
            raise ZeroDivisionError(
                f"Branch '{self.id}' has zero series impedance."
            )

        return 1.0 / z

    @property
    def series_admittance(self) -> complex:
        """Alias for admittance."""

        return self.admittance

    @property
    def shunt_admittance(self) -> complex:
        """
        Return total shunt admittance.

            Ysh = jB
        """

        return complex(
            0.0,
            self.b,
        )

    # =============================================================
    # PER-UNIT ACCESSORS
    # =============================================================

    @property
    def r_pu(self) -> float:
        """Return series resistance in per-unit."""

        return self.r

    @property
    def x_pu(self) -> float:
        """Return series reactance in per-unit."""

        return self.x

    @property
    def b_pu(self) -> float:
        """
        Return total shunt susceptance in per-unit.

        For a standard π line model, the numerical layer decides
        how this is divided between terminals.
        """

        return self.b

    # =============================================================
    # TRANSFORMER-COMPATIBLE ACCESSORS
    # =============================================================

    @property
    def tap_ratio(self) -> float:
        """Return magnitude tap ratio."""

        return self.tap

    @property
    def phase_shift(self) -> float:
        """Return phase shift in radians."""

        return self.shift

    # =============================================================
    # RATING
    # =============================================================

    @property
    def has_rating(self) -> bool:
        """Return whether a thermal rating is defined."""

        return self.rate_mva is not None

    def set_rating(
        self,
        rate_mva: float | None,
    ) -> None:
        """Set or clear the branch thermal rating."""

        if rate_mva is None:
            self.rate_mva = None
            return

        self.rate_mva = self._validate_positive(
            rate_mva,
            "rate_mva",
        )

    # =============================================================
    # OPERATIONAL STATE
    # =============================================================

    def connect(self) -> None:
        """
        Place the Branch in service.

        This does not connect either physical terminal.
        """

        self.in_service = True

    def disconnect(self) -> None:
        """
        Take the Branch out of service.

        This does not disconnect either physical terminal.
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
        """Return whether the Branch is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the Branch is out of service."""

        return not self.in_service

    # =============================================================
    # EXTENSIONS
    # =============================================================

    def register_extension(
        self,
        extension_id: str,
        extension: Any,
    ) -> None:
        """
        Register an optional engineering extension.

        The extension must not bypass Core/Application contracts.
        """

        if not isinstance(extension_id, str):
            raise TypeError(
                "extension_id must be a string."
            )

        extension_id = extension_id.strip()

        if not extension_id:
            raise ValueError(
                "extension_id cannot be empty."
            )

        if extension is None:
            raise ValueError(
                "extension cannot be None."
            )

        if extension_id in self._extensions:
            raise ValueError(
                f"Extension '{extension_id}' is already registered."
            )

        self._extensions[extension_id] = extension

    def get_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Return an extension reference."""

        return self._extensions.get(extension_id)

    def remove_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Remove and return an extension reference."""

        return self._extensions.pop(
            extension_id,
            None,
        )

    @property
    def extension_ids(self) -> tuple[str, ...]:
        """Return registered extension identifiers."""

        return tuple(self._extensions.keys())

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Branch-local engineering parameters.

        This method deliberately does not validate network topology.
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
                f"Branch '{self.id}' resistance cannot be negative."
            )

        if (
            math.isclose(self.r, 0.0, abs_tol=1e-15)
            and math.isclose(self.x, 0.0, abs_tol=1e-15)
        ):
            raise ValueError(
                f"Branch '{self.id}' cannot have zero "
                "series impedance."
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

    # Backward-compatible private validation entry point.
    def _validate_parameters(self) -> None:
        """
        Compatibility wrapper for existing internal callers.

        New code should use validate_parameters().
        """

        self.validate_parameters()

    def validate(self) -> bool:
        """
        Public local validation entry point.

        Important:
            This validates the Branch object itself.

        It does NOT validate global network topology.
        """

        return self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "r_pu": self.r,
            "x_pu": self.x,
            "b_pu": self.b,
            "impedance": self.impedance,
            "series_admittance": self._safe_admittance(),
            "shunt_admittance": self.shunt_admittance,
            "rate_mva": self.rate_mva,
            "tap": self.tap,
            "shift": self.shift,
            "in_service": self.in_service,
            "from_endpoint": self.from_endpoint,
            "to_endpoint": self.to_endpoint,
            "is_connected": self.is_connected,
            "extensions": self.extension_ids,
        }

    def _safe_admittance(self) -> complex | None:
        """Return series admittance without raising during diagnostics."""

        if self.impedance == 0.0 + 0.0j:
            return None

        return 1.0 / self.impedance

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
