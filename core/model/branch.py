# ============================================================
# File: core/model/branch.py
#
# GridForge V2 — Branch Model
#
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Branch Model
=========================

Generic two-terminal electrical branch foundation.

Architecture
------------

    ElectricalObject
          |
          v
        Branch
        /    \
       /      \
from_terminal  to_terminal
       |          |
       v          v
    endpoint    endpoint

A Branch is a physical electrical model.

The Branch owns:

    - stable identity through ElectricalObject;
    - exactly two physical Terminals;
    - branch-local electrical parameters;
    - branch-local operational state;
    - branch-local validation;
    - optional model extensions.

The Branch does NOT own:

    - Network topology;
    - Bus collections;
    - Network endpoint resolution;
    - Y-bus construction;
    - solver indices;
    - numerical state;
    - study-specific classification;
    - load-flow solving;
    - short-circuit solving;
    - protection calculations;
    - dynamic simulation;
    - SLD geometry;
    - GUI state;
    - persistence.

Terminal Ownership
------------------

Every Branch creates and owns its own two Terminals.

Therefore:

    Branch.from_terminal.owner is Branch
    Branch.to_terminal.owner   is Branch

An existing Terminal cannot be supplied as an endpoint.

This prevents:

    - Terminal sharing;
    - ownership transfer;
    - ownership reassignment;
    - Terminal-to-Terminal chaining.

Endpoint Boundary
-----------------

A Branch Terminal stores an endpoint reference.

The model layer does not resolve that endpoint into Network
topology.

Therefore this module intentionally has NO dependency on:

    core.network.endpoint
    core.network
    Network

Endpoint interpretation and topology reconciliation belong to the
Network/application layer.

Validation Boundary
-------------------

The base ElectricalObject validation contract is:

    ElectricalObject.validate()
            |
            v
    self.validate_parameters()

Branch.__init__() deliberately does NOT call
self.validate_parameters().

This is required because subclasses such as Line, Cable and
Transformer override validate_parameters(). Calling an overridable
method during base construction could execute subclass validation
before the subclass has completed initialization.

The complete object must first be constructed.

After construction:

    specialized_model.validate()
            |
            v
    ElectricalObject.validate()
            |
            v
    specialized_model.validate_parameters()
            |
            v
    Branch.validate_parameters()

