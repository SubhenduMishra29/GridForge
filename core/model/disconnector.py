# ============================================================
# File: core/model/disconnector.py
# GridForge V2 — Disconnector Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Disconnector Model
=================================

A Disconnector is a two-terminal switching/topological element
used primarily for isolation and visible network separation.

Architecture
------------

    ElectricalObject
           |
           v
      Disconnector
        /       \
       v         v
    Terminal   Terminal
       |           |
       v           v
    endpoint    endpoint


Disconnector intentionally does NOT inherit Branch.

Branch represents an electrical branch with impedance/admittance
parameters.

Disconnector represents a switching/topological element whose
primary state is:

    closed / open
    in_service

Electrical/network interpretation of the switching state belongs
to the Network/Application/Solver layers.

Terminal Contract
-----------------

Terminal is the sole authority for endpoint state.

Disconnector owns:

    from_terminal
    to_terminal

Terminal owns:

    owner
    role
    endpoint
    connection state

Endpoint mutation must use:

    Terminal.attach()
    Terminal.detach()

Disconnector does not maintain a second endpoint store.

Network Boundary
----------------

Disconnector does NOT:

    - own Bus objects;
    - maintain network topology;
    - resolve endpoints into buses;
    - modify Network collections;
    - construct solver matrices;
    - assign solver indices;
    - perform numerical studies;
    - execute protection logic;
    - execute control logic;
    - own SLD/canvas state;
    - own rendering state.

Validation
----------

Construction establishes object state.

Validation is performed after construction through the normal
ElectricalObject validation contract.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Disconnector(ElectricalObject):
    """
    Two-terminal electrical disconnector.

    The disconnector is a switching/topological element and does
    not inherit Branch.

    Endpoint authority belongs exclusively to Terminal.
    """

    TYPE = "DISCONNECTOR"

    __slots__ = (
        "_terminal_from",
        "_terminal_to",
        "_closed",
        "_in_service",
        "_normally_closed",
        "_voltage_kv",
        "_rated_current_a",
        "_operating_time",
    )

    # ============================================================
    # CONSTRUCTION
    # ============================================================

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        name: str = "",
        closed: bool = True,
        in_service: bool = True,
        normally_closed: bool | None = None,
        voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        operating_time: float | None = None,
    ) -> None:
        """
        Construct a Disconnector.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional initial endpoint for the FROM terminal.

        endpoint_to:
            Optional initial endpoint for the TO terminal.

        name:
            Human-readable disconnector name.

        closed:
            Initial switching state.

        in_service:
            Whether the disconnector is operationally in service.

        normally_closed:
            Configured normal state. If omitted, the initial
            closed state is used.

        voltage_kv:
            Optional voltage rating in kV.

        rated_current_a:
            Optional continuous-current rating in A.

        operating_time:
            Optional operating time in seconds.

        Notes
        -----
        Endpoint references are attached through Terminal.attach().
        They are never independently stored by Disconnector.
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

        self._voltage_kv = (
            self._validate_optional_positive(
                voltage_kv,
                "voltage_kv",
            )
        )

        self._rated_current_a = (
            self._validate_optional_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

        self._operating_time = (
            self._validate_optional_non_negative(
                operating_time,
                "operating_time",
            )
        )

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
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

        This is a read-only delegation property.
        """
        return self._terminal_from.endpoint

    @property
    def to_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the TO terminal.

        This is a read-only delegation property.
        """
        return self._terminal_to.endpoint

    # ============================================================
    # ENDPOINT MUTATION
    # ============================================================

    def connect_from(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to the FROM terminal.
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
        Return True when the disconnector is closed.
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
    def is_closed(self) -> bool:
        """
        Return True when the disconnector is closed.
        """
        return self._closed

    @property
    def is_open(self) -> bool:
        """
        Return True when the disconnector is open.
        """
        return not self._closed

    @property
    def conducts(self) -> bool:
        """
        Return whether the disconnector is presently conductive.

        A disconnector conducts only when:

            closed
            AND
            in_service

        This is a local state interpretation only. Network topology
        remains the responsibility of the Network/Application layer.
        """
        return (
            self._closed
            and self._in_service
        )

    def close(self) -> None:
        """
        Close the disconnector.
        """
        self._closed = True

    def open(self) -> None:
        """
        Open the disconnector.

        No Network topology is modified here.
        """
        self._closed = False

    def operate(self) -> None:
        """
        Perform the configured switching operation.

        For the Core model this represents the local state
        transition only.
        """
        self._closed = not self._closed

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the disconnector is in service.
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
    # NORMAL STATE
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
    # VOLTAGE RATING
    # ============================================================

    @property
    def voltage_kv(self) -> float | None:
        """
        Return voltage rating in kV.
        """
        return self._voltage_kv

    @voltage_kv.setter
    def voltage_kv(
        self,
        value: float | None,
    ) -> None:
        self._voltage_kv = (
            self._validate_optional_positive(
                value,
                "voltage_kv",
            )
        )

    # ============================================================
    # CURRENT RATING
    # ============================================================

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
    # OPERATING TIME
    # ============================================================

    @property
    def operating_time(self) -> float | None:
        """
        Return operating time in seconds.
        """
        return self._operating_time

    @operating_time.setter
    def operating_time(
        self,
        value: float | None,
    ) -> None:
        self._operating_time = (
            self._validate_optional_non_negative(
                value,
                "operating_time",
            )
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Disconnector-specific parameters.

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

        self._voltage_kv = (
            self._validate_optional_positive(
                self._voltage_kv,
                "voltage_kv",
            )
        )

        self._rated_current_a = (
            self._validate_optional_positive(
                self._rated_current_a,
                "rated_current_a",
            )
        )

        self._operating_time = (
            self._validate_optional_non_negative(
                self._operating_time,
                "operating_time",
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
        Return structured Disconnector diagnostics.

        Endpoint information is obtained directly from Terminal.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "closed": self._closed,
                "in_service": self._in_service,
                "normally_closed": self._normally_closed,
                "conducts": self.conducts,
                "voltage_kv": self._voltage_kv,
                "rated_current_a": self._rated_current_a,
                "operating_time": self._operating_time,
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
            f"<Disconnector "
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
        Validate a boolean value.
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

    @classmethod
    def _validate_optional_non_negative(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Validate an optional finite non-negative numeric value.
        """

        if value is None:
            return None

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} must be greater than or equal to zero."
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
    "Disconnector",
]
