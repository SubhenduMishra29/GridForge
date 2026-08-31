# ============================================================
# File: core/model/switch.py
# GridForge V2 — Generic Switch Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Generic Switch Model
===================================

Canonical two-terminal switching element.

Architecture
------------

    ElectricalObject
           |
           v
        Switch
        /     \
       v       v
 FROM Terminal  TO Terminal
       |             |
       v             v
    endpoint       endpoint


Switch is a Core domain object.

It owns:

    - persistent identity;
    - two authoritative terminals;
    - open/closed state;
    - service state;
    - normal operating-state metadata;
    - basic electrical ratings.

It does NOT own:

    - Bus objects;
    - Network topology;
    - graph state;
    - connection routing;
    - SLD geometry;
    - rendering;
    - numerical admittance/impedance representation;
    - power-flow solving;
    - short-circuit solving;
    - protection logic;
    - relay coordination;
    - GUI state.

Terminal contract
-----------------

Terminal is the authoritative owner of endpoint state.

Switch therefore owns:

    from_terminal
    to_terminal

while each Terminal owns:

    owner
    role
    endpoint
    connection state

Endpoint mutation is performed through:

    terminal.attach(endpoint)
    terminal.detach()

Switch provides no competing endpoint storage.

The Network/Application layers interpret terminal endpoints and
switching state when constructing authoritative network topology.

Numerical representation
------------------------

The Core model deliberately does not represent:

    open   -> infinite impedance
    closed -> infinite admittance

Those are numerical concerns belonging to Network/Solver layers.

Validation
----------

Construction establishes the complete object.

