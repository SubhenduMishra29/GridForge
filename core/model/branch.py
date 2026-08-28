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

A Branch is the common two-terminal electrical model for equipment
that transfers electrical quantities between two network endpoints.

Architecture
------------

    ElectricalObject
          |
          v
        Branch
       /      \
  Line/Cable  Transformer/other branches

Branch owns:

    - stable identity through ElectricalObject;
    - exactly two authoritative terminals;
    - from/to endpoint references;
    - branch-local operational state;
    - branch-local rating and generic branch parameters.

Branch does NOT own:

    - Bus objects;
    - Network topology;
    - Network collections;
    - endpoint-to-Bus resolution;
    - Y-bus construction;
    - solver indices;
    - study-specific state;
    - solved numerical state;
    - GUI/SLD state;
    - persistence;
    - Terminal objects supplied by external callers.

Terminal Boundary
-----------------

A Branch creates and owns its two Terminal objects.

External Terminal adoption/sharing is deliberately unsupported.

The authoritative branch interface is:

    from_terminal
    to_terminal

and their endpoint references:

    from_endpoint
    to_endpoint

A Branch does not expose from_bus or to_bus.

Bus resolution is a Network responsibility.

Validation Boundary
-------------------

Validation is entered through:

    ElectricalObject.validate()

which dynamically dispatches to:

    self.validate_parameters()

Branch therefore validates its own branch-local parameters and
then explicitly propagates validation to:

    ElectricalObject.validate_parameters()

This allows subclasses such as Line to extend the validation chain:

    Line.validate_parameters()
            |
            v
    Branch.validate_parameters()
            |
            v
    ElectricalObject.validate_parameters()

Construction Boundary
---------------------

Branch does not call validate() or validate_parameters() from its
constructor.

