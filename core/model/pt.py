# ============================================================
# File: core/model/pt.py
# GridForge V2 — Potential Transformer Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Potential Transformer Model
==========================================

Potential Transformer (PT) / Voltage Transformer (VT) domain model.

Architecture
------------

    ElectricalObject
           |
           v
          PT
       /  / \  \
      A  B   A  B
      |  |   |  |
      v  v   v  v
    Terminal endpoints

A PT is a four-terminal instrument-transformer element.

Physical terminals:

    primary_a
    primary_b
    secondary_a
    secondary_b

Terminal Contract
-----------------

Terminal is the authoritative owner of endpoint state.

PT owns the four Terminal objects.

Each Terminal owns:

    owner
    role
    endpoint
    connection state

Endpoint mutation must use:

    Terminal.attach(endpoint)
    Terminal.detach()

PT does not maintain duplicate endpoint state.

Domain Boundary
---------------

PT owns CT/PT nameplate and measurement characteristics:

    - primary rated voltage
    - secondary rated voltage
    - voltage ratio
    - accuracy class
    - burden
    - phase displacement
    - service state

PT does NOT own:

    - Bus objects
    - Network topology
    - graph state
    - relay logic
    - protection decisions
    - measurement channels
    - solver matrices
    - SLD geometry
    - GUI state
    - rendering state

Those responsibilities belong to the appropriate Core,
Application, Analysis, and UI layers.

Validation
----------

ElectricalObject remains the authoritative object-validation
entry point.

PT specializes:

    validate_parameters()

