# ============================================================
# File: core/model/breaker.py
# GridForge V2 — Breaker Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Breaker Model
============================

A Breaker is a two-terminal switching device.

Architecture
------------

    ElectricalObject
           |
           v
        Breaker
        /     \
       v       v
    Terminal  Terminal
       |         |
       v         v
    endpoint   endpoint
       |         |
       +---- Network ----+
               |
            Topology


Inheritance
-----------

Breaker intentionally does NOT inherit Branch.

Branch represents a generic electrical branch with canonical
electrical parameters:

    r
    x
    b

A Breaker is a switching/topological element. Its primary
electrical meaning is its switching state rather than a generic
series impedance model.

Ownership
---------

Breaker owns:

    - two authoritative Terminal objects;
    - closed/open state;
    - failed state;
    - in-service state;
    - breaker-specific ratings.

Terminal owns:

    - endpoint reference;
    - connection state;
    - terminal role;
    - terminal owner.

Breaker does NOT duplicate Terminal endpoint state.

Canonical endpoint access is:

    breaker.from_terminal.endpoint
    breaker.to_terminal.endpoint

or through the Breaker convenience accessors:

    breaker.from_endpoint
    breaker.to_endpoint

Those convenience accessors delegate directly to Terminal.

Terminal mutation
-----------------

The canonical endpoint mutation APIs are:

    breaker.from_terminal.attach(endpoint)
    breaker.from_terminal.detach()

    breaker.to_terminal.attach(endpoint)
    breaker.to_terminal.detach()

Breaker convenience methods may delegate to those APIs, but
Breaker must never maintain a second endpoint store.

Network boundary
----------------

Breaker does NOT:

    - own Bus objects;
    - resolve endpoints into Buses;
    - mutate Network topology;
    - maintain Network collections;
    - construct Y-bus matrices;
    - assign solver indices;
    - perform numerical calculations;
    - execute protection logic;
    - execute control logic;
    - maintain UI/SLD state;
    - perform persistence.

The Network/Application layers interpret switching state and
terminal endpoints when constructing authoritative topology.

Validation
----------

The public validation entry point is inherited from
ElectricalObject.

Breaker overrides validate_parameters() only for its local
parameters and calls the base validation contract.

