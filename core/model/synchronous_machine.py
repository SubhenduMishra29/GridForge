# core/model/synchronous_machine.py
"""
GridForge V2 Synchronous Machine Model
======================================

Author:
    Subhendu Mishra

File:
    core/model/synchronous_machine.py

Purpose
-------
Defines the canonical GridForge V2 synchronous-machine electrical
model.

Architectural role
------------------
A SynchronousMachine is a static electrical generator/machine model
used by the Core domain.

It owns:

    - persistent identity
    - electrical operating point
    - active/reactive power limits
    - rated apparent power
    - terminal voltage rating
    - machine impedance parameters
    - operating state
    - one authoritative electrical terminal
    - optional dynamic-model reference

It does NOT own:

    - network topology
    - network graph state
    - bus collections
    - power-flow solving
    - short-circuit solving
    - dynamic simulation execution
    - AVR execution
    - governor execution
    - exciter execution
    - PSS execution
    - protection algorithms
    - SLD geometry
    - GUI state

Power convention
----------------
GridForge uses the injection convention:

    P > 0  -> active power injected into network
    Q > 0  -> reactive power injected into network

Machine impedance convention
----------------------------
Positive resistance/reactance values represent the machine's
electrical impedance parameters.

The model does not calculate a study-specific matrix or perform
per-unit conversion. Those responsibilities belong to the
appropriate numerical/study layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class SynchronousMachine(ElectricalObject):
    """
    Static synchronous-machine electrical model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    endpoint:
        Electrical endpoint. May be None until connected.

    p_mw:
        Active-power injection in MW.

    q_mvar:
        Reactive-power injection in MVAr.

    s_rated_mva:
        Machine apparent-power rating in MVA.

    v_rated_kv:
        Machine terminal voltage rating in kV.

    p_min_mw:
        Minimum active-power operating limit.

    p_max_mw:
        Maximum active-power operating limit.

    q_min_mvar:
        Minimum reactive-power operating limit.

    q_max_mvar:
        Maximum reactive-power operating limit.

    r_pu:
        Machine resistance in per-unit.

    x_pu:
        Machine reactance in per-unit.

    xd_pu:
        Direct-axis synchronous reactance in per-unit.

    xq_pu:
        Quadrature-axis synchronous reactance in per-unit.

    xd_prime_pu:
        Direct-axis transient reactance in per-unit.

    xd_double_prime_pu:
        Direct-axis subtransient reactance in per-unit.

    xq_prime_pu:
        Quadrature-axis transient reactance in per-unit.

    xq_double_prime_pu:
        Quadrature-axis subtransient reactance in per-unit.

    in_service:
        Whether the machine is electrically active.

    bus:
        Backward-compatible endpoint alias.

    dynamic_model:
        Optional dynamic-model reference. The static machine model
        never executes dynamic simulation itself.
    """

    TYPE = "SYNCHRONOUS_MACHINE"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint: Any = None,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        s_rated_mva: float | None = None,
        v_rated_kv: float | None = None,
        p_min_mw: float | None = None,
        p_max_mw: float | None = None,
        q_min_mvar: float | None = None,
        q_max_mvar: float | None = None,
        r_pu: float = 0.0,
        x_pu: float = 0.0,
        xd_pu: float | None = None,
        xq_pu: float | None = None,
        xd_prime_pu: float | None = None,
        xd_double_prime_pu: float | None = None,
        xq_prime_pu: float | None = None,
        xq_double_prime_pu: float | None = None,
        in_service: bool = True,
        bus: Any = None,
        dynamic_model: Any = None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # ENDPOINT COMPATIBILITY
        # =============================================================

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"SynchronousMachine '{self.id}' received both "
                "endpoint and bus with different values."
            )

        if endpoint is None:
            endpoint = bus

        # =============================================================
        # OPERATING POINT
        # =============================================================

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        # =============================================================
        # MACHINE RATINGS
        # =============================================================

        self.s_rated_mva = (
            None
            if s_rated_mva is None
            else self._validate_positive(
                s_rated_mva,
                "s_rated_mva",
            )
        )

        self.v_rated_kv = (
            None
            if v_rated_kv is None
            else self._validate_positive(
                v_rated_kv,
                "v_rated_kv",
            )
        )

        # =============================================================
        # POWER LIMITS
        # =============================================================

        self.p_min_mw = (
            None
            if p_min_mw is None
            else self._validate_finite(
                p_min_mw,
                "p_min_mw",
            )
        )

        self.p_max_mw = (
            None
            if p_max_mw is None
            else self._validate_finite(
                p_max_mw,
                "p_max_mw",
            )
        )

        self.q_min_mvar = (
            None
            if q_min_mvar is None
            else self._validate_finite(
                q_min_mvar,
                "q_min_mvar",
            )
        )

        self.q_max_mvar = (
            None
            if q_max_mvar is None
            else self._validate_finite(
                q_max_mvar,
                "q_max_mvar",
            )
        )

        # =============================================================
        # MACHINE IMPEDANCE PARAMETERS
        # =============================================================

        self.r_pu = self._validate_non_negative(
            r_pu,
            "r_pu",
        )

        self.x_pu = self._validate_non_negative(
            x_pu,
            "x_pu",
        )

        self.xd_pu = self._validate_optional_non_negative(
            xd_pu,
            "xd_pu",
        )

        self.xq_pu = self._validate_optional_non_negative(
            xq_pu,
            "xq_pu",
        )

        self.xd_prime_pu = self._validate_optional_non_negative(
            xd_prime_pu,
            "xd_prime_pu",
        )

        self.xd_double_prime_pu = (
            self._validate_optional_non_negative(
                xd_double_prime_pu,
                "xd_double_prime_pu",
            )
        )

        self.xq_prime_pu = self._validate_optional_non_negative(
            xq_prime_pu,
            "xq_prime_pu",
        )

        self.xq_double_prime_pu = (
            self._validate_optional_non_negative(
                xq_double_prime_pu,
                "xq_double_prime_pu",
            )
        )

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self._validate_bool(
            in_service,
            "in_service",
        )

        self.in_service = in_service

        # =============================================================
        # AUTHORITATIVE TERMINAL
        # =============================================================

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # =============================================================
        # OPTIONAL DYNAMIC MODEL REFERENCE
        # =============================================================

        self.dynamic_model = dynamic_model

        # =============================================================
        # COMMON VALIDATION
        # =============================================================

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
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the authoritative machine terminal."""

        return (
            self.terminal,
        )

    @property
    def endpoint(self) -> Any:
        """Return the authoritative electrical endpoint."""

        return self.terminal.endpoint

    @property
    def bus(self) -> Any:
        """Compatibility accessor for the historical bus API."""

        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return whether the machine terminal is connected."""

        return self.terminal.is_connected

    # =================================================================
    # ENDPOINT CONNECTIVITY
    # =================================================================

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the machine terminal.

        Topology remains owned by core/network.
        """

        if endpoint is None:
            raise ValueError(
                f"SynchronousMachine '{self.id}' endpoint "
                "cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """Disconnect the machine terminal."""

        self.terminal.disconnect()

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the machine is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the machine is out of service."""

        return not self.in_service

    @property
    def is_available(self) -> bool:
        """Return whether the machine is electrically available."""

        return self.in_service

    def put_in_service(self) -> None:
        """Place the machine in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the machine out of service."""

        self.in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """Set service state without silent coercion."""

        self._validate_bool(
            value,
            "in_service",
        )

        self.in_service = value

    def connect(self) -> None:
        """Compatibility service-state alias."""

        self.put_in_service()

    def disconnect(self) -> None:
        """Compatibility service-state alias."""

        self.take_out_of_service()

    def close(self) -> None:
        """Place the machine in service."""

        self.put_in_service()

    def trip(self) -> None:
        """Take the machine out of service."""

        self.take_out_of_service()

    # =================================================================
    # ACTIVE POWER
    # =================================================================

    @property
    def active_power_injection_mw(self) -> float:
        """Return effective active-power network injection."""

        if not self.in_service:
            return 0.0

        return self.p_mw

    @property
    def p_injection_mw(self) -> float:
        """Compatibility alias for active injection."""

        return self.active_power_injection_mw

    def set_active_power(
        self,
        p_mw: float,
    ) -> None:
        """Set active-power injection."""

        p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self._validate_active_power(
            p_mw
        )

        self.p_mw = p_mw

    def set_p(
        self,
        p_mw: float,
    ) -> None:
        """Compatibility alias."""

        self.set_active_power(
            p_mw
        )

    # =================================================================
    # REACTIVE POWER
    # =================================================================

    @property
    def reactive_power_injection_mvar(self) -> float:
        """Return effective reactive-power network injection."""

        if not self.in_service:
            return 0.0

        return self.q_mvar

    @property
    def q_injection_mvar(self) -> float:
        """Compatibility alias for reactive injection."""

        return self.reactive_power_injection_mvar

    def set_reactive_power(
        self,
        q_mvar: float,
    ) -> None:
        """Set reactive-power injection."""

        q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        self._validate_reactive_power(
            q_mvar
        )

        self.q_mvar = q_mvar

    def set_q(
        self,
        q_mvar: float,
    ) -> None:
        """Compatibility alias."""

        self.set_reactive_power(
            q_mvar
        )

    # =================================================================
    # POWER INJECTION
    # =================================================================

    def injection(self) -> tuple[float, float]:
        """
        Return effective P/Q network injection.

        Positive P/Q values represent injection into the network.
        """

        return (
            self.active_power_injection_mw,
            self.reactive_power_injection_mvar,
        )

    # =================================================================
    # APPARENT POWER
    # =================================================================

    @property
    def apparent_power_mva(self) -> float:
        """Return magnitude of the current operating P/Q point."""

        return math.hypot(
            self.active_power_injection_mw,
            self.reactive_power_injection_mvar,
        )

    @property
    def power_factor(self) -> float | None:
        """
        Return operating power factor.

        Returns None for a zero apparent-power operating point.
        """

        s = self.apparent_power_mva

        if math.isclose(
            s,
            0.0,
            abs_tol=1e-12,
        ):
            return None

        return (
            self.active_power_injection_mw / s
        )

    # =================================================================
    # MACHINE PARAMETERS
    # =================================================================

    @property
    def synchronous_impedance_pu(self) -> complex:
        """
        Return the generic synchronous impedance representation.
        """

        return complex(
            self.r_pu,
            self.x_pu,
        )

    @property
    def xd_pu_effective(self) -> float:
        """Return configured direct-axis synchronous reactance."""

        return (
            0.0
            if self.xd_pu is None
            else self.xd_pu
        )

    @property
    def xq_pu_effective(self) -> float:
        """Return configured quadrature-axis synchronous reactance."""

        return (
            0.0
            if self.xq_pu is None
            else self.xq_pu
        )

    @property
    def xd_prime_pu_effective(self) -> float:
        """Return configured direct-axis transient reactance."""

        return (
            0.0
            if self.xd_prime_pu is None
            else self.xd_prime_pu
        )

    @property
    def xd_double_prime_pu_effective(self) -> float:
        """Return configured direct-axis subtransient reactance."""

        return (
            0.0
            if self.xd_double_prime_pu is None
            else self.xd_double_prime_pu
        )

    @property
    def xq_prime_pu_effective(self) -> float:
        """Return configured quadrature-axis transient reactance."""

        return (
            0.0
            if self.xq_prime_pu is None
            else self.xq_prime_pu
        )

    @property
    def xq_double_prime_pu_effective(self) -> float:
        """Return configured quadrature-axis subtransient reactance."""

        return (
            0.0
            if self.xq_double_prime_pu is None
            else self.xq_double_prime_pu
        )

    # =================================================================
    # DYNAMIC MODEL REFERENCE
    # =================================================================

    @property
    def has_dynamic_model(self) -> bool:
        """Return whether dynamic-model metadata is attached."""

        return self.dynamic_model is not None

    def attach_dynamic_model(
        self,
        dynamic_model: Any,
    ) -> None:
        """
        Attach dynamic-model metadata/reference.

        Execution belongs to the simulation layer.
        """

        if dynamic_model is None:
            raise ValueError(
                "dynamic_model cannot be None."
            )

        self.dynamic_model = dynamic_model

    def detach_dynamic_model(self) -> Any:
        """Detach and return the dynamic-model reference."""

        dynamic_model = self.dynamic_model
        self.dynamic_model = None
        return dynamic_model

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """Validate machine-local engineering parameters."""

        self.p_mw = self._validate_finite(
            self.p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            self.q_mvar,
            "q_mvar",
        )

        if self.s_rated_mva is not None:
            self.s_rated_mva = self._validate_positive(
                self.s_rated_mva,
                "s_rated_mva",
            )

        if self.v_rated_kv is not None:
            self.v_rated_kv = self._validate_positive(
                self.v_rated_kv,
                "v_rated_kv",
            )

        self.r_pu = self._validate_non_negative(
            self.r_pu,
            "r_pu",
        )

        self.x_pu = self._validate_non_negative(
            self.x_pu,
            "x_pu",
        )

        self.xd_pu = self._validate_optional_non_negative(
            self.xd_pu,
            "xd_pu",
        )

        self.xq_pu = self._validate_optional_non_negative(
            self.xq_pu,
            "xq_pu",
        )

        self.xd_prime_pu = self._validate_optional_non_negative(
            self.xd_prime_pu,
            "xd_prime_pu",
        )

        self.xd_double_prime_pu = (
            self._validate_optional_non_negative(
                self.xd_double_prime_pu,
                "xd_double_prime_pu",
            )
        )

        self.xq_prime_pu = self._validate_optional_non_negative(
            self.xq_prime_pu,
            "xq_prime_pu",
        )

        self.xq_double_prime_pu = (
            self._validate_optional_non_negative(
                self.xq_double_prime_pu,
                "xq_double_prime_pu",
            )
        )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        if self.terminal.owner is not self:
            raise ValueError(
                f"SynchronousMachine '{self.id}' terminal ownership "
                "is invalid."
            )

        self._validate_power_limits()

        self._validate_active_power(
            self.p_mw
        )

        self._validate_reactive_power(
            self.q_mvar
        )

        self._validate_apparent_power_rating()

        return True

    def validate(self) -> bool:
        """Validate through the common model contract."""

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured synchronous-machine diagnostics."""

        endpoint_id = None

        if self.endpoint is not None:
            endpoint_id = getattr(
                self.endpoint,
                "id",
                self.endpoint,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "p_mw": self.p_mw,
            "q_mvar": self.q_mvar,

            "p_min_mw": self.p_min_mw,
            "p_max_mw": self.p_max_mw,

            "q_min_mvar": self.q_min_mvar,
            "q_max_mvar": self.q_max_mvar,

            "s_rated_mva": self.s_rated_mva,
            "v_rated_kv": self.v_rated_kv,

            "r_pu": self.r_pu,
            "x_pu": self.x_pu,

            "xd_pu": self.xd_pu,
            "xq_pu": self.xq_pu,
            "xd_prime_pu": self.xd_prime_pu,
            "xd_double_prime_pu":
                self.xd_double_prime_pu,
            "xq_prime_pu": self.xq_prime_pu,
            "xq_double_prime_pu":
                self.xq_double_prime_pu,

            "active_power_injection_mw":
                self.active_power_injection_mw,

            "reactive_power_injection_mvar":
                self.reactive_power_injection_mvar,

            "apparent_power_mva":
                self.apparent_power_mva,

            "power_factor":
                self.power_factor,

            "in_service": self.in_service,
            "is_available": self.is_available,

            "endpoint": endpoint_id,
            "is_connected": self.is_connected,

            "has_dynamic_model":
                self.has_dynamic_model,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<SynchronousMachine "
            f"id={self.id}, "
            f"P={self.p_mw:.6f} MW, "
            f"Q={self.q_mvar:.6f} MVAr, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    def _validate_power_limits(self) -> None:
        """Validate configured P/Q operating limits."""

        if (
            self.p_min_mw is not None
            and self.p_max_mw is not None
            and self.p_min_mw > self.p_max_mw
        ):
            raise ValueError(
                "p_min_mw cannot be greater than p_max_mw."
            )

        if (
            self.q_min_mvar is not None
            and self.q_max_mvar is not None
            and self.q_min_mvar > self.q_max_mvar
        ):
            raise ValueError(
                "q_min_mvar cannot be greater than q_max_mvar."
            )

    def _validate_active_power(
        self,
        p_mw: float,
    ) -> None:
        """Validate active-power limits when configured."""

        if (
            self.p_min_mw is not None
            and p_mw < self.p_min_mw
        ):
            raise ValueError(
                f"p_mw={p_mw} is below "
                f"p_min_mw={self.p_min_mw}."
            )

        if (
            self.p_max_mw is not None
            and p_mw > self.p_max_mw
        ):
            raise ValueError(
                f"p_mw={p_mw} exceeds "
                f"p_max_mw={self.p_max_mw}."
            )

    def _validate_reactive_power(
        self,
        q_mvar: float,
    ) -> None:
        """Validate reactive-power limits when configured."""

        if (
            self.q_min_mvar is not None
            and q_mvar < self.q_min_mvar
        ):
            raise ValueError(
                f"q_mvar={q_mvar} is below "
                f"q_min_mvar={self.q_min_mvar}."
            )

        if (
            self.q_max_mvar is not None
            and q_mvar > self.q_max_mvar
        ):
            raise ValueError(
                f"q_mvar={q_mvar} exceeds "
                f"q_max_mvar={self.q_max_mvar}."
            )

    def _validate_apparent_power_rating(self) -> None:
        """Validate the operating point against S rating."""

        if self.s_rated_mva is None:
            return

        s = math.hypot(
            self.p_mw,
            self.q_mvar,
        )

        if s > self.s_rated_mva + 1e-12:
            raise ValueError(
                f"Operating apparent power {s:.6f} MVA exceeds "
                f"s_rated_mva={self.s_rated_mva:.6f} MVA."
            )

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require a finite value."""

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
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Validate a strictly positive finite value."""

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
        """Validate a non-negative finite value."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value

    @classmethod
    def _validate_optional_non_negative(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """Validate an optional non-negative finite value."""

        if value is None:
            return None

        return cls._validate_non_negative(
            value,
            name,
        )

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> None:
        """Require an actual boolean."""

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )


# Common short alias used by some domain-facing code.
SyncMachine = SynchronousMachine


__all__ = [
    "SynchronousMachine",
    "SyncMachine",
]