Validation is performed through validate() after construction,
rather than relying on partially initialized state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Switch(ElectricalObject):
    """
    Generic two-terminal electrical switch.

    Switch is a switching/topological element and therefore does
    not inherit Branch.
    """

    TYPE = "SWITCH"

    __slots__ = (
        "_terminal_from",
        "_terminal_to",
        "_closed",
        "_in_service",
        "_normally_closed",
        "_rated_voltage_kv",
        "_rated_current_a",
    )

    # ============================================================
    # CONSTRUCTION
    # ============================================================

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        closed: bool = False,
        in_service: bool = True,
        normally_closed: bool | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
    ) -> None:
        """
        Construct a two-terminal Switch.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable switch name.

        endpoint_from:
            Optional initial endpoint for the FROM terminal.

        endpoint_to:
            Optional initial endpoint for the TO terminal.

        closed:
            Initial switching state.

        in_service:
            Whether the switch is available for network operation.

        normally_closed:
            Configured normal operating state. If omitted, the
            initial closed state is used.

        rated_voltage_kv:
            Optional voltage rating in kV.

        rated_current_a:
            Optional continuous-current rating in A.

        Notes
        -----
        Endpoint references are attached through Terminal.attach().
        They are never stored independently by Switch.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Authoritative terminals
        # --------------------------------------------------------

        self._terminal_from = Terminal(
            owner=self,
            role="from",
        )

        self._terminal_to = Terminal(
            owner=self,
            role="to",
        )

        # --------------------------------------------------------
        # Initial endpoint attachment
        # --------------------------------------------------------

        if endpoint_from is not None:
            self._terminal_from.attach(
                endpoint_from
            )

        if endpoint_to is not None:
            self._terminal_to.attach(
                endpoint_to
            )

        # --------------------------------------------------------
        # Switching state
        # --------------------------------------------------------

        self._closed = self._validate_bool(
            closed,
            "closed",
        )

        self._in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        if normally_closed is None:
            normally_closed = self._closed

        self._normally_closed = self._validate_bool(
            normally_closed,
            "normally_closed",
        )

        # --------------------------------------------------------
        # Ratings
        # --------------------------------------------------------

        self._rated_voltage_kv = (
            self._validate_optional_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self._rated_current_a = (
            self._validate_optional_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return canonical GridForge element type.
        """
        return self.TYPE

    # ============================================================
    # TERMINALS
    # ============================================================

    @property
    def from_terminal(self) -> Terminal:
        """
        Return the authoritative FROM terminal.
        """
        return self._terminal_from

    @property
    def to_terminal(self) -> Terminal:
        """
        Return the authoritative TO terminal.
        """
        return self._terminal_to

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the authoritative terminals in FROM/TO order.
        """
        return (
            self._terminal_from,
            self._terminal_to,
        )

    # ============================================================
    # ENDPOINT ACCESS
    # ============================================================

    @property
    def from_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the FROM terminal.

        This property delegates to Terminal and does not maintain
        independent endpoint state.
        """
        return self._terminal_from.endpoint

    @property
    def to_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the TO terminal.

        This property delegates to Terminal and does not maintain
        independent endpoint state.
        """
        return self._terminal_to.endpoint

    # ============================================================
    # ENDPOINT CONNECTION
    # ============================================================

    def connect_from(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to the FROM terminal.

        Delegates to the canonical Terminal.attach() API.
        """
        self._terminal_from.attach(
            endpoint
        )

    def connect_to(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to the TO terminal.

        Delegates to the canonical Terminal.attach() API.
        """
        self._terminal_to.attach(
            endpoint
        )

    def disconnect_from(self) -> None:
        """
        Detach the FROM terminal endpoint.
        """
        self._terminal_from.detach()

    def disconnect_to(self) -> None:
        """
        Detach the TO terminal endpoint.
        """
        self._terminal_to.detach()

    # ============================================================
    # CONNECTION STATE
    # ============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both terminals are connected.
        """
        return (
            self._terminal_from.is_connected
            and self._terminal_to.is_connected
        )

    @property
    def is_partially_connected(self) -> bool:
        """
        Return True when exactly one terminal is connected.
        """
        return (
            self._terminal_from.is_connected
            != self._terminal_to.is_connected
        )

    # ============================================================
    # SWITCHING STATE
    # ============================================================

    @property
    def closed(self) -> bool:
        """
        Return True when the switch is closed.
        """
        return self._closed

    @closed.setter
    def closed(
        self,
        value: bool,
    ) -> None:
        self._closed = self._validate_bool(
            value,
            "closed",
        )

    @property
    def open(self) -> bool:
        """
        Return True when the switch is open.
        """
        return not self._closed

    @property
    def is_closed(self) -> bool:
        """
        Return True when the switch is closed.
        """
        return self._closed

    @property
    def is_open(self) -> bool:
        """
        Return True when the switch is open.
        """
        return not self._closed

    def close(self) -> None:
        """
        Close the switch.

        Only local switching state is changed.

        Network topology interpretation belongs outside this
        model.
        """
        self._closed = True

    def open_switch(self) -> None:
        """
        Open the switch.

        Named open_switch() to avoid collision with the boolean
        open property.
        """
        self._closed = False

    def trip(self) -> None:
        """
        Open the switch as the result of a trip command.

        The decision to trip belongs to an Application, protection,
        or control layer. This method only changes local state.
        """
        self._closed = False

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the switch is in service.
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

    # ============================================================
    # NORMAL OPERATING STATE
    # ============================================================

    @property
    def normally_closed(self) -> bool:
        """
        Return configured normal operating state.
        """
        return self._normally_closed

    @normally_closed.setter
    def normally_closed(
        self,
        value: bool,
    ) -> None:
        self._normally_closed = self._validate_bool(
            value,
            "normally_closed",
        )

    # ============================================================
    # ELECTRICAL RATINGS
    # ============================================================

    @property
    def rated_voltage_kv(self) -> float | None:
        """
        Return voltage rating in kV.
        """
        return self._rated_voltage_kv

    @rated_voltage_kv.setter
    def rated_voltage_kv(
        self,
        value: float | None,
    ) -> None:
        self._rated_voltage_kv = (
            self._validate_optional_positive(
                value,
                "rated_voltage_kv",
            )
        )

    @property
    def rated_current_a(self) -> float | None:
        """
        Return continuous current rating in A.
        """
        return self._rated_current_a

    @rated_current_a.setter
    def rated_current_a(
        self,
        value: float | None,
    ) -> None:
        self._rated_current_a = (
            self._validate_optional_positive(
                value,
                "rated_current_a",
            )
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Switch-specific parameters and terminals.

        The inherited ElectricalObject validation contract is
        executed first.
        """

        super().validate_parameters()

        self._closed = self._validate_bool(
            self._closed,
            "closed",
        )

        self._in_service = self._validate_bool(
            self._in_service,
            "in_service",
        )

        self._normally_closed = self._validate_bool(
            self._normally_closed,
            "normally_closed",
        )

        self._rated_voltage_kv = (
            self._validate_optional_positive(
                self._rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self._rated_current_a = (
            self._validate_optional_positive(
                self._rated_current_a,
                "rated_current_a",
            )
        )

        self._terminal_from.validate()
        self._terminal_to.validate()

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Switch diagnostics.

        Endpoint information is read from Terminal and is not
        independently stored by Switch.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "closed": self._closed,
                "in_service": self._in_service,
                "normally_closed": self._normally_closed,
                "rated_voltage_kv": self._rated_voltage_kv,
                "rated_current_a": self._rated_current_a,
                "from_endpoint": self._endpoint_identifier(
                    self._terminal_from.endpoint
                ),
                "to_endpoint": self._endpoint_identifier(
                    self._terminal_to.endpoint
                ),
            }
        )

        return summary

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_id = self._endpoint_identifier(
            self._terminal_from.endpoint
        )

        to_id = self._endpoint_identifier(
            self._terminal_to.endpoint
        )

        state = (
            "closed"
            if self._closed
            else "open"
        )

        return (
            f"<Switch "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"state={state}, "
            f"in_service={self._in_service}>"
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a strict boolean value.

        bool is deliberately required rather than accepting arbitrary
        truthy/falsy values.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be a boolean."
            )

        return value

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """
        Validate and normalize a finite numeric value.
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
    def _validate_optional_positive(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Validate an optional positive finite numeric value.
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
    def _endpoint_identifier(
        endpoint: Any | None,
    ) -> Any | None:
        """
        Return an endpoint identifier for diagnostics only.

        No topology resolution is performed.
        """

        if endpoint is None:
            return None

        return getattr(
            endpoint,
            "id",
            endpoint,
        )


__all__ = [
    "Switch",
]
