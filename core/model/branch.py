# core/model/branch.py
"""
GridForge V2 Branch Model
=========================

Author:
    Subhendu Mishra

Generic two-terminal electrical branch foundation.

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

Branch provides:

    - two physical terminals
    - common operational state
    - optional generic per-unit branch parameters
    - optional thermal rating
    - common connectivity accessors
    - extension support
    - local validation

Branch does NOT own:

    - global network topology
    - Bus collections
    - Y-bus construction
    - load-flow solving
    - short-circuit solving
    - protection calculations
    - dynamic simulation
    - SLD geometry
    - GUI state

Specialized branch models such as Line, Cable and Transformer may
use their own engineering parameterization.

Therefore generic r/x/b parameters are optional rather than mandatory.

This is important for physical models such as Cable, whose primary
parameters are represented in ohm/km and require conversion by the
appropriate numerical layer.

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
        Optional initial from-side endpoint.

    endpoint_to:
        Optional initial to-side endpoint.

    r:
        Optional series resistance in per-unit.

    x:
        Optional series reactance in per-unit.

    b:
        Optional total shunt susceptance in per-unit.

    name:
        Human-readable name.

    rate_mva:
        Optional thermal/nominal rating in MVA.

    tap:
        Optional transformer-compatible magnitude tap ratio.

    shift:
        Optional transformer-compatible phase-shift angle in radians.

    in_service:
        Initial operational state.
    """

    TYPE = "BRANCH"

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        name: str = "",
        rate_mva: float | None = None,
        tap: float = 1.0,
        shift: float = 0.0,
        in_service: bool = True,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # PHYSICAL TERMINALS
        # =============================================================

        self.from_terminal = self._create_terminal(
            endpoint_from,
            role="from",
        )

        self.to_terminal = self._create_terminal(
            endpoint_to,
            role="to",
        )

        if self.from_terminal is self.to_terminal:
            raise ValueError(
                f"Branch '{self.id}' cannot use the same "
                "Terminal object for both ends."
            )

        # =============================================================
        # GENERIC ELECTRICAL PARAMETERS
        # =============================================================

        self.r = self._validate_optional_finite(
            r,
            "r",
        )

        self.x = self._validate_optional_finite(
            x,
            "x",
        )

        self.b = self._validate_optional_finite(
            b,
            "b",
        )

        # =============================================================
        # TRANSFORMER-COMPATIBLE PARAMETERS
        # =============================================================

        self.tap = self._validate_positive(
            tap,
            "tap",
        )

        self.shift = self._validate_finite(
            shift,
            "shift",
        )

        # =============================================================
        # RATING
        # =============================================================

        if rate_mva is None:
            self.rate_mva = None
        else:
            self.rate_mva = self._validate_positive(
                rate_mva,
                "rate_mva",
            )

        # =============================================================
        # OPERATIONAL STATE
        # =============================================================

        self.in_service = bool(
            in_service
        )

        # =============================================================
        # EXTENSIONS
        # =============================================================

        self._extensions: dict[str, Any] = {}

        self.validate_parameters()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return the canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # TERMINAL CREATION
    # =================================================================

    def _create_terminal(
        self,
        endpoint: Any = None,
        *,
        role: str | None = None,
    ) -> Terminal:
        """
        Create or adopt a Terminal.

        An existing Terminal may be supplied only when it is
        unowned or already owned by this Branch.
        """

        if isinstance(
            endpoint,
            Terminal,
        ):
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

            if (
                role is not None
                and terminal.role is None
            ):
                terminal.role = role

            return terminal

        return Terminal(
            endpoint=endpoint,
            owner=self,
            role=role,
        )

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """Return the two authoritative physical terminals."""

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # =================================================================
    # ENDPOINTS
    # =================================================================

    @property
    def from_endpoint(self) -> Any:
        """Return the authoritative from-side endpoint."""

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self) -> Any:
        """Return the authoritative to-side endpoint."""

        return self.to_terminal.endpoint

    def endpoints(self) -> tuple[Any, Any]:
        """Return the authoritative endpoint pair."""

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # =================================================================
    # BUS COMPATIBILITY
    # =================================================================

    @property
    def from_bus(self) -> Any:
        """
        Return the bus derived by the Terminal interface.

        This is an accessor, not independent topology state.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self) -> Any:
        """
        Return the bus derived by the Terminal interface.

        This is an accessor, not independent topology state.
        """

        return self.to_terminal.bus

    def buses(self) -> tuple[Any, Any]:
        """Return derived bus references."""

        return (
            self.from_bus,
            self.to_bus,
        )

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """Return True when both terminals have endpoints."""

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

    # =================================================================
    # TERMINAL CONNECTION
    # =================================================================

    def connect_from(
        self,
        endpoint: Any,
    ) -> None:
        """
        Assign the from-side local endpoint.

        Global topology is not modified.
        """

        self.from_terminal.connect(
            endpoint
        )

    def connect_to(
        self,
        endpoint: Any,
    ) -> None:
        """
        Assign the to-side local endpoint.

        Global topology is not modified.
        """

        self.to_terminal.connect(
            endpoint
        )

    def disconnect_from(self) -> None:
        """Remove the from-side local endpoint."""

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """Remove the to-side local endpoint."""

        self.to_terminal.disconnect()

    # =================================================================
    # GENERIC ELECTRICAL PARAMETERS
    # =================================================================

    @property
    def has_per_unit_parameters(self) -> bool:
        """
        Return True when complete generic r/x data are available.
        """

        return (
            self.r is not None
            and self.x is not None
        )

    @property
    def impedance(self) -> complex:
        """
        Return generic series impedance.

            Z = R + jX

        Raises
        ------
        ValueError
            If generic per-unit r/x parameters are not available.
        """

        if (
            self.r is None
            or self.x is None
        ):
            raise ValueError(
                f"Branch '{self.id}' does not define "
                "generic per-unit series impedance."
            )

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
        Return generic series admittance.

            Y = 1 / Z

        Y-bus construction remains outside Branch.
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
        Return generic total shunt admittance.

            Ysh = jB

        Returns zero when generic b is not supplied.
        """

        if self.b is None:
            return 0.0 + 0.0j

        return complex(
            0.0,
            self.b,
        )

    # =================================================================
    # PER-UNIT ACCESSORS
    # =================================================================

    @property
    def r_pu(self) -> float | None:
        """Return generic resistance in per-unit."""

        return self.r

    @property
    def x_pu(self) -> float | None:
        """Return generic reactance in per-unit."""

        return self.x

    @property
    def b_pu(self) -> float | None:
        """Return generic shunt susceptance in per-unit."""

        return self.b

    # =================================================================
    # TAP / PHASE SHIFT
    # =================================================================

    @property
    def tap_ratio(self) -> float:
        """Return magnitude tap ratio."""

        return self.tap

    @property
    def phase_shift(self) -> float:
        """Return phase shift in radians."""

        return self.shift

    # =================================================================
    # RATING
    # =================================================================

    @property
    def has_rating(self) -> bool:
        """Return whether a thermal rating is defined."""

        return self.rate_mva is not None

    def set_rating(
        self,
        rate_mva: float | None,
    ) -> None:
        """Set or clear the thermal rating."""

        if rate_mva is None:
            self.rate_mva = None
            return

        self.rate_mva = self._validate_positive(
            rate_mva,
            "rate_mva",
        )

    # =================================================================
    # OPERATIONAL STATE
    # =================================================================

    def connect(self) -> None:
        """
        Place the Branch in service.

        This does not connect physical terminals.
        """

        self.in_service = True

    def disconnect(self) -> None:
        """
        Take the Branch out of service.

        This does not disconnect physical terminals.
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

    # =================================================================
    # EXTENSIONS
    # =================================================================

    def register_extension(
        self,
        extension_id: str,
        extension: Any,
    ) -> None:
        """
        Register an optional engineering extension.

        Extensions are references only. They do not bypass
        Core/Application contracts.
        """

        if not isinstance(
            extension_id,
            str,
        ):
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

        self._extensions[
            extension_id
        ] = extension

    def get_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Return an extension reference."""

        return self._extensions.get(
            extension_id
        )

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

        return tuple(
            self._extensions.keys()
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Branch-local parameters.

        Important:

        A generic Branch is allowed to have no generic r/x/b
        parameterization because specialized physical branches may
        define their electrical parameters in another engineering
        representation.

        Therefore this method validates supplied values but does not
        require them to exist.
        """

        self.r = self._validate_optional_finite(
            self.r,
            "r",
        )

        self.x = self._validate_optional_finite(
            self.x,
            "x",
        )

        self.b = self._validate_optional_finite(
            self.b,
            "b",
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

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be a boolean."
            )

        return True

    def validate(self) -> bool:
        """
        Public Branch validation entry point.
        """

        super().validate()

        return self.validate_parameters()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Branch-local diagnostic information.

        No global topology is embedded in the result.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.element_type,
            "in_service": self.in_service,
            "connected": self.is_connected,

            "from_endpoint": (
                self.from_terminal.endpoint_id
            ),

            "to_endpoint": (
                self.to_terminal.endpoint_id
            ),

            "r_pu": self.r,
            "x_pu": self.x,
            "b_pu": self.b,

            "rate_mva": self.rate_mva,

            "tap": self.tap,
            "shift": self.shift,

            "extensions": self.extension_ids,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return a concise developer-facing representation."""

        return (
            f"<{self.__class__.__name__} "
            f"id={self.id}, "
            f"in_service={self.in_service}, "
            f"connected={self.is_connected}>"
        )

    # =================================================================
    # NUMERICAL VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: Any,
        field_name: str,
    ) -> float:
        """Validate a finite numeric value."""

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{field_name} must be finite."
            )

        return value

    @classmethod
    def _validate_optional_finite(
        cls,
        value: Any,
        field_name: str,
    ) -> float | None:
        """Validate an optional finite numeric value."""

        if value is None:
            return None

        return cls._validate_finite(
            value,
            field_name,
        )

    @staticmethod
    def _validate_positive(
        value: Any,
        field_name: str,
    ) -> float:
        """Validate a finite positive numeric value."""

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{field_name} must be finite."
            )

        if value <= 0.0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return value


__all__ = [
    "Branch",
]
