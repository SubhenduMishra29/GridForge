# core/model/solar.py
"""
GridForge V2 Solar Generator Model
==================================

Author:
    Subhendu Mishra

File:
    core/model/solar.py

Purpose
-------
Defines the canonical GridForge V2 static solar generation model.

Architectural role
------------------
Solar is an electrical generation/injection model.

It owns:

    - identity
    - electrical operating point
    - active/reactive power limits
    - operating state
    - one electrical terminal
    - optional dynamic-model metadata

It does NOT own:

    - network topology
    - bus collections
    - graph state
    - Y-bus construction
    - power-flow solving
    - short-circuit solving
    - protection logic
    - SLD geometry
    - GUI state
    - dynamic simulation execution

Power convention
----------------
GridForge uses the injection convention:

    P > 0  -> active power injected into network
    Q > 0  -> reactive power injected into network

Therefore:

    P < 0  -> net active-power absorption
    Q < 0  -> net reactive-power absorption

The Network layer owns connectivity and topology.

The analysis/numerical layers consume the electrical state and
perform calculations.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Solar(ElectricalObject):
    """
    Static solar generation/injection model.

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

    p_max_mw:
        Maximum active-power output in MW.

    p_min_mw:
        Minimum active-power output in MW.

    q_max_mvar:
        Maximum reactive-power injection in MVAr.

    q_min_mvar:
        Minimum reactive-power injection in MVAr.

    in_service:
        Whether the solar generator is electrically active.

    bus:
        Backward-compatible endpoint alias.

    dynamic_model:
        Optional dynamic-model reference/metadata. The Solar model
        never executes the dynamic model itself.
    """

    TYPE = "SOLAR"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint: Any = None,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        p_max_mw: float | None = None,
        p_min_mw: float = 0.0,
        q_max_mvar: float | None = None,
        q_min_mvar: float | None = None,
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
                f"Solar '{self.id}' received both endpoint and bus "
                "with different values."
            )

        if endpoint is None:
            endpoint = bus

        # =============================================================
        # POWER STATE
        # =============================================================

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        # -------------------------------------------------------------
        # Active-power limits
        # -------------------------------------------------------------

        self.p_min_mw = self._validate_finite(
            p_min_mw,
            "p_min_mw",
        )

        if p_max_mw is None:
            p_max_mw = max(
                self.p_mw,
                self.p_min_mw,
            )

        self.p_max_mw = self._validate_finite(
            p_max_mw,
            "p_max_mw",
        )

        # -------------------------------------------------------------
        # Reactive-power limits
        # -------------------------------------------------------------

        self.q_max_mvar = (
            None
            if q_max_mvar is None
            else self._validate_finite(
                q_max_mvar,
                "q_max_mvar",
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
        # COMMON MODEL VALIDATION
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
        """Return the authoritative Solar terminal."""

        return (
            self.terminal,
        )

    @property
    def endpoint(self) -> Any:
        """Return the authoritative electrical endpoint."""

        return self.terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor for the historical bus API.

        The Terminal remains authoritative.
        """

        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return whether the Solar terminal is connected."""

        return self.terminal.is_connected

    # =================================================================
    # ENDPOINT CONNECTIVITY
    # =================================================================

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the Solar terminal.

        Network topology remains owned by the Network layer.
        """

        if endpoint is None:
            raise ValueError(
                f"Solar '{self.id}' endpoint cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Solar terminal.

        This does not change service state.
        """

        self.terminal.disconnect()

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the Solar generator is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the Solar generator is out of service."""

        return not self.in_service

    @property
    def is_available(self) -> bool:
        """Return whether the Solar generator is electrically active."""

        return self.in_service

    def put_in_service(self) -> None:
        """Place the Solar generator in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the Solar generator out of service."""

        self.in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """Set service state without silent boolean coercion."""

        self._validate_bool(
            value,
            "in_service",
        )

        self.in_service = value

    # Compatibility aliases. These are service-state operations,
    # not network-topology operations.

    def connect(self) -> None:
        """Compatibility alias for put_in_service()."""

        self.put_in_service()

    def disconnect(self) -> None:
        """Compatibility alias for take_out_of_service()."""

        self.take_out_of_service()

    def close(self) -> None:
        """Compatibility alias for putting the generator in service."""

        self.put_in_service()

    def trip(self) -> None:
        """Compatibility alias for taking the generator out of service."""

        self.take_out_of_service()

    # =================================================================
    # ACTIVE POWER
    # =================================================================

    @property
    def active_power_injection_mw(self) -> float:
        """
        Return effective active-power injection.

        An out-of-service generator contributes zero injection.
        """

        if not self.in_service:
            return 0.0

        return self.p_mw

    @property
    def active_power_mw(self) -> float:
        """Compatibility alias for effective active power."""

        return self.active_power_injection_mw

    def set_active_power(
        self,
        p_mw: float,
    ) -> None:
        """
        Set active-power injection.

        The value must remain within the configured active-power
        operating range.
        """

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
        """Compatibility alias for set_active_power()."""

        self.set_active_power(
            p_mw
        )

    # =================================================================
    # REACTIVE POWER
    # =================================================================

    @property
    def reactive_power_injection_mvar(self) -> float:
        """
        Return effective reactive-power injection.

        An out-of-service generator contributes zero injection.
        """

        if not self.in_service:
            return 0.0

        return self.q_mvar

    @property
    def reactive_power_mvar(self) -> float:
        """Compatibility alias for effective reactive power."""

        return self.reactive_power_injection_mvar

    def set_reactive_power(
        self,
        q_mvar: float,
    ) -> None:
        """
        Set reactive-power injection.

        If reactive limits are configured, the value must remain
        inside those limits.
        """

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
        """Compatibility alias for set_reactive_power()."""

        self.set_reactive_power(
            q_mvar
        )

    # =================================================================
    # POWER LIMITS
    # =================================================================

    def set_active_power_limits(
        self,
        p_min_mw: float,
        p_max_mw: float,
    ) -> None:
        """Set active-power operating limits."""

        p_min_mw = self._validate_finite(
            p_min_mw,
            "p_min_mw",
        )

        p_max_mw = self._validate_finite(
            p_max_mw,
            "p_max_mw",
        )

        if p_min_mw > p_max_mw:
            raise ValueError(
                "p_min_mw cannot be greater than p_max_mw."
            )

        self.p_min_mw = p_min_mw
        self.p_max_mw = p_max_mw

        self._validate_active_power(
            self.p_mw
        )

    def set_reactive_power_limits(
        self,
        q_min_mvar: float | None,
        q_max_mvar: float | None,
    ) -> None:
        """
        Set reactive-power operating limits.

        Passing None for both limits means unlimited reactive power.
        """

        if q_min_mvar is None:
            q_min = None
        else:
            q_min = self._validate_finite(
                q_min_mvar,
                "q_min_mvar",
            )

        if q_max_mvar is None:
            q_max = None
        else:
            q_max = self._validate_finite(
                q_max_mvar,
                "q_max_mvar",
            )

        if (
            q_min is not None
            and q_max is not None
            and q_min > q_max
        ):
            raise ValueError(
                "q_min_mvar cannot be greater than q_max_mvar."
            )

        self.q_min_mvar = q_min
        self.q_max_mvar = q_max

        self._validate_reactive_power(
            self.q_mvar
        )

    @property
    def active_power_headroom_mw(self) -> float:
        """Return remaining upward active-power headroom."""

        return max(
            0.0,
            self.p_max_mw - self.p_mw,
        )

    @property
    def active_power_reserve_mw(self) -> float:
        """Compatibility alias for active-power headroom."""

        return self.active_power_headroom_mw

    @property
    def reactive_power_headroom_mvar(self) -> float | None:
        """
        Return upward reactive-power headroom.

        None means no upper Q limit is configured.
        """

        if self.q_max_mvar is None:
            return None

        return max(
            0.0,
            self.q_max_mvar - self.q_mvar,
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
        Attach a dynamic-model reference.

        The Solar model does not execute the dynamic model.
        """

        if dynamic_model is None:
            raise ValueError(
                "dynamic_model cannot be None."
            )

        self.dynamic_model = dynamic_model

    def detach_dynamic_model(self) -> Any:
        """
        Detach and return the dynamic-model reference.
        """

        dynamic_model = self.dynamic_model
        self.dynamic_model = None
        return dynamic_model

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Solar-local engineering parameters.

        Network topology and numerical studies are deliberately
        excluded.
        """

        self.p_mw = self._validate_finite(
            self.p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            self.q_mvar,
            "q_mvar",
        )

        self.p_min_mw = self._validate_finite(
            self.p_min_mw,
            "p_min_mw",
        )

        self.p_max_mw = self._validate_finite(
            self.p_max_mw,
            "p_max_mw",
        )

        if self.p_min_mw > self.p_max_mw:
            raise ValueError(
                "p_min_mw cannot be greater than p_max_mw."
            )

        if self.q_min_mvar is not None:
            self.q_min_mvar = self._validate_finite(
                self.q_min_mvar,
                "q_min_mvar",
            )

        if self.q_max_mvar is not None:
            self.q_max_mvar = self._validate_finite(
                self.q_max_mvar,
                "q_max_mvar",
            )

        if (
            self.q_min_mvar is not None
            and self.q_max_mvar is not None
            and self.q_min_mvar > self.q_max_mvar
        ):
            raise ValueError(
                "q_min_mvar cannot be greater than q_max_mvar."
            )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        if self.terminal.owner is not self:
            raise ValueError(
                f"Solar '{self.id}' terminal ownership is invalid."
            )

        self._validate_active_power(
            self.p_mw
        )

        self._validate_reactive_power(
            self.q_mvar
        )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Solar model through the common
        ElectricalObject contract.
        """

        return super().validate()

    # =================================================================
    # POWER INJECTION
    # =================================================================

    def injection(self) -> tuple[float, float]:
        """
        Return effective P/Q injection.

        Returns
        -------
        tuple[float, float]
            (P_MW, Q_MVAr)

        Positive values represent injection into the network.
        """

        return (
            self.active_power_injection_mw,
            self.reactive_power_injection_mvar,
        )

    @property
    def p_injection_mw(self) -> float:
        """Return effective active-power injection."""

        return self.active_power_injection_mw

    @property
    def q_injection_mvar(self) -> float:
        """Return effective reactive-power injection."""

        return self.reactive_power_injection_mvar

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured Solar diagnostics."""

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

            "active_power_injection_mw":
                self.active_power_injection_mw,

            "reactive_power_injection_mvar":
                self.reactive_power_injection_mvar,

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
            f"<Solar "
            f"id={self.id}, "
            f"P={self.p_mw:.6f} MW, "
            f"Q={self.q_mvar:.6f} MVAr, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    def _validate_active_power(
        self,
        p_mw: float,
    ) -> None:
        """Validate active-power operating limits."""

        if p_mw < self.p_min_mw:
            raise ValueError(
                f"p_mw={p_mw} is below "
                f"p_min_mw={self.p_min_mw}."
            )

        if p_mw > self.p_max_mw:
            raise ValueError(
                f"p_mw={p_mw} exceeds "
                f"p_max_mw={self.p_max_mw}."
            )

    def _validate_reactive_power(
        self,
        q_mvar: float,
    ) -> None:
        """Validate configured reactive-power limits."""

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


__all__ = [
    "Solar",
]
