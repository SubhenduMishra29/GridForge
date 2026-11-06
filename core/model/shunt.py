# ============================================================
# File: core/model/shunt.py
# GridForge V2 — Shunt Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Shunt Model
==========================

Authoritative single-terminal shunt electrical model.

Architecture
------------

    ElectricalObject
          +
       Injection
          |
          v
        Shunt
          |
          v
       Terminal
          |
          v
       Endpoint
          |
          v
       Network

The Shunt owns:

    - identity
    - shunt conductance
    - shunt susceptance
    - operational state
    - exactly one authoritative Terminal
    - optional engineering extensions

The Shunt does NOT own:

    - Network topology
    - Bus collections
    - solver state
    - Y-bus construction
    - SLD geometry
    - UI state

Terminal Contract
-----------------

The Shunt owns exactly one Terminal.

The Terminal owns endpoint state.

Canonical operations are:

    connect_endpoint(endpoint)
        -> Terminal.attach(endpoint)

    disconnect_endpoint()
        -> Terminal.detach()

Endpoint state is never duplicated inside Shunt.

Electrical Convention
---------------------

The shunt is represented as an admittance:

    Y = G + jB

The exact P/Q injection is calculated from the connected
endpoint voltage when the endpoint exposes a compatible
voltage representation.

For compatibility with the existing model, the direct
admittance components remain authoritative model parameters.

