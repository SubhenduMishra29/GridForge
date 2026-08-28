# core/model/bus.py

"""
GridForge V2 — Bus Model
========================

Author:
Subhendu Mishra

A Bus is a first-class electrical network node.

Architecture
------------

    ElectricalObject
          |
          v
         Bus
          |
          +---- physical/node-local configuration
          |
          +---- authoritative Terminal
          |
          v
        Network

The Bus represents the physical electrical node.

The Bus owns:

    - stable identity;
    - human-readable name;
    - nominal voltage;
    - operational state;
    - optional initial voltage conditions;
    - exactly one authoritative electrical Terminal.

The Bus does NOT own:

    - Network collections;
    - topology collections;
    - PQ / PV / SLACK study classification;
    - study-specific P/Q/V/angle specifications;
    - solved numerical state;
    - Y-bus matrices;
    - solver indices;
    - Jacobians;
    - load-flow calculations;
    - short-circuit calculations;
    - dynamic simulation;
    - protection calculations;
    - control logic;
    - SLD geometry;
    - GUI state;
    - persistence logic.

Study Boundary
--------------

PQ / PV / SLACK is a property of a particular study formulation,
not an intrinsic physical property of a Bus.

Study-specific quantities belong to the Study / Analysis layer.

Numerical quantities and solved state belong to the Numerical layer.

Initial Conditions
------------------

A Bus may optionally provide initial voltage conditions used as
input to a numerical study.

These values are explicitly initial conditions.

They are not solved numerical state.

Topology Boundary
-----------------

The Bus does not own collections of connected equipment.

Equipment connects through Terminal objects.

Network owns authoritative topology and determines network
membership and connectivity.

A Bus may therefore exist:

    - before being connected;
    - with no connected equipment;
    - as an isolated node;
    - as part of a larger Network.

Connectivity is not itself a measure of study validity.

Electrical Boundary
-------------------

The Bus represents an electrical node.

It does not calculate the node power balance.

Load, generator, grid, shunt, and other equipment contributions
are assembled by the appropriate Network / Study / Numerical
layers.

Terminal Ownership Contract
----------------------------

The Bus permanently owns exactly one authoritative Terminal.

The Terminal is created by the Bus itself.

An externally created Terminal cannot be injected into or adopted
by a Bus.

Terminal ownership is never transferred between model objects.

This guarantees:

    Bus -> authoritative Terminal -> endpoint

rather than:

    Bus -> externally shared/adopted Terminal

Compatibility Boundary
----------------------

The repository contains application-layer code using the
``nominal_voltage_kv`` constructor name.

That name is retained as the canonical constructor parameter
because it describes the physical quantity explicitly and keeps
the verified application construction path compatible.

The ``nominal_voltage`` property remains available as a model
alias.

The old ``terminal=`` constructor injection mechanism is
intentionally removed because it violates the frozen ownership
contract.

Design Principles
-----------------

1. Bus represents a physical electrical node.
2. Bus identity is independent of study identity.
3. Study formulation is external to Bus.
4. Numerical state is external to Bus.
5. Network topology is external to Bus.
6. Terminal connectivity remains terminal-centric.
7. Bus owns exactly one authoritative Terminal.
8. Terminal ownership is never transferred.
9. Bus never adopts another object's Terminal.
10. Bus never constructs or owns Y-bus matrices.
11. Bus never performs numerical solving.
12. Bus never owns GUI/SLD state.
13. Device collections are owned by Network.
14. Initial voltage values are configuration/input, not solved state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Bus(ElectricalObject):
    """
    First-class electrical network node.

    The Bus owns one authoritative Terminal.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    nominal_voltage_kv:
        Nominal bus voltage in kV.

    name:
        Human-readable bus name.

    initial_voltage_magnitude:
        Initial voltage magnitude in per-unit.

    initial_voltage_angle:
        Initial voltage angle in degrees.

    in_service:
        Operational state.

    Notes
    -----
    The Bus always creates its own Terminal.

    A Terminal cannot be supplied to the constructor.

    This makes Terminal ownership explicit and prevents terminal
    sharing or ownership transfer between model objects.
    """

    TYPE = "BUS"

    def __init__(
        self,
        id: str,
        *,
        nominal_voltage_kv: float,
        name: str = "",
        initial_voltage_magnitude: float = 1.0,
        initial_voltage_angle: float = 0.0,
        in_service: bool = True,
    ) -> None:
        """
        Create a Bus and its authoritative Terminal.
        """

        ElectricalObject.__init__(
            self,
            id=id,
            name=name,
        )

        self._nominal_voltage = (
            self._validate_nominal_voltage(
                nominal_voltage_kv
            )
        )

        self._initial_voltage_magnitude = (
            self._validate_voltage_magnitude(
                initial_voltage_magnitude,
                "initial_voltage_magnitude",
            )
        )

        self._initial_voltage_angle = (
            self._validate_voltage_angle(
                initial_voltage_angle,
                "initial_voltage_angle",
            )
        )

        self._in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        # -------------------------------------------------------------
        # AUTHORITATIVE TERMINAL
        # -------------------------------------------------------------
        #
        # The Bus creates its own Terminal.
        #
        # Ownership is established during Terminal construction and
        # is never subsequently reassigned.
        #

        self._terminal = Terminal(
            owner=self,
            role="BUS",
        )

        self.validate()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """

        return self.TYPE

    # =================================================================
    # NOMINAL VOLTAGE
    # =================================================================

    @property
    def nominal_voltage(self) -> float:
        """
        Return nominal bus voltage in kV.
        """

        return self._nominal_voltage

    @nominal_voltage.setter
    def nominal_voltage(
        self,
        value: float,
    ) -> None:
        self._nominal_voltage = (
            self._validate_nominal_voltage(
                value
            )
        )

    @property
    def nominal_voltage_kv(self) -> float:
        """
        Return nominal bus voltage in kV.
        """

        return self._nominal_voltage

    @nominal_voltage_kv.setter
    def nominal_voltage_kv(
        self,
        value: float,
    ) -> None:
        self._nominal_voltage = (
            self._validate_nominal_voltage(
                value
            )
        )

    # =================================================================
    # INITIAL VOLTAGE CONDITIONS
    # =================================================================

    @property
    def initial_voltage_magnitude(self) -> float:
        """
        Return the configured initial voltage magnitude in per-unit.

        This is an initial-condition value, not a solved numerical
        result.
        """

        return self._initial_voltage_magnitude

    @initial_voltage_magnitude.setter
    def initial_voltage_magnitude(
        self,
        value: float,
    ) -> None:
        self._initial_voltage_magnitude = (
            self._validate_voltage_magnitude(
                value,
                "initial_voltage_magnitude",
            )
        )

    @property
    def initial_voltage_angle(self) -> float:
        """
        Return the configured initial voltage angle in degrees.

        This is an initial-condition value, not a solved numerical
        result.
        """

        return self._initial_voltage_angle

    @initial_voltage_angle.setter
    def initial_voltage_angle(
        self,
        value: float,
    ) -> None:
        self._initial_voltage_angle = (
            self._validate_voltage_angle(
                value,
                "initial_voltage_angle",
            )
        )

    def set_initial_voltage(
        self,
        magnitude: float,
        angle: float,
    ) -> None:
        """
        Set the initial voltage condition.

        Parameters
        ----------
        magnitude:
            Initial voltage magnitude in per-unit.

        angle:
            Initial voltage angle in degrees.
        """

        self.initial_voltage_magnitude = magnitude
        self.initial_voltage_angle = angle

    # =================================================================
    # TERMINAL
    # =================================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative Bus Terminal.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return the Bus terminal collection.

        A Bus currently has exactly one authoritative electrical
        Terminal.
        """

        return (self._terminal,)

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return whether the Bus Terminal has an endpoint.

        This is a local terminal-connectivity diagnostic.

        It does not determine Network or Study validity.
        """

        return self._terminal.is_connected

    @property
    def endpoint(self) -> Any:
        """
        Return the Bus Terminal endpoint, if any.
        """

        return self._terminal.endpoint

    def connect_terminal(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the authoritative Bus Terminal to an endpoint.

        Terminal owns the local connection state.

        Network topology validation remains outside the Bus.
        """

        if endpoint is None:
            raise ValueError(
                "Bus terminal endpoint cannot be None."
            )

        self._terminal.connect(endpoint)

    def disconnect_terminal(
        self,
    ) -> None:
        """
        Disconnect the authoritative Bus Terminal.

        A disconnected Bus remains a valid physical model object.
        """

        self._terminal.disconnect()

    # =================================================================
    # OPERATIONAL STATE
    # =================================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the Bus is in service.
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
        Return True when the Bus is out of service.
        """

        return not self._in_service

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set the Bus operational state.
        """

        self.in_service = value

    def close(self) -> None:
        """
        Place the Bus in service.
        """

        self._in_service = True

    def trip(self) -> None:
        """
        Remove the Bus from service.
        """

        self._in_service = False

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Bus-local parameters.

        Study formulation, Network topology, and numerical state
        are deliberately outside this validation boundary.
        """

        self._nominal_voltage = (
            self._validate_nominal_voltage(
                self._nominal_voltage
            )
        )

        self._initial_voltage_magnitude = (
            self._validate_voltage_magnitude(
                self._initial_voltage_magnitude,
                "initial_voltage_magnitude",
            )
        )

        self._initial_voltage_angle = (
            self._validate_voltage_angle(
                self._initial_voltage_angle,
                "initial_voltage_angle",
            )
        )

        self._in_service = self._validate_bool(
            self._in_service,
            "in_service",
        )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Bus model.

        ElectricalObject.validate() is responsible for invoking
        validate_parameters() through normal dynamic dispatch.
        """

        ElectricalObject.validate(self)

        if self._terminal is None:
            raise ValueError(
                f"Bus '{self.id}' must have a terminal."
            )

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                f"Bus '{self.id}' terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Bus '{self.id}' terminal ownership is invalid."
            )

        if self._terminal.role != "BUS":
            raise ValueError(
                f"Bus '{self.id}' terminal role must be 'BUS'."
            )

        return True

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Bus diagnostics.

        Only Bus-local model and initial-condition information is
        exposed.

        Study-specific and solved numerical state are excluded.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "nominal_voltage_kv": (
                self._nominal_voltage
            ),
            "initial_voltage_magnitude_pu": (
                self._initial_voltage_magnitude
            ),
            "initial_voltage_angle_deg": (
                self._initial_voltage_angle
            ),
            "terminal": self._terminal.role,
            "endpoint": (
                self._terminal.endpoint.id
                if self._terminal.endpoint is not None
                else None
            ),
            "connected": self.is_connected,
            "in_service": self._in_service,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Bus "
            f"id={self.id}, "
            f"name={self.name!r}, "
            f"nominal_voltage="
            f"{self._nominal_voltage:.6f} kV, "
            f"initial_voltage="
            f"{self._initial_voltage_magnitude:.6f} pu, "
            f"initial_angle="
            f"{self._initial_voltage_angle:.6f} deg, "
            f"in_service={self._in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_nominal_voltage(
        value: float,
    ) -> float:
        """
        Validate nominal bus voltage in kV.
        """

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "nominal_voltage_kv must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                "nominal_voltage_kv must be finite."
            )

        if value <= 0.0:
            raise ValueError(
                "nominal_voltage_kv must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_voltage_magnitude(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a voltage magnitude in per-unit.
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

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_voltage_angle(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a voltage angle in degrees.

        Any finite angle is accepted.

        Angle normalization is left to the numerical formulation
        because different numerical consumers may use different
        conventions.
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

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a strict boolean value.

        Arbitrary truthy/falsy values are deliberately rejected so
        values such as the string ``"False"`` cannot silently become
        True through bool coercion.
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
    "Bus",
]
