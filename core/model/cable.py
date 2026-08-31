# ============================================================
# File: core/model/cvt.py
# GridForge V2 — Capacitive Voltage Transformer Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Capacitive Voltage Transformer Model
===================================================

Capacitive Voltage Transformer (CVT) / Capacitive Potential
Transformer (CPT) domain model.

Architecture
------------

    ElectricalObject
           |
           v
          CVT
       /  /  \  \
      H1 H2   X1 X2
      |  |    |  |
      v  v    v  v
    Terminal endpoints

A CVT is a four-terminal instrument-transformer element.

Physical terminals:

    H1 — primary/high-voltage terminal 1
    H2 — primary/high-voltage terminal 2
    X1 — secondary/low-voltage terminal 1
    X2 — secondary/low-voltage terminal 2

Terminal Contract
-----------------

Terminal is the authoritative owner of endpoint state.

CVT owns the four Terminal objects.

Each Terminal owns:

    owner
    role
    endpoint
    connection state

Endpoint mutation must use:

    Terminal.attach(endpoint)
    Terminal.detach()

CVT does not maintain duplicate endpoint state.

Domain Boundary
---------------

CVT owns static nameplate and instrument-transformer data:

    - rated primary voltage
    - rated secondary voltage
    - voltage ratio
    - accuracy class
    - rated burden
    - polarity
    - frequency
    - service state

CVT does NOT own:

    - Bus objects
    - Network topology
    - graph state
    - Y-bus construction
    - load-flow calculations
    - short-circuit calculations
    - relay logic
    - protection decisions
    - dynamic simulation
    - transient simulation
    - ferroresonance simulation
    - measurement channels
    - SLD geometry
    - GUI state
    - rendering state

Those responsibilities belong to the appropriate Core,
Application, Analysis, Numerical, and UI layers.

Validation
----------

ElectricalObject remains the authoritative validation entry point.

CVT specializes:

    validate_parameters()

CVT does not replace the inherited validation contract.

Engineering Convention
----------------------

H1/H2 are retained as the physical primary-side terminal names.

X1/X2 are retained as the physical secondary-side terminal names.

The model does not infer electrical topology from terminal names.
Terminal role is explicit and authoritative.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class CVTPolarity(str, Enum):
    """
    Physical polarity convention of a CVT.

    NORMAL:
        H1 corresponds to the positive/reference orientation
        relative to X1.

    REVERSED:
        The secondary polarity is reversed relative to the
        normal convention.

    This property describes the equipment convention only.
    It does not perform a voltage transformation calculation.
    """

    NORMAL = "NORMAL"
    REVERSED = "REVERSED"


