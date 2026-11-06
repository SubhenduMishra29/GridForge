# ============================================================
# File: core/model/ct.py
# GridForge V2 — Current Transformer Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Current Transformer Model
========================================

Current Transformer (CT) domain model.

Architecture
------------

    ElectricalObject
           |
           v
    CurrentTransformer
       /   |   |   \
      P1  P2  S1  S2
      |   |   |   |
      v   v   v   v
    Terminal endpoints

A CurrentTransformer is a four-terminal electrical/instrumentation
element.

The four physical terminals are:

    P1  Primary terminal 1
    P2  Primary terminal 2
    S1  Secondary terminal 1
    S2  Secondary terminal 2

Terminal Contract
-----------------

Terminal is the authoritative owner of endpoint state.

CurrentTransformer owns the four Terminal objects.

Each Terminal owns:

    owner
    role
    endpoint
    connection state

Endpoint mutation must use:

    Terminal.attach(endpoint)
    Terminal.detach()

CurrentTransformer does not maintain duplicate endpoint state.

Domain Boundary
---------------

CurrentTransformer owns CT-specific physical/nameplate data:

    - primary rated current
    - secondary rated current
    - ratio
    - burden
    - accuracy class
    - frequency
    - polarity
    - service state

CurrentTransformer does NOT own:

    - Bus objects
    - Network topology
    - Y-bus construction
    - short-circuit calculations
    - relay logic
    - relay coordination
    - measurement channels
    - protection decisions
    - saturation simulation
    - UI/SLD state
    - rendering state

Those responsibilities belong to the appropriate Core/Application
services and analysis layers.

Polarity
--------

The CT polarity convention is represented explicitly by the
CTPolarity enumeration.

    P1_P2
        Primary current enters P1 and exits P2.

    P2_P1
        Reverse physical primary orientation.

This property describes the physical/model convention. It does
not perform a measurement calculation.

Validation
----------

ElectricalObject remains the authoritative object-validation
entry point.

CurrentTransformer specializes:

    validate_parameters()

It does not replace the inherited validate() contract.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class CTPolarity(str, Enum):
    """
    Physical polarity/orientation convention of a CT.

    P1_P2:
        Primary current enters P1 and exits P2.

    P2_P1:
        Primary current enters P2 and exits P1.
    """

    P1_P2 = "P1_P2"
    P2_P1 = "P2_P1"