PT does not replace the inherited validation contract.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class PT(ElectricalObject):
    """
    Potential Transformer / Voltage Transformer model.

    A PT is a four-terminal measurement instrument transformer.

    Physical terminals:

        primary_a
        primary_b
        secondary_a
        secondary_b

    Terminal objects are authoritative for endpoint connectivity.
    """

    TYPE = "PT"

    __slots__ = (
        "_primary_a_terminal",
        "_primary_b_terminal",
        "_secondary_a_terminal",
        "_secondary_b_terminal",
        "_primary_voltage_kv",
        "_secondary_voltage_v",
        "_accuracy_class",
        "_burden_va",
        "_phase_displacement_deg",
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
        primary_voltage_kv: float = 11.0,
        secondary_voltage_v: float = 110.0,
        accuracy_class: str = "0.5",
        burden_va: float = 100.0,
        phase_displacement_deg: float = 0.0,
        in_service: bool = True,
        primary_a: Any = None,
        primary_b: Any = None,
        secondary_a: Any = None,
        secondary_b: Any = None,
    ) -> None:
        """
        Construct a Potential Transformer.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable PT name.

        primary_voltage_kv:
            Rated primary voltage in kV.

        secondary_voltage_v:
            Rated secondary voltage in volts.

        accuracy_class:
            Instrument-transformer accuracy class.

        burden_va:
            Rated secondary burden in VA.

        phase_displacement_deg:
            Rated phase displacement in degrees.

        in_service:
            Whether the PT is operationally in service.

        primary_a:
            Optional endpoint attached to primary terminal A.

        primary_b:
            Optional endpoint attached to primary terminal B.

        secondary_a:
            Optional endpoint attached to secondary terminal A.

        secondary_b:
            Optional endpoint attached to secondary terminal B.

        Notes
        -----
        Endpoint references are attached through Terminal.attach().
        PT does not maintain independent endpoint storage.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Authoritative terminals
        # --------------------------------------------------------

        self._primary_a_terminal = Terminal(
            owner=self,
            role="primary_a",
        )

        self._primary_b_terminal = Terminal(
            owner=self,
            role="primary_b",
        )

        self._secondary_a_terminal = Terminal(
            owner=self,
            role="secondary_a",
        )

        self._secondary_b_terminal = Terminal(
            owner=self,
            role="secondary_b",
        )

        # --------------------------------------------------------
        # Initial endpoint attachment
        # --------------------------------------------------------

        if primary_a is not None:
            self._primary_a_terminal.attach(
                primary_a
            )

        if primary_b is not None:
            self._primary_b_terminal.attach(
                primary_b
            )

        if secondary_a is not None:
            self._secondary_a_terminal.attach(
                secondary_a
            )

        if secondary_b is not None:
            self._secondary_b_terminal.attach(
                secondary_b
            )

        # --------------------------------------------------------
        # Nameplate / measurement parameters
        # --------------------------------------------------------

        self._primary_voltage_kv = (
            self._validate_positive(
                primary_voltage_kv,
                "primary_voltage_kv",
            )
        )

        self._secondary_voltage_v = (
            self._validate_positive(
                secondary_voltage_v,
                "secondary_voltage_v",
            )
        )

        self._accuracy_class = (
            self._validate_accuracy_class(
                accuracy_class
            )
        )

        self._burden_va = (
            self._validate_non_negative(
                burden_va,
                "burden_va",
            )
        )

        self._phase_displacement_deg = (
            self._validate_finite(
                phase_displacement_deg,
                "phase_displacement_deg",
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
    def primary_a(self) -> Terminal:
        """
        Return the authoritative primary-A terminal.
        """
        return self._primary_a_terminal

    @property
    def primary_b(self) -> Terminal:
        """
        Return the authoritative primary-B terminal.
        """
        return self._primary_b_terminal

    @property
    def secondary_a(self) -> Terminal:
        """
        Return the authoritative secondary-A terminal.
        """
        return self._secondary_a_terminal

    @property
    def secondary_b(self) -> Terminal:
        """
        Return the authoritative secondary-B terminal.
        """
        return self._secondary_b_terminal

    @property
    def primary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return primary terminals in deterministic order.
        """
        return (
            self._primary_a_terminal,
            self._primary_b_terminal,
        )

    @property
    def secondary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return secondary terminals in deterministic order.
        """
        return (
            self._secondary_a_terminal,
            self._secondary_b_terminal,
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

            primary_a
            primary_b
            secondary_a
            secondary_b
        """
        return (
            self._primary_a_terminal,
            self._primary_b_terminal,
            self._secondary_a_terminal,
            self._secondary_b_terminal,
        )

    # ============================================================
    # ENDPOINT ACCESS
    # ============================================================

    @property
    def primary_a_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by primary_a Terminal.
        """
        return self._primary_a_terminal.endpoint

    @property
    def primary_b_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by primary_b Terminal.
        """
        return self._primary_b_terminal.endpoint

    @property
    def secondary_a_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by secondary_a Terminal.
        """
        return self._secondary_a_terminal.endpoint

    @property
    def secondary_b_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by secondary_b Terminal.
        """
        return self._secondary_b_terminal.endpoint

    # ============================================================
    # ENDPOINT MUTATION
    # ============================================================

    def connect_primary_a(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to primary_a.
        """
        self._primary_a_terminal.attach(
            endpoint
        )

    def connect_primary_b(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to primary_b.
        """
        self._primary_b_terminal.attach(
            endpoint
        )

    def connect_secondary_a(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to secondary_a.
        """
        self._secondary_a_terminal.attach(
            endpoint
        )

    def connect_secondary_b(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to secondary_b.
        """
        self._secondary_b_terminal.attach(
            endpoint
        )

    def disconnect_primary_a(self) -> None:
        """
        Detach primary_a.
        """
        self._primary_a_terminal.detach()

    def disconnect_primary_b(self) -> None:
        """
        Detach primary_b.
        """
        self._primary_b_terminal.detach()

    def disconnect_secondary_a(self) -> None:
        """
        Detach secondary_a.
        """
        self._secondary_a_terminal.detach()

    def disconnect_secondary_b(self) -> None:
        """
        Detach secondary_b.
        """
        self._secondary_b_terminal.detach()

    def disconnect_all(self) -> None:
        """
        Detach all PT terminals.
        """
        for terminal in self.terminals:
            terminal.detach()

    # ============================================================
    # NAMEPLATE — PRIMARY VOLTAGE
    # ============================================================

    @property
    def primary_voltage_kv(self) -> float:
        """
        Return rated primary voltage in kV.
        """
        return self._primary_voltage_kv

    @primary_voltage_kv.setter
    def primary_voltage_kv(
        self,
        value: float,
    ) -> None:
        self._primary_voltage_kv = (
            self._validate_positive(
                value,
                "primary_voltage_kv",
            )
        )

    # ============================================================
    # NAMEPLATE — SECONDARY VOLTAGE
    # ============================================================

    @property
    def secondary_voltage_v(self) -> float:
        """
        Return rated secondary voltage in volts.
        """
        return self._secondary_voltage_v

    @secondary_voltage_v.setter
    def secondary_voltage_v(
        self,
        value: float,
    ) -> None:
        self._secondary_voltage_v = (
            self._validate_positive(
                value,
                "secondary_voltage_v",
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
        is stored in V, therefore primary voltage is converted
        to volts before calculating the ratio.
        """
        return (
            self._primary_voltage_kv * 1000.0
            / self._secondary_voltage_v
        )

    @property
    def ratio(self) -> float:
        """
        Return nominal PT voltage ratio.

        Compatibility alias for voltage_ratio.
        """
        return self.voltage_ratio

    # ============================================================
    # ACCURACY CLASS
    # ============================================================

    @property
    def accuracy_class(self) -> str:
        """
        Return instrument-transformer accuracy class.
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
    def burden_va(self) -> float:
        """
        Return rated secondary burden in VA.
        """
        return self._burden_va

    @burden_va.setter
    def burden_va(
        self,
        value: float,
    ) -> None:
        self._burden_va = (
            self._validate_non_negative(
                value,
                "burden_va",
            )
        )

    # ============================================================
    # PHASE DISPLACEMENT
    # ============================================================

    @property
    def phase_displacement_deg(self) -> float:
        """
        Return rated phase displacement in degrees.
        """
        return self._phase_displacement_deg

    @phase_displacement_deg.setter
    def phase_displacement_deg(
        self,
        value: float,
    ) -> None:
        self._phase_displacement_deg = (
            self._validate_finite(
                value,
                "phase_displacement_deg",
            )
        )

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the PT is in service.
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
        Return True when the PT is in service.
        """
        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the PT is out of service.
        """
        return not self._in_service

    def put_in_service(self) -> None:
        """
        Place the PT in service.
        """
        self._in_service = True

    def take_out_of_service(self) -> None:
        """
        Take the PT out of service.
        """
        self._in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set PT service state using strict boolean validation.
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
        Return True when both primary terminals are connected.
        """
        return (
            self._primary_a_terminal.is_connected
            and self._primary_b_terminal.is_connected
        )

    @property
    def is_secondary_connected(self) -> bool:
        """
        Return True when both secondary terminals are connected.
        """
        return (
            self._secondary_a_terminal.is_connected
            and self._secondary_b_terminal.is_connected
        )

    @property
    def is_connected(self) -> bool:
        """
        Return True when all four PT terminals are connected.
        """
        return all(
            terminal.is_connected
            for terminal in self.terminals
        )

    @property
    def is_partially_connected(self) -> bool:
        """
        Return True when at least one but not all PT terminals
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
        Validate PT-specific parameters.

        Network topology is deliberately not validated here.
        """

        super().validate_parameters()

        self._primary_voltage_kv = (
            self._validate_positive(
                self._primary_voltage_kv,
                "primary_voltage_kv",
            )
        )

        self._secondary_voltage_v = (
            self._validate_positive(
                self._secondary_voltage_v,
                "secondary_voltage_v",
            )
        )

        self._accuracy_class = (
            self._validate_accuracy_class(
                self._accuracy_class
            )
        )

        self._burden_va = (
            self._validate_non_negative(
                self._burden_va,
                "burden_va",
            )
        )

        self._phase_displacement_deg = (
            self._validate_finite(
                self._phase_displacement_deg,
                "phase_displacement_deg",
            )
        )

        self._in_service = (
            self._validate_bool(
                self._in_service,
                "in_service",
            )
        )

        # --------------------------------------------------------
        # Terminal ownership validation
        # --------------------------------------------------------

        for terminal in self.terminals:
            if terminal.owner is not self:
                raise ValueError(
                    f"PT '{self.id}' terminal ownership is invalid."
                )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured PT diagnostic information.

        Endpoint information is delegated to Terminal.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "primary_voltage_kv":
                self._primary_voltage_kv,

            "secondary_voltage_v":
                self._secondary_voltage_v,

            "voltage_ratio":
                self.voltage_ratio,

            "accuracy_class":
                self._accuracy_class,

            "burden_va":
                self._burden_va,

            "phase_displacement_deg":
                self._phase_displacement_deg,

            "in_service":
                self._in_service,

            "primary_a_endpoint":
                self._endpoint_identifier(
                    self._primary_a_terminal.endpoint
                ),

            "primary_b_endpoint":
                self._endpoint_identifier(
                    self._primary_b_terminal.endpoint
                ),

            "secondary_a_endpoint":
                self._endpoint_identifier(
                    self._secondary_a_terminal.endpoint
                ),

            "secondary_b_endpoint":
                self._endpoint_identifier(
                    self._secondary_b_terminal.endpoint
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
            f"<PT "
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
        Validate the PT accuracy-class identifier.
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
    "PT",
]