A subclass must be allowed to finish construction before complete
validation occurs.

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
    Common two-terminal electrical branch model.

    Branch is an electrical model abstraction and not a Network
    topology object.

    Each Branch owns exactly two Terminal instances:

        from_terminal
        to_terminal

    Endpoints are references carried by the terminals. Their
    interpretation and connection to Network topology remain
    outside the Branch model.
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
        in_service: bool = True,
    ) -> None:
        """
        Construct a two-terminal Branch.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional endpoint reference for the from terminal.

        endpoint_to:
            Optional endpoint reference for the to terminal.

        r:
            Optional series resistance in per-unit.

        x:
            Optional series reactance in per-unit.

        b:
            Optional total shunt susceptance in per-unit.

        name:
            Human-readable branch name.

        rate_mva:
            Optional branch rating in MVA.

        in_service:
            Operational state.

        Notes
        -----
        The Branch always creates its own terminals.

        External Terminal objects are not accepted or adopted.

        Validation is deliberately deferred until construction of
        the complete concrete model.
        """

        super().__init__(
            id=id,
            name=name,
        )

        self._from_terminal = Terminal(
            owner=self,
            role="FROM",
            endpoint=endpoint_from,
        )

        self._to_terminal = Terminal(
            owner=self,
            role="TO",
            endpoint=endpoint_to,
        )

        self._r = self._validate_optional_finite(
            r,
            "r",
        )

        self._x = self._validate_optional_finite(
            x,
            "x",
        )

        self._b = self._validate_optional_finite(
            b,
            "b",
        )

        self._rate_mva = self._validate_optional_positive(
            rate_mva,
            "rate_mva",
        )

        self._in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        # Deliberately no validate() call here.
        #
        # A concrete subclass must be allowed to finish
        # initialization before complete validation occurs.

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
    # TERMINALS
    # ================================================================

    @property
    def from_terminal(self) -> Terminal:
        """
        Return the authoritative from terminal.

        The returned Terminal is owned exclusively by this Branch.
        """

        return self._from_terminal

    @property
    def to_terminal(self) -> Terminal:
        """
        Return the authoritative to terminal.

        The returned Terminal is owned exclusively by this Branch.
        """

        return self._to_terminal

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the two authoritative Branch terminals.

        Terminal ownership remains inside the Branch model.
        """

        return (
            self._from_terminal,
            self._to_terminal,
        )

    # ================================================================
    # ENDPOINT REFERENCES
    # ================================================================

    @property
    def from_endpoint(self) -> Any:
        """
        Return the endpoint reference associated with the from
        terminal.

        The endpoint is not interpreted as a Bus by Branch.
        """

        return self._from_terminal.endpoint

    @property
    def to_endpoint(self) -> Any:
        """
        Return the endpoint reference associated with the to
        terminal.

        The endpoint is not interpreted as a Bus by Branch.
        """

        return self._to_terminal.endpoint

    @property
    def endpoints(self) -> tuple[Any, Any]:
        """
        Return the two endpoint references.
        """

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # ================================================================
    # ENDPOINT MUTATION
    # ================================================================

    def set_from_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Set the from-terminal endpoint reference.

        Network topology validation is outside Branch.
        """

        self._from_terminal.set_endpoint(
            endpoint
        )

    def set_to_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Set the to-terminal endpoint reference.

        Network topology validation is outside Branch.
        """

        self._to_terminal.set_endpoint(
            endpoint
        )

    # ================================================================
    # CONNECTIVITY
    # ================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both Branch terminals have endpoints.
        """

        return (
            self._from_terminal.is_connected
            and self._to_terminal.is_connected
        )

    @property
    def is_partially_connected(self) -> bool:
        """
        Return True when exactly one Branch terminal has an
        endpoint.
        """

        return (
            self._from_terminal.is_connected
            != self._to_terminal.is_connected
        )

    @property
    def is_open(self) -> bool:
        """
        Return True when neither Branch terminal has an endpoint.
        """

        return (
            not self._from_terminal.is_connected
            and not self._to_terminal.is_connected
        )

    def connect(
        self,
        endpoint_from: Any,
        endpoint_to: Any,
    ) -> None:
        """
        Assign both endpoint references.

        This method performs local terminal assignment only.

        Network-level topology validation remains outside Branch.
        """

        if endpoint_from is None:
            raise ValueError(
                "Branch from endpoint cannot be None."
            )

        if endpoint_to is None:
            raise ValueError(
                "Branch to endpoint cannot be None."
            )

        self._from_terminal.set_endpoint(
            endpoint_from
        )

        self._to_terminal.set_endpoint(
            endpoint_to
        )

    def disconnect(self) -> None:
        """
        Disconnect both Branch terminals.

        The Branch remains a valid model object after
        disconnection.
        """

        self._from_terminal.disconnect()
        self._to_terminal.disconnect()

    # ================================================================
    # ELECTRICAL PARAMETERS
    # ================================================================

    @property
    def r(self) -> float | None:
        """
        Return series resistance in per-unit.
        """

        return self._r

    @r.setter
    def r(
        self,
        value: float | None,
    ) -> None:
        self._r = self._validate_optional_finite(
            value,
            "r",
        )

    @property
    def x(self) -> float | None:
        """
        Return series reactance in per-unit.
        """

        return self._x

    @x.setter
    def x(
        self,
        value: float | None,
    ) -> None:
        self._x = self._validate_optional_finite(
            value,
            "x",
        )

    @property
    def b(self) -> float | None:
        """
        Return total shunt susceptance in per-unit.
        """

        return self._b

    @b.setter
    def b(
        self,
        value: float | None,
    ) -> None:
        self._b = self._validate_optional_finite(
            value,
            "b",
        )

    # ================================================================
    # COMMON BRANCH ALIASES
    # ================================================================

    @property
    def resistance(self) -> float | None:
        """
        Return series resistance.

        Alias for r.
        """

        return self._r

    @resistance.setter
    def resistance(
        self,
        value: float | None,
    ) -> None:
        self.r = value

    @property
    def reactance(self) -> float | None:
        """
        Return series reactance.

        Alias for x.
        """

        return self._x

    @reactance.setter
    def reactance(
        self,
        value: float | None,
    ) -> None:
        self.x = value

    @property
    def shunt_susceptance(self) -> float | None:
        """
        Return total shunt susceptance.

        Alias for b.
        """

        return self._b

    @shunt_susceptance.setter
    def shunt_susceptance(
        self,
        value: float | None,
    ) -> None:
        self.b = value

    # ================================================================
    # RATING
    # ================================================================

    @property
    def rate_mva(self) -> float | None:
        """
        Return the optional branch rating in MVA.
        """

        return self._rate_mva

    @rate_mva.setter
    def rate_mva(
        self,
        value: float | None,
    ) -> None:
        self._rate_mva = self._validate_optional_positive(
            value,
            "rate_mva",
        )

    @property
    def rating_mva(self) -> float | None:
        """
        Compatibility alias for rate_mva.
        """

        return self._rate_mva

    @rating_mva.setter
    def rating_mva(
        self,
        value: float | None,
    ) -> None:
        self.rate_mva = value

    # ================================================================
    # OPERATIONAL STATE
    # ================================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the Branch is in service.
        """

        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = self._validate_bool(
            value,
            "in_service",
        )

    @property
    def is_in_service(self) -> bool:
        """
        Compatibility alias for in_service.
        """

        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the Branch is out of service.
        """

        return not self._in_service

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set the operational state.
        """

        self.in_service = value

    def close(self) -> None:
        """
        Place the Branch in service.
        """

        self._in_service = True

    def trip(self) -> None:
        """
        Remove the Branch from service.
        """

        self._in_service = False

    # ================================================================
    # VALIDATION
    # ================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Branch-local parameters.

        The Base validation contract is explicitly propagated
        through ElectricalObject.validate_parameters().

        This is essential for subclasses.

        Validation chain:

            Line.validate_parameters()
                    |
                    v
            Branch.validate_parameters()
                    |
                    v
            ElectricalObject.validate_parameters()
        """

        ElectricalObject.validate_parameters(
            self
        )

        self._r = self._validate_optional_finite(
            self._r,
            "r",
        )

        self._x = self._validate_optional_finite(
            self._x,
            "x",
        )

        self._b = self._validate_optional_finite(
            self._b,
            "b",
        )

        self._rate_mva = self._validate_optional_positive(
            self._rate_mva,
            "rate_mva",
        )

        self._in_service = self._validate_bool(
            self._in_service,
            "in_service",
        )

        if (
            self._r is not None
            and self._x is not None
            and self._r == 0.0
            and self._x == 0.0
        ):
            raise ValueError(
                f"Branch '{self.id}' cannot have zero "
                "series impedance."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Branch.

        The authoritative validation entry point is inherited
        from ElectricalObject.

        Dynamic dispatch therefore invokes the concrete model's
        validate_parameters() implementation.
        """

        return super().validate()

    # ================================================================
    # DIAGNOSTICS
    # ================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Branch-local diagnostics.

        No Bus resolution or Network topology is included.
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
            "partially_connected": self.is_partially_connected,

            "r": self._r,
            "x": self._x,
            "b": self._b,

            "rate_mva": self._rate_mva,
            "in_service": self._in_service,
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
            f"r={self._r}, "
            f"x={self._x}, "
            f"b={self._b}, "
            f"rate_mva={self._rate_mva}, "
            f"in_service={self._in_service}>"
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
    def _validate_optional_positive(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Validate an optional finite positive numeric value.
        """

        if value is None:
            return None

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
        """

        if not isinstance(value, bool):
            raise ValueError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Branch",
]