Construction does not call validate().

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Breaker(ElectricalObject):
    """
    Two-terminal switching device.

    Breaker is a topology/switching model element rather than a
    generic electrical Branch.

    Endpoint ownership is delegated completely to the two
    authoritative Terminal instances.
    """

    TYPE = "BREAKER"

    __slots__ = (
        "_terminal_from",
        "_terminal_to",
        "_in_service",
        "_closed",
        "_failed",
        "_voltage_kv",
        "_current_a",
        "_interrupting_ka",
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
        in_service: bool = True,
        closed: bool = True,
        failed: bool = False,
        voltage_kv: float | None = None,
        current_a: float | None = None,
        interrupting_ka: float | None = None,
    ) -> None:
        """
        Construct a two-terminal Breaker.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional initial endpoint for the FROM terminal.

        endpoint_to:
            Optional initial endpoint for the TO terminal.

            These are attached through Terminal.attach(). They are
            not stored independently by Breaker.

        name:
            Human-readable breaker name.

        in_service:
            Whether the breaker is operationally in service.

        closed:
            Initial switching state.

        failed:
            Whether the breaker is failed.

        voltage_kv:
            Optional breaker voltage rating.

        current_a:
            Optional continuous-current rating.

        interrupting_ka:
            Optional interrupting-current rating.

        Notes
        -----
        Construction establishes local model state.

        Validation is deliberately deferred until the complete
        object has been constructed.
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
        # Endpoint attachment
        # --------------------------------------------------------
        #
        # Terminal is the sole owner of endpoint state.
        # Never assign endpoint references directly to Breaker.
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

        self._in_service = bool(
            in_service
        )

        self._closed = bool(
            closed
        )

        self._failed = bool(
            failed
        )

        # --------------------------------------------------------
        # Ratings
        # --------------------------------------------------------

        self._voltage_kv = (
            self._normalize_optional_positive(
                voltage_kv,
                "voltage_kv",
            )
        )

        self._current_a = (
            self._normalize_optional_positive(
                current_a,
                "current_a",
            )
        )

        self._interrupting_ka = (
            self._normalize_optional_positive(
                interrupting_ka,
                "interrupting_ka",
            )
        )

    # ============================================================
    # TYPE
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge model type.
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
        Return the authoritative Breaker terminals.

        The order is:

            (from_terminal, to_terminal)
        """
        return (
            self._terminal_from,
            self._terminal_to,
        )

    # ============================================================
    # ENDPOINTS
    # ============================================================

    @property
    def from_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the FROM terminal.

        This is a read-only delegation property.

        Endpoint mutation must occur through:

            from_terminal.attach()
            from_terminal.detach()
        """
        return self._terminal_from.endpoint

    @property
    def to_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the TO terminal.

        This is a read-only delegation property.

        Endpoint mutation must occur through:

            to_terminal.attach()
            to_terminal.detach()
        """
        return self._terminal_to.endpoint

    @property
    def endpoint_from(self) -> Any | None:
        """
        Return the FROM terminal endpoint.

        Compatibility naming only; endpoint state remains owned
        by Terminal.
        """
        return self._terminal_from.endpoint

    @property
    def endpoint_to(self) -> Any | None:
        """
        Return the TO terminal endpoint.

        Compatibility naming only; endpoint state remains owned
        by Terminal.
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

        Delegates to Terminal.detach().
        """
        self._terminal_from.detach()

    def disconnect_to(self) -> None:
        """
        Detach the TO terminal endpoint.

        Delegates to Terminal.detach().
        """
        self._terminal_to.detach()

    # ============================================================
    # CONNECTION STATE
    # ============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both Breaker terminals are connected.
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
    # OPERATIONAL STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the Breaker is in service.
        """
        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = bool(value)

    @property
    def closed(self) -> bool:
        """
        Return True when the Breaker is closed.
        """
        return self._closed

    @closed.setter
    def closed(
        self,
        value: bool,
    ) -> None:
        self._closed = bool(value)

    @property
    def is_closed(self) -> bool:
        """
        Return True when the Breaker is closed.
        """
        return self._closed

    @property
    def is_open(self) -> bool:
        """
        Return True when the Breaker is open.
        """
        return not self._closed

    @property
    def failed(self) -> bool:
        """
        Return True when the Breaker is failed.
        """
        return self._failed

    @failed.setter
    def failed(
        self,
        value: bool,
    ) -> None:
        self._failed = bool(value)

    # ============================================================
    # SWITCHING OPERATIONS
    # ============================================================

    def open(self) -> None:
        """
        Open the Breaker.

        Only local Breaker state is changed.

        Network topology interpretation is outside this model.
        """
        self._closed = False

    def close(self) -> None:
        """
        Close the Breaker.

        Only local Breaker state is changed.

        Network topology interpretation is outside this model.
        """
        self._closed = True

    def trip(self) -> None:
        """
        Trip the Breaker open.

        Protection/control systems are responsible for deciding
        when a trip should occur. This method represents only the
        resulting local switching state.
        """
        self._closed = False

    # ============================================================
    # RATINGS
    # ============================================================

    @property
    def voltage_kv(self) -> float | None:
        """
        Return the voltage rating in kV.
        """
        return self._voltage_kv

    @voltage_kv.setter
    def voltage_kv(
        self,
        value: float | None,
    ) -> None:
        self._voltage_kv = (
            self._normalize_optional_positive(
                value,
                "voltage_kv",
            )
        )

    @property
    def current_a(self) -> float | None:
        """
        Return the continuous-current rating in amperes.
        """
        return self._current_a

    @current_a.setter
    def current_a(
        self,
        value: float | None,
    ) -> None:
        self._current_a = (
            self._normalize_optional_positive(
                value,
                "current_a",
            )
        )

    @property
    def interrupting_ka(self) -> float | None:
        """
        Return the interrupting-current rating in kA.
        """
        return self._interrupting_ka

    @interrupting_ka.setter
    def interrupting_ka(
        self,
        value: float | None,
    ) -> None:
        self._interrupting_ka = (
            self._normalize_optional_positive(
                value,
                "interrupting_ka",
            )
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Breaker-specific parameters.

        Validation hierarchy:

            Breaker.validate_parameters()
                    |
                    v
            ElectricalObject.validate_parameters()
        """

        super().validate_parameters()

        # --------------------------------------------------------
        # Terminal validation
        # --------------------------------------------------------

        self._terminal_from.validate()
        self._terminal_to.validate()

        # --------------------------------------------------------
        # Boolean state
        # --------------------------------------------------------

        if not isinstance(
            self._in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be a boolean."
            )

        if not isinstance(
            self._closed,
            bool,
        ):
            raise TypeError(
                "closed must be a boolean."
            )

        if not isinstance(
            self._failed,
            bool,
        ):
            raise TypeError(
                "failed must be a boolean."
            )

        # --------------------------------------------------------
        # Ratings
        # --------------------------------------------------------

        self._voltage_kv = (
            self._normalize_optional_positive(
                self._voltage_kv,
                "voltage_kv",
            )
        )

        self._current_a = (
            self._normalize_optional_positive(
                self._current_a,
                "current_a",
            )
        )

        self._interrupting_ka = (
            self._normalize_optional_positive(
                self._interrupting_ka,
                "interrupting_ka",
            )
        )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Breaker diagnostics.

        Endpoint information is obtained from Terminal and is not
        stored independently by Breaker.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "closed": self._closed,
                "in_service": self._in_service,
                "failed": self._failed,
                "voltage_kv": self._voltage_kv,
                "current_a": self._current_a,
                "interrupting_ka": self._interrupting_ka,
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
            f"<Breaker "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"state={state}>"
        )

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _normalize_optional_positive(
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Normalize an optional positive finite numeric value.

        None is permitted because breaker ratings may be unspecified
        during early model construction.
        """

        if value is None:
            return None

        try:
            normalized = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric or None."
            ) from exc

        if not math.isfinite(normalized):
            raise ValueError(
                f"{name} must be finite."
            )

        if normalized <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return normalized

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
    "Breaker",
]