class CapacitiveVoltageTransformer(ElectricalObject):
    """
    Four-terminal Capacitive Voltage Transformer.

    Physical terminals:

        H1 — primary/high-voltage terminal 1
        H2 — primary/high-voltage terminal 2
        X1 — secondary/low-voltage terminal 1
        X2 — secondary/low-voltage terminal 2

    Terminal objects are authoritative for endpoint state.
    """

    TYPE = "CVT"

    __slots__ = (
        "_h1_terminal",
        "_h2_terminal",
        "_x1_terminal",
        "_x2_terminal",
        "_rated_primary_voltage_kv",
        "_rated_secondary_voltage_v",
        "_accuracy_class",
        "_rated_burden_va",
        "_polarity",
        "_frequency_hz",
        "_in_service",
    )

    # ============================================================
    # CONSTRUCTION
    # ============================================================

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        rated_primary_voltage_kv: float = 220.0,
        rated_secondary_voltage_v: float = 110.0,
        accuracy_class: str = "0.5",
        rated_burden_va: float = 100.0,
        polarity: CVTPolarity | str = CVTPolarity.NORMAL,
        frequency_hz: float = 50.0,
        in_service: bool = True,
        h1_endpoint: Any = None,
        h2_endpoint: Any = None,
        x1_endpoint: Any = None,
        x2_endpoint: Any = None,
    ) -> None:
        """
        Construct a Capacitive Voltage Transformer.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable CVT name.

        rated_primary_voltage_kv:
            Rated primary voltage in kV.

        rated_secondary_voltage_v:
            Rated secondary voltage in volts.

        accuracy_class:
            Instrument-transformer accuracy class.

        rated_burden_va:
            Rated secondary burden in VA.

        polarity:
            CVTPolarity value or corresponding string.

        frequency_hz:
            Rated operating frequency in Hz.

        in_service:
            Whether the CVT is operationally in service.

        h1_endpoint:
            Optional endpoint attached to H1.

        h2_endpoint:
            Optional endpoint attached to H2.

        x1_endpoint:
            Optional endpoint attached to X1.

        x2_endpoint:
            Optional endpoint attached to X2.

        Notes
        -----
        Endpoint references are attached through Terminal.attach().
        No independent endpoint state is maintained by the CVT.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Authoritative physical terminals
        # --------------------------------------------------------

        self._h1_terminal = Terminal(
            owner=self,
            role="H1",
        )

        self._h2_terminal = Terminal(
            owner=self,
            role="H2",
        )

        self._x1_terminal = Terminal(
            owner=self,
            role="X1",
        )

        self._x2_terminal = Terminal(
            owner=self,
            role="X2",
        )

        # --------------------------------------------------------
        # Initial endpoint attachment
        # --------------------------------------------------------

        if h1_endpoint is not None:
            self._h1_terminal.attach(
                h1_endpoint
            )

        if h2_endpoint is not None:
            self._h2_terminal.attach(
                h2_endpoint
            )

        if x1_endpoint is not None:
            self._x1_terminal.attach(
                x1_endpoint
            )

        if x2_endpoint is not None:
            self._x2_terminal.attach(
                x2_endpoint
            )

        # --------------------------------------------------------
        # Nameplate parameters
        # --------------------------------------------------------

        self._rated_primary_voltage_kv = (
            self._validate_positive(
                rated_primary_voltage_kv,
                "rated_primary_voltage_kv",
            )
        )

        self._rated_secondary_voltage_v = (
            self._validate_positive(
                rated_secondary_voltage_v,
                "rated_secondary_voltage_v",
            )
        )

        self._accuracy_class = (
            self._validate_accuracy_class(
                accuracy_class
            )
        )

        self._rated_burden_va = (
            self._validate_non_negative(
                rated_burden_va,
                "rated_burden_va",
            )
        )

        self._polarity = (
            self._validate_polarity(
                polarity
            )
        )

        self._frequency_hz = (
            self._validate_positive(
                frequency_hz,
                "frequency_hz",
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
    def h1_terminal(self) -> Terminal:
        """
        Return the authoritative H1 terminal.
        """
        return self._h1_terminal

    @property
    def h2_terminal(self) -> Terminal:
        """
        Return the authoritative H2 terminal.
        """
        return self._h2_terminal

    @property
    def x1_terminal(self) -> Terminal:
        """
        Return the authoritative X1 terminal.
        """
        return self._x1_terminal

    @property
    def x2_terminal(self) -> Terminal:
        """
        Return the authoritative X2 terminal.
        """
        return self._x2_terminal

    @property
    def primary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return primary H1/H2 terminals.
        """
        return (
            self._h1_terminal,
            self._h2_terminal,
        )

    @property
    def secondary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return secondary X1/X2 terminals.
        """
        return (
            self._x1_terminal,
            self._x2_terminal,
        )

    @property
    def terminals(
        self,
    ) -> tuple[
        Terminal,
        Terminal,
        Terminal,
        Terminal,
    ]:
        """
        Return all authoritative terminals.

        Order:

            H1
            H2
            X1
            X2
        """
        return (
            self._h1_terminal,
            self._h2_terminal,
            self._x1_terminal,
            self._x2_terminal,
        )

    # ============================================================
    # ENDPOINT ACCESS
    # ============================================================

    @property
    def h1_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by H1 Terminal.
        """
        return self._h1_terminal.endpoint

    @property
    def h2_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by H2 Terminal.
        """
        return self._h2_terminal.endpoint

    @property
    def x1_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by X1 Terminal.
        """
        return self._x1_terminal.endpoint

    @property
    def x2_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by X2 Terminal.
        """
        return self._x2_terminal.endpoint

    # ============================================================
    # ENDPOINT MUTATION
    # ============================================================

    def connect_h1(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to H1.
        """
        self._h1_terminal.attach(
            endpoint
        )

    def connect_h2(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to H2.
        """
        self._h2_terminal.attach(
            endpoint
        )

    def connect_x1(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to X1.
        """
        self._x1_terminal.attach(
            endpoint
        )

    def connect_x2(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to X2.
        """
        self._x2_terminal.attach(
            endpoint
        )

    def disconnect_h1(self) -> None:
        """
        Detach H1.
        """
        self._h1_terminal.detach()

    def disconnect_h2(self) -> None:
        """
        Detach H2.
        """
        self._h2_terminal.detach()

    def disconnect_x1(self) -> None:
        """
        Detach X1.
        """
        self._x1_terminal.detach()

    def disconnect_x2(self) -> None:
        """
        Detach X2.
        """
        self._x2_terminal.detach()

    def disconnect_all(self) -> None:
        """
        Detach all CVT terminals.
        """
        for terminal in self.terminals:
            terminal.detach()

    # ============================================================
    # PRIMARY VOLTAGE
    # ============================================================

    @property
    def rated_primary_voltage_kv(self) -> float:
        """
        Return rated primary voltage in kV.
        """
        return self._rated_primary_voltage_kv

    @rated_primary_voltage_kv.setter
    def rated_primary_voltage_kv(
        self,
        value: float,
    ) -> None:
        self._rated_primary_voltage_kv = (
            self._validate_positive(
                value,
                "rated_primary_voltage_kv",
            )
        )

    # ============================================================
    # SECONDARY VOLTAGE
    # ============================================================

    @property
    def rated_secondary_voltage_v(self) -> float:
        """
        Return rated secondary voltage in volts.
        """
        return self._rated_secondary_voltage_v

    @rated_secondary_voltage_v.setter
    def rated_secondary_voltage_v(
        self,
        value: float,
    ) -> None:
        self._rated_secondary_voltage_v = (
            self._validate_positive(
                value,
                "rated_secondary_voltage_v",
            )
        )

    # ============================================================
    # VOLTAGE RATIO
    # ============================================================

    @property
    def voltage_ratio(self) -> float:
        """
        Return nominal primary-to-secondary voltage ratio.

        Primary voltage is stored in kV and secondary voltage
        is stored in V, so the primary value is converted to V.
        """
        return (
            self._rated_primary_voltage_kv * 1000.0
            / self._rated_secondary_voltage_v
        )

    @property
    def ratio(self) -> float:
        """
        Return nominal CVT voltage ratio.

        Alias for voltage_ratio.
        """
        return self.voltage_ratio

    # ============================================================
    # ACCURACY CLASS
    # ============================================================

    @property
    def accuracy_class(self) -> str:
        """
        Return the CVT accuracy class.
        """
        return self._accuracy_class

    @accuracy_class.setter
    def accuracy_class(
        self,
        value: str,
    ) -> None:
        self._accuracy_class = (
            self._validate_accuracy_class(
                value
            )
        )

    # ============================================================
    # BURDEN
    # ============================================================

    @property
    def rated_burden_va(self) -> float:
        """
        Return rated secondary burden in VA.
        """
        return self._rated_burden_va

    @rated_burden_va.setter
    def rated_burden_va(
        self,
        value: float,
    ) -> None:
        self._rated_burden_va = (
            self._validate_non_negative(
                value,
                "rated_burden_va",
            )
        )

    @property
    def burden_va(self) -> float:
        """
        Return rated burden in VA.

        Engineering alias for rated_burden_va.
        """
        return self._rated_burden_va

    @burden_va.setter
    def burden_va(
        self,
        value: float,
    ) -> None:
        self._rated_burden_va = (
            self._validate_non_negative(
                value,
                "burden_va",
            )
        )

    # ============================================================
    # POLARITY
    # ============================================================

    @property
    def polarity(self) -> CVTPolarity:
        """
        Return the CVT polarity convention.
        """
        return self._polarity

    @polarity.setter
    def polarity(
        self,
        value: CVTPolarity | str,
    ) -> None:
        self._polarity = (
            self._validate_polarity(
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
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the CVT is in service.
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

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the CVT is in service.
        """
        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the CVT is out of service.
        """
        return not self._in_service

    def put_in_service(self) -> None:
        """
        Place the CVT in service.
        """
        self._in_service = True

    def take_out_of_service(self) -> None:
        """
        Take the CVT out of service.
        """
        self._in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set CVT service state.
        """
        self._in_service = (
            self._validate_bool(
                value,
                "in_service",
            )
        )

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    @property
    def is_primary_connected(self) -> bool:
        """
        Return True when H1 and H2 are both connected.
        """
        return (
            self._h1_terminal.is_connected
            and self._h2_terminal.is_connected
        )

    @property
    def is_secondary_connected(self) -> bool:
        """
        Return True when X1 and X2 are both connected.
        """
        return (
            self._x1_terminal.is_connected
            and self._x2_terminal.is_connected
        )

    @property
    def is_connected(self) -> bool:
        """
        Return True when all four CVT terminals are connected.
        """
        return all(
            terminal.is_connected
            for terminal in self.terminals
        )

    @property
    def is_partially_connected(self) -> bool:
        """
        Return True when at least one but not all terminals
        are connected.
        """
        states = tuple(
            terminal.is_connected
            for terminal in self.terminals
        )

        return any(states) and not all(states)

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate CVT-specific parameters.

        Terminal ownership is also checked here.

        Network topology is deliberately not validated here.
        """

        super().validate_parameters()

        self._rated_primary_voltage_kv = (
            self._validate_positive(
                self._rated_primary_voltage_kv,
                "rated_primary_voltage_kv",
            )
        )

        self._rated_secondary_voltage_v = (
            self._validate_positive(
                self._rated_secondary_voltage_v,
                "rated_secondary_voltage_v",
            )
        )

        self._accuracy_class = (
            self._validate_accuracy_class(
                self._accuracy_class
            )
        )

        self._rated_burden_va = (
            self._validate_non_negative(
                self._rated_burden_va,
                "rated_burden_va",
            )
        )

        self._polarity = (
            self._validate_polarity(
                self._polarity
            )
        )

        self._frequency_hz = (
            self._validate_positive(
                self._frequency_hz,
                "frequency_hz",
            )
        )

        self._in_service = (
            self._validate_bool(
                self._in_service,
                "in_service",
            )
        )

        for terminal in self.terminals:
            if terminal.owner is not self:
                raise ValueError(
                    f"CVT '{self.id}' terminal ownership is invalid."
                )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured CVT diagnostic information.

        Endpoint information is obtained from Terminal.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "rated_primary_voltage_kv":
                self._rated_primary_voltage_kv,

            "rated_secondary_voltage_v":
                self._rated_secondary_voltage_v,

            "voltage_ratio":
                self.voltage_ratio,

            "accuracy_class":
                self._accuracy_class,

            "rated_burden_va":
                self._rated_burden_va,

            "polarity":
                self._polarity.value,

            "frequency_hz":
                self._frequency_hz,

            "in_service":
                self._in_service,

            "h1_endpoint":
                self._endpoint_identifier(
                    self._h1_terminal.endpoint
                ),

            "h2_endpoint":
                self._endpoint_identifier(
                    self._h2_terminal.endpoint
                ),

            "x1_endpoint":
                self._endpoint_identifier(
                    self._x1_terminal.endpoint
                ),

            "x2_endpoint":
                self._endpoint_identifier(
                    self._x2_terminal.endpoint
                ),

            "is_primary_connected":
                self.is_primary_connected,

            "is_secondary_connected":
                self.is_secondary_connected,

            "is_connected":
                self.is_connected,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<CVT "
            f"id={self.id}, "
            f"ratio={self.voltage_ratio:.6g}, "
            f"accuracy={self._accuracy_class}, "
            f"in_service={self._in_service}>"
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """
        Convert to float and require a finite value.
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
        Validate a finite positive numeric value.
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
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite non-negative numeric value.
        """

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return numeric

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
                f"{name} must be boolean."
            )

        return value

    @staticmethod
    def _validate_accuracy_class(
        value: str,
    ) -> str:
        """
        Validate an accuracy-class identifier.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "accuracy_class must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                "accuracy_class cannot be empty."
            )

        return value

    @staticmethod
    def _validate_polarity(
        value: CVTPolarity | str,
    ) -> CVTPolarity:
        """
        Validate and normalize CVT polarity.
        """

        if isinstance(
            value,
            CVTPolarity,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            try:
                return CVTPolarity(value)
            except ValueError:
                try:
                    return CVTPolarity[
                        value
                    ]
                except KeyError as exc:
                    raise ValueError(
                        "polarity must be a valid "
                        "CVTPolarity value."
                    ) from exc

        raise TypeError(
            "polarity must be a CVTPolarity or string."
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


# ============================================================
# Public aliases
# ============================================================

CVT = CapacitiveVoltageTransformer


__all__ = [
    "CVTPolarity",
    "CapacitiveVoltageTransformer",
    "CVT",
]
