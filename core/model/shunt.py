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

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
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
        endpoint: Any = None,
        g_pu: float = 0.0,
        b_pu: float = 0.0,
        in_service: bool = True,
        bus: Any = None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # ENDPOINT COMPATIBILITY
        # =============================================================

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Shunt '{self.id}' received both endpoint and bus "
                "with different values."
            )

        if endpoint is None:
            endpoint = bus

        # =============================================================
        # ADMITTANCE
        # =============================================================

        self.g_pu = self._validate_finite(
            g_pu,
            "g_pu",
        )

        self.b_pu = self._validate_finite(
            b_pu,
            "b_pu",
        )

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self._validate_bool(
            in_service,
            "in_service",
        )

        self.in_service = in_service

        # =============================================================
        # AUTHORITATIVE TERMINAL
        # =============================================================

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # =============================================================
        # OPTIONAL EXTENSIONS
        # =============================================================

        self._extensions: dict[str, Any] = {}

        # =============================================================
        # COMMON VALIDATION CONTRACT
        # =============================================================

        self.validate()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Shunt's authoritative terminal."""

        return (
            self.terminal,
        )

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def endpoint(self) -> Any:
        """
        Return the authoritative physical electrical endpoint.
        """

        return self.terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor for the historical bus API.

        The Terminal remains authoritative.
        """

        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return whether the Shunt terminal is connected."""

        return self.terminal.is_connected

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the Shunt terminal.

        Global network topology is managed by the Network layer.
        """

        if endpoint is None:
            raise ValueError(
                f"Shunt '{self.id}' endpoint cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Shunt terminal.

        This does not alter service state.
        """

        self.terminal.disconnect()

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the Shunt is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the Shunt is out of service."""

        return not self.in_service

    @property
    def is_available(self) -> bool:
        """Return whether the Shunt is electrically active."""

        return self.in_service

    def put_in_service(self) -> None:
        """Place the Shunt in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the Shunt out of service."""

        self.in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """Set service state without silently coercing values."""

        self._validate_bool(
            value,
            "in_service",
        )

        self.in_service = value

    def connect(self) -> None:
        """
        Compatibility service-state operation.

        This changes operating state, not network topology.
        """

        self.put_in_service()

    def disconnect(self) -> None:
        """
        Compatibility service-state operation.

        This changes operating state, not network topology.
        """

        self.take_out_of_service()

    def close(self) -> None:
        """Compatibility alias for placing the Shunt in service."""

        self.put_in_service()

    def trip(self) -> None:
        """Compatibility alias for taking the Shunt out of service."""

        self.take_out_of_service()

    # =================================================================
    # ADMITTANCE
    # =================================================================

    @property
    def admittance(self) -> complex:
        """
        Return the effective complex shunt admittance.

        Y = G + jB

        When out of service:

            Y = 0 + j0
        """

        if not self.in_service:
            return 0.0 + 0.0j

        return complex(
            self.g_pu,
            self.b_pu,
        )

    @property
    def y(self) -> complex:
        """Compatibility alias for admittance."""

        return self.admittance

    @property
    def conductance(self) -> float:
        """Return conductance G in per-unit."""

        return self.g_pu

    @property
    def susceptance(self) -> float:
        """Return susceptance B in per-unit."""

        return self.b_pu

    def get_admittance(self) -> complex:
        """
        Return the effective network admittance.

        The Shunt does not perform matrix stamping.
        """

        return self.admittance

    # =================================================================
    # ADMITTANCE MUTATION
    # =================================================================

    def set_admittance(
        self,
        g_pu: float,
        b_pu: float,
    ) -> None:
        """Set the complete complex admittance."""

        self.g_pu = self._validate_finite(
            g_pu,
            "g_pu",
        )

        self.b_pu = self._validate_finite(
            b_pu,
            "b_pu",
        )

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

    # =================================================================
    # SHUNT CLASSIFICATION
    # =================================================================

    @property
    def is_capacitive(self) -> bool:
        """Return True when susceptance is positive."""

        return self.b_pu > 0.0

    @property
    def is_inductive(self) -> bool:
        """Return True when susceptance is negative."""

        return self.b_pu < 0.0

    @property
    def is_purely_resistive(self) -> bool:
        """Return True when susceptance is effectively zero."""

        return math.isclose(
            self.b_pu,
            0.0,
            abs_tol=1e-12,
        )

    @property
    def is_zero_admittance(self) -> bool:
        """Return True when both G and B are effectively zero."""

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

    # =================================================================
    # ADMITTANCE CHARACTERISTICS
    # =================================================================

    @property
    def magnitude(self) -> float:
        """Return magnitude of the effective admittance."""

        return abs(
            self.admittance
        )

    @property
    def angle_rad(self) -> float:
        """Return effective admittance angle in radians."""

        return cmath.phase(
            self.admittance
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Shunt-local engineering parameters.

        Zero admittance is valid.

        Network topology is deliberately excluded.
        """

        self.g_pu = self._validate_finite(
            self.g_pu,
            "g_pu",
        )

        self.b_pu = self._validate_finite(
            self.b_pu,
            "b_pu",
        )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        if self.terminal.owner is not self:
            raise ValueError(
                f"Shunt '{self.id}' terminal ownership is invalid."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Shunt through the common model contract.
        """

        return super().validate()

    # Backward-compatible private validation entry point.
    def _validate(self) -> None:
        """Validate current Shunt parameters."""

        self.validate_parameters()

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

        Extensions must not bypass Core/Application command
        boundaries.
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

        self._extensions[extension_id] = extension

    def get_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Return a registered extension."""

        return self._extensions.get(
            extension_id
        )

    def remove_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Remove and return a registered extension."""

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
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured Shunt diagnostics."""

        endpoint_id = None

        if self.endpoint is not None:
            endpoint_id = getattr(
                self.endpoint,
                "id",
                self.endpoint,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "g_pu": self.g_pu,
            "b_pu": self.b_pu,

            "admittance": self.admittance,

            "in_service": self.in_service,
            "is_available": self.is_available,

            "endpoint": endpoint_id,
            "is_connected": self.is_connected,

            "is_capacitive": self.is_capacitive,
            "is_inductive": self.is_inductive,
            "is_purely_resistive":
                self.is_purely_resistive,
            "is_zero_admittance":
                self.is_zero_admittance,

            "extensions": self.extension_ids,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Shunt "
            f"id={self.id}, "
            f"G={self.g_pu:.6f} pu, "
            f"B={self.b_pu:.6f} pu, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require a finite value."""

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> None:
        """Require an actual boolean."""

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )


__all__ = [
    "Shunt",
]
