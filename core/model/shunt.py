# core/model/shunt.py
"""
GridForge V2 Shunt Model
========================

Author:
    Subhendu Mishra

A Shunt is a single-terminal passive electrical element represented
by its complex admittance:

    Y = G + jB

where:

    G > 0  -> conductance
    B > 0  -> capacitive susceptance
    B < 0  -> inductive susceptance

Architecture
------------

    Shunt
      |
      +-- ElectricalObject
      +-- Terminal
      +-- complex admittance
      |
      +-- service state

The Shunt does NOT:

    - own network topology
    - maintain bus collections
    - add itself to a Grid
    - build a Y-bus
    - solve power flow
    - solve short circuit
    - perform protection calculations
    - own SLD state
    - own GUI state
    - perform dynamic simulation

The numerical/study layer consumes the Shunt admittance and performs
the appropriate network calculation or matrix stamping.
"""

from __future__ import annotations

import cmath
import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Shunt(ElectricalObject):
    """
    Static single-terminal shunt admittance element.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    endpoint:
        Physical electrical endpoint. May be None.

    g_pu:
        Conductance in per-unit.

    b_pu:
        Susceptance in per-unit.

        Positive B = capacitive.
        Negative B = inductive.

    in_service:
        Whether the shunt is electrically active.

    bus:
        Backward-compatible endpoint alias.
    """

    TYPE = "SHUNT"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint=None,
        g_pu: float = 0.0,
        b_pu: float = 0.0,
        in_service: bool = True,
        bus=None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Endpoint compatibility
        # ---------------------------------------------------------

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Shunt '{self.id}' received both 'endpoint' and "
                "'bus' with different values."
            )

        if endpoint is None:
            endpoint = bus

        # ---------------------------------------------------------
        # Admittance parameters
        # ---------------------------------------------------------

        self.g_pu = self._validate_finite(
            g_pu,
            "g_pu",
        )

        self.b_pu = self._validate_finite(
            b_pu,
            "b_pu",
        )

        # ---------------------------------------------------------
        # Service state
        # ---------------------------------------------------------

        self.in_service = bool(in_service)

        # ---------------------------------------------------------
        # Physical terminal
        # ---------------------------------------------------------

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # ---------------------------------------------------------
        # Optional engineering extensions
        # ---------------------------------------------------------

        self._extensions: dict[str, Any] = {}

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""
        return self.TYPE

    # =============================================================
    # CONNECTIVITY
    # =============================================================

    @property
    def endpoint(self):
        """
        Return the authoritative physical electrical endpoint.
        """
        return self.terminal.endpoint

    @property
    def bus(self):
        """
        Compatibility accessor.

        The terminal is authoritative; this property exists only
        for compatibility with code using the historical bus API.
        """
        return self.terminal.bus

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Shunt electrical terminal."""
        return (self.terminal,)

    @property
    def is_connected(self) -> bool:
        """Return whether the Shunt has an electrical endpoint."""
        return self.terminal.is_connected

    def connect_endpoint(self, endpoint) -> None:
        """
        Connect the Shunt to an electrical endpoint.

        Global topology is managed outside the Shunt model.
        """
        self.terminal.connect(endpoint)

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Shunt from its electrical endpoint.

        This does not change service state.
        """
        self.terminal.disconnect()

    # =============================================================
    # SERVICE STATE
    # =============================================================

    def connect(self) -> None:
        """
        Place the Shunt in service.

        This changes electrical operating state, not topology.
        """
        self.in_service = True

    def disconnect(self) -> None:
        """
        Take the Shunt out of service.

        This changes electrical operating state, not topology.
        """
        self.in_service = False

    def close(self) -> None:
        """Compatibility alias for placing the Shunt in service."""
        self.connect()

    def trip(self) -> None:
        """Compatibility alias for taking the Shunt out of service."""
        self.disconnect()

    @property
    def is_available(self) -> bool:
        """Return whether the Shunt is in service."""
        return self.in_service

    # =============================================================
    # ADMITTANCE
    # =============================================================

    @property
    def admittance(self) -> complex:
        """
        Return the complex shunt admittance.

        Y = G + jB

        When out of service, the effective network admittance is zero.
        """
        if not self.in_service:
            return 0.0 + 0.0j

        return complex(
            self.g_pu,
            self.b_pu,
        )

    @property
    def y(self) -> complex:
        """Alias for admittance."""
        return self.admittance

    @property
    def conductance(self) -> float:
        """Return conductance G in per-unit."""
        return self.g_pu

    @property
    def susceptance(self) -> float:
        """Return susceptance B in per-unit."""
        return self.b_pu

    def set_admittance(
        self,
        g_pu: float,
        b_pu: float,
    ) -> None:
        """
        Set the complete complex admittance.

        Parameters
        ----------
        g_pu:
            Conductance in per-unit.

        b_pu:
            Susceptance in per-unit.
        """

        g_pu = self._validate_finite(
            g_pu,
            "g_pu",
        )

        b_pu = self._validate_finite(
            b_pu,
            "b_pu",
        )

        self.g_pu = g_pu
        self.b_pu = b_pu

    def set_conductance(
        self,
        g_pu: float,
    ) -> None:
        """Set conductance G in per-unit."""
        self.g_pu = self._validate_finite(
            g_pu,
            "g_pu",
        )

    def set_susceptance(
        self,
        b_pu: float,
    ) -> None:
        """Set susceptance B in per-unit."""
        self.b_pu = self._validate_finite(
            b_pu,
            "b_pu",
        )

    # =============================================================
    # SHUNT TYPE
    # =============================================================

    @property
    def is_capacitive(self) -> bool:
        """
        Return True when B is positive.

        Positive susceptance is treated as capacitive.
        """
        return self.b_pu > 0.0

    @property
    def is_inductive(self) -> bool:
        """
        Return True when B is negative.

        Negative susceptance is treated as inductive.
        """
        return self.b_pu < 0.0

    @property
    def is_purely_resistive(self) -> bool:
        """Return True when B is zero."""
        return math.isclose(
            self.b_pu,
            0.0,
            abs_tol=1e-12,
        )

    @property
    def is_zero_admittance(self) -> bool:
        """
        Return True when both G and B are zero.

        Zero admittance is valid and intentionally supported.
        """
        return (
            math.isclose(
                self.g_pu,
                0.0,
                abs_tol=1e-12,
            )
            and math.isclose(
                self.b_pu,
                0.0,
                abs_tol=1e-12,
            )
        )

    # =============================================================
    # ADMITTANCE COMPONENTS
    # =============================================================

    @property
    def magnitude(self) -> float:
        """Return magnitude of the shunt admittance."""
        return abs(self.admittance)

    @property
    def angle_rad(self) -> float:
        """Return admittance angle in radians."""
        return cmath.phase(self.admittance)

    # =============================================================
    # NUMERICAL REPRESENTATION
    # =============================================================

    def get_admittance(self) -> complex:
        """
        Return the effective network admittance.

        This method provides the numerical/study layer with the
        value required for network calculations.

        The Shunt does not perform matrix stamping itself.
        """
        return self.admittance

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Shunt-local parameters.

        Zero admittance is valid.

        This method deliberately does not validate network topology.
        """

        self._validate_finite(
            self.g_pu,
            "g_pu",
        )

        self._validate_finite(
            self.b_pu,
            "b_pu",
        )

        return True

    # Backward-compatible private validation entry point.
    def _validate(self) -> None:
        """Validate current Shunt parameters."""
        self.validate_parameters()

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

        Extensions must not bypass Core/Application command
        boundaries.
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
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "g_pu": self.g_pu,
            "b_pu": self.b_pu,
            "admittance": self.admittance,
            "in_service": self.in_service,
            "endpoint": self.endpoint,
            "is_connected": self.is_connected,
            "is_capacitive": self.is_capacitive,
            "is_inductive": self.is_inductive,
            "is_zero_admittance": self.is_zero_admittance,
            "extensions": self.extension_ids,
        }

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