class CurrentTransformer(ElectricalObject):
    """
    Four-terminal Current Transformer.

    Physical terminals:

        P1 — primary terminal 1
        P2 — primary terminal 2
        S1 — secondary terminal 1
        S2 — secondary terminal 2

    The terminals are authoritative endpoint containers.
    """

    TYPE = "CT"

    __slots__ = (
        "_p1_terminal",
        "_p2_terminal",
        "_s1_terminal",
        "_s2_terminal",
        "_primary_rated_current_a",
        "_secondary_rated_current_a",
        "_burden_va",
        "_accuracy_class",
        "_frequency_hz",
        "_polarity",
        "_in_service",
    )

    # ============================================================
    # CONSTRUCTION
    # ============================================================

    def __init__(
        self,
        id: str,
        *,
        name: str = "",
        primary_rated_current_a: float = 100.0,
        secondary_rated_current_a: float = 5.0,
        burden_va: float | None = None,
        accuracy_class: str | None = None,
        frequency_hz: float = 50.0,
        polarity: CTPolarity | str = CTPolarity.P1_P2,
        in_service: bool = True,
        p1_endpoint: Any = None,
        p2_endpoint: Any = None,
        s1_endpoint: Any = None,
        s2_endpoint: Any = None,
    ) -> None:
        """
        Construct a CurrentTransformer.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable CT name.

        primary_rated_current_a:
            Rated primary current in amperes.

        secondary_rated_current_a:
            Rated secondary current in amperes.

        burden_va:
            Rated secondary burden in VA.

        accuracy_class:
            CT accuracy class, for example "5P20", "10P10",
            "0.5", etc.

        frequency_hz:
            Rated operating frequency in Hz.

        polarity:
            CTPolarity value or corresponding string.

        in_service:
            Whether the CT is operationally in service.

        p1_endpoint:
            Optional endpoint attached to P1.

        p2_endpoint:
            Optional endpoint attached to P2.

        s1_endpoint:
            Optional endpoint attached to S1.

        s2_endpoint:
            Optional endpoint attached to S2.

        Notes
        -----
        Endpoint references are attached through Terminal.attach().
        No duplicate endpoint attributes are maintained by the CT.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Authoritative physical terminals
        # --------------------------------------------------------

        self._p1_terminal = Terminal(
            owner=self,
            role="P1",
        )

        self._p2_terminal = Terminal(
            owner=self,
            role="P2",
        )

        self._s1_terminal = Terminal(
            owner=self,
            role="S1",
        )

        self._s2_terminal = Terminal(
            owner=self,
            role="S2",
        )

        # --------------------------------------------------------
        # Initial endpoint attachment
        # --------------------------------------------------------

        if p1_endpoint is not None:
            self._p1_terminal.attach(
                p1_endpoint
            )

        if p2_endpoint is not None:
            self._p2_terminal.attach(
                p2_endpoint
            )

        if s1_endpoint is not None:
            self._s1_terminal.attach(
                s1_endpoint
            )

        if s2_endpoint is not None:
            self._s2_terminal.attach(
                s2_endpoint
            )

        # --------------------------------------------------------
        # CT nameplate data
        # --------------------------------------------------------

        self._primary_rated_current_a = (
            self._validate_positive(
                primary_rated_current_a,
                "primary_rated_current_a",
            )
        )

        self._secondary_rated_current_a = (
            self._validate_positive(
                secondary_rated_current_a,
                "secondary_rated_current_a",
            )
        )

        self._burden_va = (
            self._validate_optional_positive(
                burden_va,
                "burden_va",
            )
        )

        self._accuracy_class = (
            self._validate_accuracy_class(
                accuracy_class
            )
        )

        self._frequency_hz = (
            self._validate_positive(
                frequency_hz,
                "frequency_hz",
            )
        )

        self._polarity = (
            self._validate_polarity(
                polarity
            )
        )

        self._in_service = (
            self._validate_bool(
                in_service,
                "in_service",
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
    def p1_terminal(self) -> Terminal:
        """
        Return the authoritative P1 terminal.
        """
        return self._p1_terminal

    @property
    def p2_terminal(self) -> Terminal:
        """
        Return the authoritative P2 terminal.
        """
        return self._p2_terminal

    @property
    def s1_terminal(self) -> Terminal:
        """
        Return the authoritative S1 terminal.
        """
        return self._s1_terminal

    @property
    def s2_terminal(self) -> Terminal:
        """
        Return the authoritative S2 terminal.
        """
        return self._s2_terminal

    @property
    def primary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the primary P1/P2 terminals.
        """
        return (
            self._p1_terminal,
            self._p2_terminal,
        )

    @property
    def secondary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the secondary S1/S2 terminals.
        """
        return (
            self._s1_terminal,
            self._s2_terminal,
        )

    @property
    def terminals(
        self,
    ) -> tuple[Terminal, Terminal, Terminal, Terminal]:
        """
        Return all authoritative terminals in physical order:

            P1, P2, S1, S2
        """
        return (
            self._p1_terminal,
            self._p2_terminal,
            self._s1_terminal,
            self._s2_terminal,
        )

    # ============================================================
    # ENDPOINT ACCESS
    # ============================================================

    @property
    def p1_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by P1 Terminal.
        """
        return self._p1_terminal.endpoint

    @property
    def p2_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by P2 Terminal.
        """
        return self._p2_terminal.endpoint

    @property
    def s1_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by S1 Terminal.
        """
        return self._s1_terminal.endpoint

    @property
    def s2_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by S2 Terminal.
        """
        return self._s2_terminal.endpoint

    # ============================================================
    # ENDPOINT MUTATION
    # ============================================================

    def connect_p1(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to P1.
        """
        self._p1_terminal.attach(
            endpoint
        )

    def connect_p2(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to P2.
        """
        self._p2_terminal.attach(
            endpoint
        )

    def connect_s1(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to S1.
        """
        self._s1_terminal.attach(
            endpoint
        )

    def connect_s2(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to S2.
        """
        self._s2_terminal.attach(
            endpoint
        )

    def disconnect_p1(self) -> None:
        """
        Detach P1.
        """
        self._p1_terminal.detach()

    def disconnect_p2(self) -> None:
        """
        Detach P2.
        """
        self._p2_terminal.detach()

    def disconnect_s1(self) -> None:
        """
        Detach S1.
        """
        self._s1_terminal.detach()

    def disconnect_s2(self) -> None:
        """
        Detach S2.
        """
        self._s2_terminal.detach()

    # ============================================================
    # CONNECTION STATE
    # ============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when all four CT terminals are connected.
        """
        return all(
            terminal.is_connected
            for terminal in self.terminals
        )

    @property
    def is_partially_connected(self) -> bool:
        """
        Return True when at least one, but not all, terminals
        are connected.
        """
        states = tuple(
            terminal.is_connected
            for terminal in self.terminals
        )

        return any(states) and not all(states)

    @property
    def primary_is_connected(self) -> bool:
        """
        Return True when both primary terminals are connected.
        """
        return (
            self._p1_terminal.is_connected
            and self._p2_terminal.is_connected
        )

    @property
    def secondary_is_connected(self) -> bool:
        """
        Return True when both secondary terminals are connected.
        """
        return (
            self._s1_terminal.is_connected
            and self._s2_terminal.is_connected
        )

    # ============================================================
    # RATED CURRENT
    # ============================================================

    @property
    def primary_rated_current_a(self) -> float:
        """
        Return rated primary current in amperes.
        """
        return self._primary_rated_current_a

    @primary_rated_current_a.setter
    def primary_rated_current_a(
        self,
        value: float,
    ) -> None:
        self._primary_rated_current_a = (
            self._validate_positive(
                value,
                "primary_rated_current_a",
            )
        )

    @property
    def secondary_rated_current_a(self) -> float:
        """
        Return rated secondary current in amperes.
        """
        return self._secondary_rated_current_a

    @secondary_rated_current_a.setter
    def secondary_rated_current_a(
        self,
        value: float,
    ) -> None:
        self._secondary_rated_current_a = (
            self._validate_positive(
                value,
                "secondary_rated_current_a",
            )
        )

    # ============================================================
    # TRANSFORMATION RATIO
    # ============================================================

    @property
    def ratio(self) -> float:
        """
        Return CT transformation ratio:

            primary rated current /
            secondary rated current
        """
        return (
            self._primary_rated_current_a
            / self._secondary_rated_current_a
        )

    @property
    def turns_ratio(self) -> float:
        """
        Return the nominal current transformation ratio.

        Alias for ratio for engineering readability.
        """
        return self.ratio

    # ============================================================
    # BURDEN
    # ============================================================

    @property
    def burden_va(self) -> float | None:
        """
        Return rated secondary burden in VA.
        """
        return self._burden_va

    @burden_va.setter
    def burden_va(
        self,
        value: float | None,
    ) -> None:
        self._burden_va = (
            self._validate_optional_positive(
                value,
                "burden_va",
            )
        )

    # ============================================================
    # ACCURACY CLASS
    # ============================================================

    @property
    def accuracy_class(self) -> str | None:
        """
        Return CT accuracy class.
        """
        return self._accuracy_class

    @accuracy_class.setter
    def accuracy_class(
        self,
        value: str | None,
    ) -> None:
        self._accuracy_class = (
            self._validate_accuracy_class(
                value
            )
        )

    # ============================================================
    # FREQUENCY
    # ============================================================

    @property
    def frequency_hz(self) -> float:
        """
        Return rated frequency in Hz.
        """
        return self._frequency_hz

    @frequency_hz.setter
    def frequency_hz(
        self,
        value: float,
    ) -> None:
        self._frequency_hz = (
            self._validate_positive(
                value,
                "frequency_hz",
            )
        )

    # ============================================================
    # POLARITY
    # ============================================================

    @property
    def polarity(self) -> CTPolarity:
        """
        Return CT polarity convention.
        """
        return self._polarity

    @polarity.setter
    def polarity(
        self,
        value: CTPolarity | str,
    ) -> None:
        self._polarity = (
            self._validate_polarity(
                value
            )
        )

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the CT is in service.
        """
        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = (
            self._validate_bool(
                value,
                "in_service",
            )
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate CurrentTransformer-specific parameters.

        The inherited ElectricalObject validation contract is
        executed first.
        """

        super().validate_parameters()

        self._primary_rated_current_a = (
            self._validate_positive(
                self._primary_rated_current_a,
                "primary_rated_current_a",
            )
        )

        self._secondary_rated_current_a = (
            self._validate_positive(
                self._secondary_rated_current_a,
                "secondary_rated_current_a",
            )
        )

        self._burden_va = (
            self._validate_optional_positive(
                self._burden_va,
                "burden_va",
            )
        )

        self._accuracy_class = (
            self._validate_accuracy_class(
                self._accuracy_class
            )
        )

        self._frequency_hz = (
            self._validate_positive(
                self._frequency_hz,
                "frequency_hz",
            )
        )

        self._polarity = (
            self._validate_polarity(
                self._polarity
            )
        )

        self._in_service = (
            self._validate_bool(
                self._in_service,
                "in_service",
            )
        )

        self._p1_terminal.validate()
        self._p2_terminal.validate()
        self._s1_terminal.validate()
        self._s2_terminal.validate()

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured CT diagnostics.

        Endpoint information is obtained from Terminal.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "primary_rated_current_a": (
                    self._primary_rated_current_a
                ),
                "secondary_rated_current_a": (
                    self._secondary_rated_current_a
                ),
                "ratio": self.ratio,
                "burden_va": self._burden_va,
                "accuracy_class": self._accuracy_class,
                "frequency_hz": self._frequency_hz,
                "polarity": self._polarity.value,
                "in_service": self._in_service,
                "p1_endpoint": self._endpoint_identifier(
                    self._p1_terminal.endpoint
                ),
                "p2_endpoint": self._endpoint_identifier(
                    self._p2_terminal.endpoint
                ),
                "s1_endpoint": self._endpoint_identifier(
                    self._s1_terminal.endpoint
                ),
                "s2_endpoint": self._endpoint_identifier(
                    self._s2_terminal.endpoint
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

        return (
            f"<CurrentTransformer "
            f"id={self.id}, "
            f"ratio="
            f"{self._primary_rated_current_a:.3g}/"
            f"{self._secondary_rated_current_a:.3g}, "
            f"polarity={self._polarity.value}, "
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
            numeric = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(numeric):
            raise ValueError(
                f"{name} must be finite."
            )

        return numeric

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Validate a positive finite numeric value.
        """

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return numeric

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

        return cls._validate_positive(
            value,
            name,
        )

    @staticmethod
    def _validate_accuracy_class(
        value: str | None,
    ) -> str | None:
        """
        Validate an optional CT accuracy-class identifier.
        """

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "accuracy_class must be a string or None."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                "accuracy_class cannot be empty."
            )

        return value

    @staticmethod
    def _validate_polarity(
        value: CTPolarity | str,
    ) -> CTPolarity:
        """
        Validate and normalize CT polarity.
        """

        if isinstance(
            value,
            CTPolarity,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            try:
                return CTPolarity(value)
            except ValueError:
                try:
                    return CTPolarity[
                        value
                    ]
                except KeyError as exc:
                    raise ValueError(
                        "polarity must be a valid "
                        "CTPolarity value."
                    ) from exc

        raise TypeError(
            "polarity must be a CTPolarity or string."
        )

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
    "CTPolarity",
    "CurrentTransformer",
]
