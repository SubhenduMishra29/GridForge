# core/model/disconnector.py
"""
GridForge V2 Disconnector Model
===============================

Author:
    Subhendu Mishra

A Disconnector is a physical two-terminal switchgear element used
primarily for electrical isolation.

Architecture
------------

    ElectricalObject
          |
     Disconnector
        /     \
   Terminal  Terminal

The Disconnector owns:

    - two authoritative Terminal objects
    - voltage rating
    - continuous current rating
    - mechanical operating time
    - physical open/closed state
    - equipment service state

The Disconnector does NOT own:

    - global network topology
    - network graph mutation
    - Y-bus construction
    - load-flow calculations
    - short-circuit calculations
    - protection logic
    - simulation event history
    - SLD geometry
    - GUI state

Local state
-----------

    conducts = closed and in_service

This is only a local equipment-state interpretation.

The network/topology layer is responsible for deriving electrical
connectivity from the equipment state.

A Disconnector differs from a Circuit Breaker:

    Disconnector:
        - isolation device
        - normally operated without interrupting fault current
        - no protection-clearing responsibility

    Circuit Breaker:
        - switching/interruption device
        - capable of interrupting current within ratings
        - participates in protection clearing

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Disconnector(ElectricalObject):
    """
    Physical two-terminal electrical disconnector / isolator.
    """

    TYPE = "DISCONNECTOR"

    def __init__(
        self,
        id: str,
        voltage_kv: float,
        rated_current_a: float,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        operating_time: float = 1.0,
        closed: bool = True,
        in_service: bool = True,
        name: str = "",
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # AUTHORITATIVE LOCAL TERMINALS
        # -------------------------------------------------------------

        self.from_terminal = Terminal(
            endpoint=endpoint_from,
            owner=self,
        )

        self.to_terminal = Terminal(
            endpoint=endpoint_to,
            owner=self,
        )

        # -------------------------------------------------------------
        # EQUIPMENT PARAMETERS
        # -------------------------------------------------------------

        self.voltage_kv = self._validate_positive(
            voltage_kv,
            "voltage_kv",
        )

        self.rated_current_a = self._validate_positive(
            rated_current_a,
            "rated_current_a",
        )

        self.operating_time = self._validate_non_negative(
            operating_time,
            "operating_time",
        )

        # -------------------------------------------------------------
        # AUTHORITATIVE PHYSICAL STATE
        # -------------------------------------------------------------

        self.closed = bool(closed)
        self.in_service = bool(in_service)

        # -------------------------------------------------------------
        # USE THE COMMON MODEL VALIDATION CONTRACT
        # -------------------------------------------------------------

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
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the two authoritative physical terminals.
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self) -> Any:
        """
        Return the from-side terminal endpoint.

        This is derived from Terminal state and is not independently
        stored by the Disconnector.
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self) -> Any:
        """
        Return the to-side terminal endpoint.

        This is derived from Terminal state and is not independently
        stored by the Disconnector.
        """

        return self.to_terminal.endpoint

    def endpoints(
        self,
    ) -> tuple[Any | None, Any | None]:
        """
        Return the local endpoint pair.
        """

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # =================================================================
    # LOCAL TERMINAL CONNECTION
    # =================================================================

    def connect_from(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the from-side terminal locally.

        This does not mutate global network topology.
        """

        if endpoint is None:
            raise ValueError(
                f"Disconnector '{self.id}' from endpoint "
                "cannot be None."
            )

        self.from_terminal.connect(endpoint)

    def connect_to(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the to-side terminal locally.

        This does not mutate global network topology.
        """

        if endpoint is None:
            raise ValueError(
                f"Disconnector '{self.id}' to endpoint "
                "cannot be None."
            )

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
    # LOCAL CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both local terminals are connected.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    @property
    def has_from_endpoint(self) -> bool:
        """Return whether the from terminal has an endpoint."""

        return self.from_terminal.is_connected

    @property
    def has_to_endpoint(self) -> bool:
        """Return whether the to terminal has an endpoint."""

        return self.to_terminal.is_connected

    # =================================================================
    # PHYSICAL SWITCHING STATE
    # =================================================================

    @property
    def is_closed(self) -> bool:
        """Return True when physically closed."""

        return self.closed

    @property
    def is_open(self) -> bool:
        """Return True when physically open."""

        return not self.closed

    def open(self) -> None:
        """
        Open the disconnector.

        Only local physical state changes.
        """

        self.closed = False

    def close(self) -> None:
        """
        Close the disconnector.

        Only local physical state changes.
        """

        self.closed = True

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return True when equipment is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return True when equipment is out of service."""

        return not self.in_service

    def put_in_service(self) -> None:
        """Place the disconnector in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Remove the disconnector from service."""

        self.in_service = False

    # =================================================================
    # CONDUCTING STATE
    # =================================================================

    @property
    def conducts(self) -> bool:
        """
        Return the local conducting state.

        A disconnector conducts only when:

            closed == True
            in_service == True

        This property does not mutate or query the global network
        topology.
        """

        return (
            self.closed
            and self.in_service
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate disconnector-local parameters.

        This satisfies the common ElectricalObject validation
        contract.

        Network-level compatibility and topology are deliberately
        excluded.
        """

        self.voltage_kv = self._validate_positive(
            self.voltage_kv,
            "voltage_kv",
        )

        self.rated_current_a = self._validate_positive(
            self.rated_current_a,
            "rated_current_a",
        )

        self.operating_time = self._validate_non_negative(
            self.operating_time,
            "operating_time",
        )

        if not isinstance(
            self.closed,
            bool,
        ):
            raise ValueError(
                f"Disconnector '{self.id}' closed state "
                "must be boolean."
            )

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise ValueError(
                f"Disconnector '{self.id}' in_service state "
                "must be boolean."
            )

        if self.from_terminal.owner is not self:
            raise ValueError(
                f"Disconnector '{self.id}' from terminal "
                "ownership is invalid."
            )

        if self.to_terminal.owner is not self:
            raise ValueError(
                f"Disconnector '{self.id}' to terminal "
                "ownership is invalid."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Disconnector model.

        Topological connectivity is not required for model validity.
        """

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured disconnector diagnostics.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "from_terminal": self.from_terminal.id,
            "to_terminal": self.to_terminal.id,

            "from_endpoint": (
                self.from_terminal.endpoint_id
                if self.from_terminal.is_connected
                else None
            ),

            "to_endpoint": (
                self.to_terminal.endpoint_id
                if self.to_terminal.is_connected
                else None
            ),

            "from_connected":
                self.from_terminal.is_connected,

            "to_connected":
                self.to_terminal.is_connected,

            "is_connected":
                self.is_connected,

            "voltage_kv":
                self.voltage_kv,

            "rated_current_a":
                self.rated_current_a,

            "operating_time":
                self.operating_time,

            "closed":
                self.closed,

            "open":
                self.is_open,

            "in_service":
                self.in_service,

            "conducts":
                self.conducts,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        from_id = (
            self.from_terminal.endpoint_id
            if self.from_terminal.is_connected
            else None
        )

        to_id = (
            self.to_terminal.endpoint_id
            if self.to_terminal.is_connected
            else None
        )

        return (
            f"<Disconnector "
            f"id={self.id}, "
            f"from={from_id}, "
            f"to={to_id}, "
            f"voltage={self.voltage_kv:.3f} kV, "
            f"rated={self.rated_current_a:.2f} A, "
            f"closed={self.closed}, "
            f"in_service={self.in_service}, "
            f"conducts={self.conducts}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """
        Convert to float and require a finite value.
        """

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Convert to float and require value > 0.
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

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Convert to float and require value >= 0.
        """

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value


__all__ = [
    "Disconnector",
]