This preserves normal Python dynamic dispatch while avoiding
partially initialized subclass state.

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

    Specialized branch equipment may inherit this class.

    The Branch owns exactly two Terminals:

        from_terminal
        to_terminal

    The Terminals are created by the Branch and are never adopted
    from another object.
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
        """
        Construct a generic two-terminal Branch.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional initial endpoint for the from-side terminal.

        endpoint_to:
            Optional initial endpoint for the to-side terminal.

        r:
            Optional generic series resistance in per-unit.

        x:
            Optional generic series reactance in per-unit.

        b:
            Optional generic total shunt susceptance in per-unit.

        name:
            Human-readable object name.

        rate_mva:
            Optional branch rating in MVA.

        tap:
            Generic positive tap ratio.

        shift:
            Generic phase shift in radians.

        in_service:
            Operational state.

        Notes
        -----
        Existing Terminal objects are not accepted as endpoints.

        Branch construction does not invoke validate_parameters().
        Validation occurs only after the complete object has been
        initialized.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # ============================================================
        # TERMINALS
        # ============================================================

        self.from_terminal = self._create_terminal(
            endpoint=endpoint_from,
            role="from",
        )

        self.to_terminal = self._create_terminal(
            endpoint=endpoint_to,
            role="to",
        )

        # ============================================================
        # GENERIC ELECTRICAL PARAMETERS
        # ============================================================

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

        # ============================================================
        # GENERIC TAP / PHASE PARAMETERS
        # ============================================================

        self.tap = self._validate_positive(
            tap,
            "tap",
        )

        self.shift = self._validate_finite(
            shift,
            "shift",
        )

        # ============================================================
        # RATING
        # ============================================================

        if rate_mva is None:
            self.rate_mva = None
        else:
            self.rate_mva = self._validate_positive(
                rate_mva,
                "rate_mva",
            )

        # ============================================================
        # OPERATIONAL STATE
        # ============================================================

        self.in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        # ============================================================
        # EXTENSIONS
        # ============================================================

        self._extensions: dict[str, Any] = {}

        # IMPORTANT:
        #
        # Do not call self.validate_parameters() here.
        #
        # Subclasses override validate_parameters(). Validation is
        # deliberately deferred until the complete object exists.

    # ================================================================
    # IDENTITY
    # ================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """

        return self.TYPE

    # ================================================================
    # TERMINAL CREATION
    # ================================================================

    def _create_terminal(
        self,
        endpoint: Any = None,
        *,
        role: str,
    ) -> Terminal:
        """
        Create a Branch-owned Terminal.

        An existing Terminal cannot be supplied as an endpoint.

        The endpoint is a domain-level reference only. Network
        topology resolution is outside this model.
        """

        if isinstance(
            endpoint,
            Terminal,
        ):
            raise TypeError(
                f"Branch '{self.id}' endpoint '{role}' "
                "cannot be a Terminal. Branch terminals are "
                "owned exclusively by the Branch."
            )

        return Terminal(
            endpoint=endpoint,
            owner=self,
            role=role,
        )

    # ================================================================
    # TERMINALS
    # ================================================================

    @property
    def terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the authoritative Branch terminals.
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # ================================================================
    # ENDPOINTS
    # ================================================================

    @property
    def from_endpoint(self) -> Any:
        """
        Return the local endpoint stored by the from terminal.
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self) -> Any:
        """
        Return the local endpoint stored by the to terminal.
        """

        return self.to_terminal.endpoint

    def endpoints(
        self,
    ) -> tuple[Any, Any]:
        """
        Return the authoritative endpoint pair.
        """

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # ================================================================
    # CONNECTIVITY
    # ================================================================

    @property
    def has_from_endpoint(self) -> bool:
        """
        Return whether the from terminal has an endpoint.
        """

        return self.from_terminal.is_connected

    @property
    def has_to_endpoint(self) -> bool:
        """
        Return whether the to terminal has an endpoint.
        """

        return self.to_terminal.is_connected

    @property
    def is_connected(self) -> bool:
        """
        Return True when both terminals have endpoints.

        This is a local model diagnostic only.

        It does not determine Network validity.
        """

        return (
            self.has_from_endpoint
            and self.has_to_endpoint
        )

    @property
    def is_fully_connected(self) -> bool:
        """
        Alias for is_connected.
        """

        return self.is_connected

    # ================================================================
    # TERMINAL ATTACHMENT
    # ================================================================

    def connect_from(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to the from terminal.

        This changes only the terminal's local endpoint reference.

        Network topology management remains outside Branch.
        """

        if isinstance(
            endpoint,
            Terminal,
        ):
            raise TypeError(
                "A Branch endpoint cannot be another Terminal."
            )

        if endpoint is None:
            raise ValueError(
                "Branch from endpoint cannot be None."
            )

        self.from_terminal.attach(
            endpoint
        )

    def connect_to(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to the to terminal.

        This changes only the terminal's local endpoint reference.

        Network topology management remains outside Branch.
        """

        if isinstance(
            endpoint,
            Terminal,
        ):
            raise TypeError(
                "A Branch endpoint cannot be another Terminal."
            )

        if endpoint is None:
            raise ValueError(
                "Branch to endpoint cannot be None."
            )

        self.to_terminal.attach(
            endpoint
        )

    def disconnect_from(self) -> None:
        """
        Detach the from-side endpoint.
        """

        self.from_terminal.detach()

    def disconnect_to(self) -> None:
        """
        Detach the to-side endpoint.
        """

        self.to_terminal.detach()

    # ================================================================
    # GENERIC ELECTRICAL PARAMETERS
    # ================================================================

    @property
    def has_per_unit_parameters(self) -> bool:
        """
        Return True when both generic r and x are defined.
        """

        return (
            self.r is not None
            and self.x is not None
        )

    @property
    def impedance(self) -> complex:
        """
        Return the generic series impedance.

            Z = R + jX
        """

        if (
            self.r is None
            or self.x is None
        ):
            raise ValueError(
                f"Branch '{self.id}' does not define "
                "generic series impedance."
            )

        return complex(
            self.r,
            self.x,
        )

    @property
    def series_impedance(self) -> complex:
        """
        Return the generic series impedance.

        Alias for impedance.
        """

        return self.impedance

    @property
    def admittance(self) -> complex:
        """
        Return the generic series admittance.

            Y = 1 / Z
        """

        z = self.impedance

        if z == 0.0 + 0.0j:
            raise ZeroDivisionError(
                f"Branch '{self.id}' has zero series impedance."
            )

        return 1.0 / z

    @property
    def series_admittance(self) -> complex:
        """
        Return the generic series admittance.

        Alias for admittance.
        """

        return self.admittance

    @property
    def shunt_admittance(self) -> complex:
        """
        Return generic total shunt admittance.

            Ysh = jB
        """

        if self.b is None:
            return 0.0 + 0.0j

        return complex(
            0.0,
            self.b,
        )

    # ================================================================
    # PER-UNIT ACCESSORS
    # ================================================================

    @property
    def r_pu(self) -> float | None:
        """
        Return resistance in per-unit.
        """

        return self.r

    @property
    def x_pu(self) -> float | None:
        """
        Return reactance in per-unit.
        """

        return self.x

    @property
    def b_pu(self) -> float | None:
        """
        Return shunt susceptance in per-unit.
        """

        return self.b

    # ================================================================
    # TAP / PHASE SHIFT
    # ================================================================

    @property
    def tap_ratio(self) -> float:
        """
        Return the generic tap ratio.
        """

        return self.tap

    @property
    def phase_shift(self) -> float:
        """
        Return the generic phase shift in radians.
        """

        return self.shift

    # ================================================================
    # RATING
    # ================================================================

    @property
    def has_rating(self) -> bool:
        """
        Return whether a rating is defined.
        """

        return self.rate_mva is not None

    def set_rating(
        self,
        rate_mva: float | None,
    ) -> None:
        """
        Set or clear the branch rating.
        """

        if rate_mva is None:
            self.rate_mva = None
            return

        self.rate_mva = self._validate_positive(
            rate_mva,
            "rate_mva",
        )

    # ================================================================
    # OPERATIONAL STATE
    # ================================================================

    def connect(self) -> None:
        """
        Place the Branch in service.

        This does not attach terminals.
        """

        self.in_service = True

    def disconnect(self) -> None:
        """
        Take the Branch out of service.

        This does not detach terminals.
        """

        self.in_service = False

    def close(self) -> None:
        """
        Place the Branch in service.

        Compatibility alias for connect().
        """

        self.connect()

    def trip(self) -> None:
        """
        Take the Branch out of service.

        Compatibility alias for disconnect().
        """

        self.disconnect()

    @property
    def is_in_service(self) -> bool:
        """
        Return whether the Branch is in service.
        """

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return whether the Branch is out of service.
        """

        return not self.in_service

    # ================================================================
    # EXTENSIONS
    # ================================================================

    def register_extension(
        self,
        extension_id: str,
        extension: Any,
    ) -> None:
        """
        Register an optional model extension.

        Extensions do not alter Branch ownership or topology.
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
        """
        Return an extension by identifier.
        """

        return self._extensions.get(
            extension_id
        )

    def remove_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """
        Remove and return an extension.
        """

        return self._extensions.pop(
            extension_id,
            None,
        )

    @property
    def extension_ids(self) -> tuple[str, ...]:
        """
        Return registered extension identifiers.
        """

        return tuple(
            self._extensions.keys()
        )

    # ================================================================
    # VALIDATION
    # ================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Branch-local parameters.

        Generic r/x/b are optional because specialized branches may
        use different physical parameterizations.
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

        self.in_service = self._validate_bool(
            self.in_service,
            "in_service",
        )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Branch object.

        ElectricalObject.validate() is deliberately used as the
        validation entry point so that the inherited validation
        contract remains authoritative.

        Dynamic dispatch then invokes the most specialized
        validate_parameters() implementation.
        """

        ElectricalObject.validate(
            self
        )

        if not isinstance(
            self.from_terminal,
            Terminal,
        ):
            raise TypeError(
                f"Branch '{self.id}' from_terminal must be Terminal."
            )

        if not isinstance(
            self.to_terminal,
            Terminal,
        ):
            raise TypeError(
                f"Branch '{self.id}' to_terminal must be Terminal."
            )

        if self.from_terminal.owner is not self:
            raise ValueError(
                f"Branch '{self.id}' from_terminal ownership is invalid."
            )

        if self.to_terminal.owner is not self:
            raise ValueError(
                f"Branch '{self.id}' to_terminal ownership is invalid."
            )

        if self.from_terminal.role != "from":
            raise ValueError(
                f"Branch '{self.id}' from_terminal role is invalid."
            )

        if self.to_terminal.role != "to":
            raise ValueError(
                f"Branch '{self.id}' to_terminal role is invalid."
            )

        return True

    # ================================================================
    # DIAGNOSTICS
    # ================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Branch-local diagnostic information.

        No Network topology or solved numerical state is included.
        """

        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "from_endpoint": (
                from_endpoint.id
                if from_endpoint is not None
                and hasattr(from_endpoint, "id")
                else from_endpoint
            ),

            "to_endpoint": (
                to_endpoint.id
                if to_endpoint is not None
                and hasattr(to_endpoint, "id")
                else to_endpoint
            ),

            "connected": self.is_connected,
            "in_service": self.in_service,

            "r": self.r,
            "x": self.x,
            "b": self.b,

            "rate_mva": self.rate_mva,

            "tap": self.tap,
            "shift": self.shift,

            "extensions": self.extension_ids,
        }

    # ================================================================
    # REPRESENTATION
    # ================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        from_id = (
            from_endpoint.id
            if from_endpoint is not None
            and hasattr(from_endpoint, "id")
            else from_endpoint
        )

        to_id = (
            to_endpoint.id
            if to_endpoint is not None
            and hasattr(to_endpoint, "id")
            else to_endpoint
        )

        return (
            f"<Branch "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"r={self.r}, "
            f"x={self.x}, "
            f"b={self.b}, "
            f"rate_mva={self.rate_mva}, "
            f"in_service={self.in_service}>"
        )

    # ================================================================
    # VALIDATION HELPERS
    # ================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite numeric value.
        """

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

    @classmethod
    def _validate_optional_finite(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Validate an optional finite numeric value.
        """

        if value is None:
            return None

        return cls._validate_finite(
            value,
            name,
        )

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite positive numeric value.
        """

        value = cls._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a strict boolean value.

        Arbitrary truthy/falsy values are deliberately rejected.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise ValueError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Branch",
]
