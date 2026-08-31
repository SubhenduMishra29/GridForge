# ============================================================
# File: core/model/fuse.py
# GridForge V2 — Fuse Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Fuse Model
=========================

A Fuse is a two-terminal protective switching element.

Architecture
------------

    ElectricalObject
           |
           v
          Fuse
        /      \
       v        v
    Terminal  Terminal
       |          |
       v          v
    endpoint   endpoint


Fuse intentionally does NOT inherit Branch.

A Fuse is not a generic electrical branch. Its primary domain
meaning is its protective state and current interruption behavior.

Terminal Contract
-----------------

Terminal is the sole authority for endpoint state.

Fuse owns:

    from_terminal
    to_terminal

Terminal owns:

    owner
    role
    endpoint
    connection state

Canonical endpoint mutation:

    Terminal.attach(endpoint)
    Terminal.detach()

Fuse does not maintain:

    _endpoint_from
    _endpoint_to
    from_bus
    to_bus

and does not provide a competing endpoint store.

Protection Boundary
-------------------

Fuse owns its local physical/protective state:

    - blown
    - in_service
    - rated current
    - rated voltage
    - interrupting rating

The Fuse model does NOT:

    - execute global protection coordination;
    - calculate network fault current;
    - construct Y-bus;
    - solve short circuit;
    - mutate Network topology;
    - operate relays;
    - issue application commands;
    - modify UI/SLD state.

Application / Protection / Network layers interpret the Fuse
state and perform controlled system-level mutation.

Switching Semantics
-------------------

A healthy fuse conducts when:

    in_service and not blown

A blown fuse is considered non-conductive.

The model stores this state only. Network topology interpretation
belongs to the Network/Application layers.

Validation
----------

Construction establishes local object state.

Validation is performed through the inherited ElectricalObject
validation contract.

Fuse-specific validation is implemented through
validate_parameters().

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Fuse(ElectricalObject):
    """
    Two-terminal protective fuse.

    Fuse is a protective switching element and therefore does not
    inherit Branch.
    """

    TYPE = "FUSE"

    __slots__ = (
        "_terminal_from",
        "_terminal_to",
        "_in_service",
        "_blown",
        "_rated_current_a",
        "_rated_voltage_v",
        "_interrupting_rating_ka",
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
        blown: bool = False,
        rated_current_a: float | None = None,
        rated_voltage_v: float | None = None,
        interrupting_rating_ka: float | None = None,
    ) -> None:
        """
        Construct a Fuse.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional initial endpoint for the FROM terminal.

        endpoint_to:
            Optional initial endpoint for the TO terminal.

        name:
            Human-readable fuse name.

        in_service:
            Whether the fuse is operationally in service.

        blown:
            Initial fuse condition.

        rated_current_a:
            Continuous current rating in amperes.

        rated_voltage_v:
            Voltage rating in volts.

        interrupting_rating_ka:
            Interrupting rating in kiloamperes.

        Notes
        -----
        Endpoint references are attached through Terminal.attach().
        They are never independently stored by Fuse.
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
        # Fuse state
        # --------------------------------------------------------

        self._in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        self._blown = self._validate_bool(
            blown,
            "blown",
        )

        # --------------------------------------------------------
        # Ratings
        # --------------------------------------------------------

        self._rated_current_a = (
            self._validate_optional_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

        self._rated_voltage_v = (
            self._validate_optional_positive(
                rated_voltage_v,
                "rated_voltage_v",
            )
        )

        self._interrupting_rating_ka = (
            self._validate_optional_positive(
                interrupting_rating_ka,
                "interrupting_rating_ka",
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

        This property is read-only delegation to Terminal.
        """
        return self._terminal_from.endpoint

    @property
    def to_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the TO terminal.

        This property is read-only delegation to Terminal.
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
        Return True when both terminals have endpoints.
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
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the fuse is in service.
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
    # FUSE CONDITION
    # ============================================================

    @property
    def blown(self) -> bool:
        """
        Return True when the fuse is blown.
        """
        return self._blown

    @blown.setter
    def blown(
        self,
        value: bool,
    ) -> None:
        self._blown = self._validate_bool(
            value,
            "blown",
        )

    @property
    def is_blown(self) -> bool:
        """
        Return True when the fuse is blown.
        """
        return self._blown

    @property
    def is_intact(self) -> bool:
        """
        Return True when the fuse is not blown.
        """
        return not self._blown

    @property
    def conducts(self) -> bool:
        """
        Return whether the fuse is presently conductive.

        A fuse conducts when it is both:

            in_service
            and
            not blown

        Network topology remains outside the Fuse model.
        """
        return (
            self._in_service
            and not self._blown
        )

    # ============================================================
    # FUSE OPERATIONS
    # ============================================================

    def blow(self) -> None:
        """
        Mark the fuse as blown.

        This changes only local Fuse state.

        Protection/Application layers are responsible for deciding
        when the fuse should blow.
        """
        self._blown = True

    def reset(self) -> None:
        """
        Reset the fuse to an intact state.

        This represents replacement/reset of the local fuse state.

        Whether such an operation is permissible in a particular
        engineering workflow belongs to the Application layer.
        """
        self._blown = False

    # ============================================================
    # RATINGS
    # ============================================================

    @property
    def rated_current_a(self) -> float | None:
        """
        Return continuous current rating in amperes.
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

    @property
    def rated_voltage_v(self) -> float | None:
        """
        Return voltage rating in volts.
        """
        return self._rated_voltage_v

    @rated_voltage_v.setter
    def rated_voltage_v(
        self,
        value: float | None,
    ) -> None:
        self._rated_voltage_v = (
            self._validate_optional_positive(
                value,
                "rated_voltage_v",
            )
        )

    @property
    def interrupting_rating_ka(self) -> float | None:
        """
        Return interrupting rating in kiloamperes.
        """
        return self._interrupting_rating_ka

    @interrupting_rating_ka.setter
    def interrupting_rating_ka(
        self,
        value: float | None,
    ) -> None:
        self._interrupting_rating_ka = (
            self._validate_optional_positive(
                value,
                "interrupting_rating_ka",
            )
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Fuse-specific parameters.

        The inherited ElectricalObject validation contract is
        executed first.
        """

        super().validate_parameters()

        self._in_service = self._validate_bool(
            self._in_service,
            "in_service",
        )

        self._blown = self._validate_bool(
            self._blown,
            "blown",
        )

        self._rated_current_a = (
            self._validate_optional_positive(
                self._rated_current_a,
                "rated_current_a",
            )
        )

        self._rated_voltage_v = (
            self._validate_optional_positive(
                self._rated_voltage_v,
                "rated_voltage_v",
            )
        )

        self._interrupting_rating_ka = (
            self._validate_optional_positive(
                self._interrupting_rating_ka,
                "interrupting_rating_ka",
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
        Return structured Fuse diagnostics.

        Endpoint information is obtained from Terminal.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "in_service": self._in_service,
                "blown": self._blown,
                "conducts": self.conducts,
                "rated_current_a": self._rated_current_a,
                "rated_voltage_v": self._rated_voltage_v,
                "interrupting_rating_ka": (
                    self._interrupting_rating_ka
                ),
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
            "blown"
            if self._blown
            else "intact"
        )

        return (
            f"<Fuse "
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
    "Fuse",
]