An out-of-service Shunt contributes zero injection.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Shunt(ElectricalObject, Injection):
    """
    Single-terminal shunt admittance model.

    Parameters
    ----------
    g_pu:
        Shunt conductance in per-unit.

    b_pu:
        Shunt susceptance in per-unit.

    Positive/negative sign interpretation of ``b_pu`` follows
    the existing GridForge shunt convention and is preserved
    without reinterpretation by this model.
    """

    TYPE = "SHUNT"

    def __init__(
        self,
        id: str,
        *,
        endpoint: Any = None,
        terminal: Terminal | None = None,
        bus: Any = None,
        g_pu: float = 0.0,
        b_pu: float = 0.0,
        name: str = "",
        in_service: bool = True,
    ) -> None:
        """
        Construct a Shunt.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint:
            Optional initial electrical endpoint.

        terminal:
            Optional pre-created authoritative Terminal.

        bus:
            Compatibility alias for the initial endpoint.

        g_pu:
            Conductance in per-unit.

        b_pu:
            Susceptance in per-unit.

        name:
            Human-readable name.

        in_service:
            Initial operational state.

        Notes
        -----
        If an externally supplied Terminal is provided, it must
        already belong to this Shunt. Terminal ownership is never
        mutated by this class.
        """

        ElectricalObject.__init__(
            self,
            id=id,
            name=name,
        )

        # ========================================================
        # ENDPOINT COMPATIBILITY
        # ========================================================

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

        # ========================================================
        # ADMITTANCE
        # ========================================================

        self.g_pu = self._validate_finite(
            g_pu,
            "g_pu",
        )

        self.b_pu = self._validate_finite(
            b_pu,
            "b_pu",
        )

        # ========================================================
        # SERVICE STATE
        # ========================================================

        self.in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        # ========================================================
        # AUTHORITATIVE TERMINAL
        # ========================================================

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
                    f"Shunt '{self.id}' terminal owner "
                    "must be this Shunt."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "Shunt terminal role must be 'terminal'."
                )

            self._terminal = terminal

        # ========================================================
        # OPTIONAL EXTENSIONS
        # ========================================================

        self._extensions: dict[str, Any] = {}

        # ========================================================
        # INITIAL ENDPOINT
        # ========================================================

        if endpoint is not None:
            self.connect_endpoint(
                endpoint
            )

        # ========================================================
        # COMMON VALIDATION CONTRACT
        # ========================================================

        self.validate()

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # ============================================================
    # TERMINAL
    # ============================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative physical Terminal.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return the Shunt's authoritative terminal collection.
        """

        return (
            self._terminal,
        )

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    @property
    def endpoint(self) -> Any | None:
        """
        Return the authoritative physical electrical endpoint.

        Terminal.endpoint is the sole source of endpoint truth.
        """

        return self._terminal.endpoint

    @property
    def bus(self) -> Any | None:
        """
        Compatibility accessor for the historical bus API.

        The Terminal remains authoritative.
        """

        return self._terminal.endpoint

    @bus.setter
    def bus(
        self,
        value: Any,
    ) -> None:
        """
        Compatibility setter routed through Terminal.
        """

        self.connect_endpoint(
            value
        )

    @property
    def is_connected(self) -> bool:
        """Return whether the Shunt terminal is connected."""

        return self._terminal.is_connected

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

        self._terminal.attach(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Shunt terminal.

        This does not alter service state.
        """

        self._terminal.detach()

    # ============================================================
    # ADMITTANCE
    # ============================================================

    @property
    def admittance(self) -> complex:
        """
        Return the complex shunt admittance.

            Y = G + jB
        """

        return complex(
            self.g_pu,
            self.b_pu,
        )

    @property
    def conductance_pu(self) -> float:
        """Return shunt conductance in per-unit."""

        return self.g_pu

    @conductance_pu.setter
    def conductance_pu(
        self,
        value: float,
    ) -> None:
        self.g_pu = self._validate_finite(
            value,
            "conductance_pu",
        )

    @property
    def susceptance_pu(self) -> float:
        """Return shunt susceptance in per-unit."""

        return self.b_pu

    @susceptance_pu.setter
    def susceptance_pu(
        self,
        value: float,
    ) -> None:
        self.b_pu = self._validate_finite(
            value,
            "susceptance_pu",
        )

    def set_admittance(
        self,
        g_pu: float,
        b_pu: float,
    ) -> None:
        """Set conductance and susceptance."""

        self.g_pu = self._validate_finite(
            g_pu,
            "g_pu",
        )

        self.b_pu = self._validate_finite(
            b_pu,
            "b_pu",
        )

    # ============================================================
    # POWER INJECTION
    # ============================================================

    def get_power(
        self,
        voltage_pu: complex | float = 1.0,
    ) -> tuple[float, float]:
        """
        Return the shunt's P/Q injection.

        Parameters
        ----------
        voltage_pu:
            Complex or real per-unit voltage at the shunt
            terminal.

        Returns
        -------
        tuple[float, float]
            Active and reactive power injection in per-unit.

        Notes
        -----
        For:

            Y = G + jB
            V = voltage_pu

        the current is:

            I = YV

        and complex power injection is:

            S = V * conjugate(I)

        giving:

            P = G |V|²
            Q = -B |V|²

        This preserves the standard network injection convention.
        """

        if not self.in_service:
            return (
                0.0,
                0.0,
            )

        voltage = self._validate_voltage(
            voltage_pu
        )

        magnitude_squared = (
            abs(voltage) ** 2
        )

        p = (
            self.g_pu
            * magnitude_squared
        )

        q = (
            -self.b_pu
            * magnitude_squared
        )

        return (
            p,
            q,
        )

    def get_injection(
        self,
        voltage_pu: complex | float = 1.0,
    ) -> tuple[float, float]:
        """
        Explicit alias for get_power().
        """

        return self.get_power(
            voltage_pu
        )

    # ============================================================
    # SERVICE STATE
    # ============================================================

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
        """Set service state without implicit coercion."""

        self.in_service = self._validate_bool(
            value,
            "in_service",
        )

    def connect(self) -> None:
        """
        Compatibility service-state operation.

        This changes operational state only; it does not attach
        the Terminal.
        """

        self.put_in_service()

    def disconnect(self) -> None:
        """
        Compatibility service-state operation.

        This changes operational state only; it does not detach
        the Terminal.
        """

        self.take_out_of_service()

    def close(self) -> None:
        """Compatibility alias for put_in_service()."""

        self.put_in_service()

    def trip(self) -> None:
        """Compatibility alias for take_out_of_service()."""

        self.take_out_of_service()

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Shunt-local engineering parameters.
        """

        self.g_pu = self._validate_finite(
            self.g_pu,
            "g_pu",
        )

        self.b_pu = self._validate_finite(
            self.b_pu,
            "b_pu",
        )

        self.in_service = self._validate_bool(
            self.in_service,
            "in_service",
        )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Shunt model.

        Terminal connectivity is validated independently from
        global Network topology.
        """

        self.validate_parameters()

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Shunt terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Shunt '{self.id}' terminal ownership is invalid."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "Shunt terminal role must be 'terminal'."
            )

        self._terminal.validate()

        return super().validate()

    # ============================================================
    # EXTENSIONS
    # ============================================================

    def register_extension(
        self,
        extension_id: str,
        extension: Any,
    ) -> None:
        """
        Register an optional engineering extension.
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
        """Return an extension, or None."""

        return self._extensions.get(
            extension_id
        )

    def remove_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Remove and return an extension."""

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

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(
        self,
        voltage_pu: complex | float = 1.0,
    ) -> dict[str, Any]:
        """Return structured Shunt diagnostics."""

        endpoint = self._terminal.endpoint

        endpoint_id = None

        if endpoint is not None:
            endpoint_id = getattr(
                endpoint,
                "id",
                endpoint,
            )

        p, q = self.get_power(
            voltage_pu
        )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal,
            "terminal_role": self._terminal.role,

            "endpoint": endpoint_id,
            "bus": endpoint_id,
            "is_connected":
                self._terminal.is_connected,

            "g_pu": self.g_pu,
            "b_pu": self.b_pu,

            "admittance":
                self.admittance,

            "p_pu": p,
            "q_pu": q,

            "in_service":
                self.in_service,

            "extensions":
                self.extension_ids,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        endpoint = self._terminal.endpoint

        endpoint_id = None

        if endpoint is not None:
            endpoint_id = getattr(
                endpoint,
                "id",
                endpoint,
            )

        return (
            f"<Shunt "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"G={self.g_pu:.6f} pu, "
            f"B={self.b_pu:.6f} pu, "
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
        """Convert to float and require a finite value."""

        try:
            numeric = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(
            numeric
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return numeric

    @staticmethod
    def _validate_voltage(
        value: complex | float,
    ) -> complex:
        """
        Validate a complex or real per-unit voltage.
        """

        try:
            voltage = complex(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "voltage_pu must be numeric."
            ) from exc

        if not (
            math.isfinite(
                voltage.real
            )
            and math.isfinite(
                voltage.imag
            )
        ):
            raise ValueError(
                "voltage_pu must be finite."
            )

        return voltage

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """Validate a strict boolean."""

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Shunt",
]
