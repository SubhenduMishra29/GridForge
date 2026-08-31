# ============================================================
# File: core/model/solar.py
# GridForge V2 — Solar Generator Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Solar Generator Model
==================================

Canonical static solar generation / injection model.

Architectural responsibility
----------------------------

Solar owns:

    - identity
    - electrical operating point
    - active/reactive power limits
    - operating state
    - one authoritative Terminal
    - optional dynamic-model metadata

Solar does NOT own:

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

    P < 0  -> active-power absorption
    Q < 0  -> reactive-power absorption

Terminal contract
-----------------

The Solar model owns exactly one authoritative Terminal:

    Terminal
    ├── owner
    ├── role
    ├── endpoint
    ├── attach()
    ├── detach()
    ├── is_connected
    └── validate()

The Terminal is the sole owner of endpoint connectivity.

Electrical connectivity and service state are separate.

    connect_endpoint(endpoint)
        -> Terminal.attach(endpoint)

    disconnect_endpoint()
        -> Terminal.detach()

while:

    put_in_service()
    take_out_of_service()

modify only operating state.

The Network layer owns network topology.

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
    Static solar generation / injection model.

    Positive P/Q values represent injection into the network.
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
        terminal: Terminal | None = None,
        dynamic_model: Any = None,
    ) -> None:
        """
        Construct a Solar generator.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable name.

        endpoint:
            Initial electrical endpoint.

        p_mw:
            Active-power injection in MW.

        q_mvar:
            Reactive-power injection in MVAr.

        p_max_mw:
            Maximum active-power output.

        p_min_mw:
            Minimum active-power output.

        q_max_mvar:
            Maximum reactive-power injection.

        q_min_mvar:
            Minimum reactive-power injection.

        in_service:
            Whether the Solar generator is operational.

        bus:
            Backward-compatible endpoint alias.

        terminal:
            Optional pre-created authoritative Terminal.

        dynamic_model:
            Optional dynamic-model reference or metadata.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # ========================================================
        # ENDPOINT COMPATIBILITY
        # ========================================================

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Solar '{self.id}' received both endpoint and "
                "bus with different values."
            )

        if endpoint is None:
            endpoint = bus

        # ========================================================
        # POWER STATE
        # ========================================================

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

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

        # ========================================================
        # SERVICE STATE
        # ========================================================

        self._validate_bool(
            in_service,
            "in_service",
        )

        self.in_service = in_service

        # ========================================================
        # AUTHORITATIVE TERMINAL
        # ========================================================

        if terminal is None:
            self._terminal = Terminal(
                owner=self,
                role="terminal",
            )
        else:
            if not isinstance(
                terminal,
                Terminal,
            ):
                raise TypeError(
                    "terminal must be a Terminal."
                )

            if terminal.owner is not self:
                raise ValueError(
                    f"Solar '{self.id}' terminal owner must "
                    "be this Solar."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "Solar terminal role must be 'terminal'."
                )

            self._terminal = terminal

        # ========================================================
        # INITIAL ENDPOINT ATTACHMENT
        # ========================================================

        if endpoint is not None:
            self._terminal.attach(
                endpoint
            )

        # ========================================================
        # OPTIONAL DYNAMIC MODEL REFERENCE
        # ========================================================

        self.dynamic_model = dynamic_model

        # ========================================================
        # COMMON MODEL VALIDATION
        # ========================================================

        self.validate()

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # ============================================================
    # TERMINALS
    # ============================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative Solar Terminal.

        The private _terminal attribute remains the authoritative
        storage location.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Solar terminal collection."""

        return (
            self._terminal,
        )

    @property
    def endpoint(self) -> Any:
        """
        Return the authoritative electrical endpoint.

        Endpoint state is derived exclusively from Terminal.
        """

        return self._terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor for the historical bus API.

        The Terminal remains authoritative.
        """

        return self._terminal.endpoint

    @property
    def is_connected(self) -> bool:
        """Return whether the Solar terminal is connected."""

        return self._terminal.is_connected

    # ============================================================
    # ENDPOINT CONNECTIVITY
    # ============================================================

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach the Solar Terminal to an electrical endpoint.

        This changes Terminal connectivity only.
        Network topology remains owned by Network.
        """

        if endpoint is None:
            raise ValueError(
                f"Solar '{self.id}' endpoint cannot be None."
            )

        self._terminal.attach(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Detach the Solar Terminal.

        This does not change service state.
        """

        self._terminal.detach()

    # ============================================================
    # SERVICE STATE
    # ============================================================

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
        """
        Return whether the Solar generator is operationally
        available.
        """

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
        """Set service state without boolean coercion."""

        self._validate_bool(
            value,
            "in_service",
        )

        self.in_service = value

    # ------------------------------------------------------------
    # Compatibility aliases
    # ------------------------------------------------------------

    def connect(self) -> None:
        """
        Compatibility alias for putting the generator in service.

        This is NOT an electrical Terminal connection operation.
        """

        self.put_in_service()

    def disconnect(self) -> None:
        """
        Compatibility alias for taking the generator out of
        service.

        This is NOT an electrical Terminal disconnection
        operation.
        """

        self.take_out_of_service()

    def close(self) -> None:
        """Compatibility alias for put_in_service()."""

        self.put_in_service()

    def trip(self) -> None:
        """Compatibility alias for take_out_of_service()."""

        self.take_out_of_service()

    # ============================================================
    # ACTIVE POWER
    # ============================================================

    @property
    def active_power_injection_mw(self) -> float:
        """
        Return effective active-power injection.

        Out-of-service Solar contributes zero injection.
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

        The value must remain inside configured limits.
        """

        value = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self._validate_active_power(
            value
        )

        self.p_mw = value

    def set_p(
        self,
        p_mw: float,
    ) -> None:
        """Compatibility alias for set_active_power()."""

        self.set_active_power(
            p_mw
        )

    # ============================================================
    # REACTIVE POWER
    # ============================================================

    @property
    def reactive_power_injection_mvar(self) -> float:
        """
        Return effective reactive-power injection.

        Out-of-service Solar contributes zero injection.
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

        The value must remain inside configured limits.
        """

        value = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        self._validate_reactive_power(
            value
        )

        self.q_mvar = value

    def set_q(
        self,
        q_mvar: float,
    ) -> None:
        """Compatibility alias for set_reactive_power()."""

        self.set_reactive_power(
            q_mvar
        )

    # ============================================================
    # POWER LIMITS
    # ============================================================

    def set_active_power_limits(
        self,
        p_min_mw: float,
        p_max_mw: float,
    ) -> None:
        """Set active-power operating limits."""

        p_min = self._validate_finite(
            p_min_mw,
            "p_min_mw",
        )

        p_max = self._validate_finite(
            p_max_mw,
            "p_max_mw",
        )

        if p_min > p_max:
            raise ValueError(
                "p_min_mw cannot be greater than p_max_mw."
            )

        if not (
            p_min <= self.p_mw <= p_max
        ):
            raise ValueError(
                "Existing p_mw is outside the new "
                "active-power limits."
            )

        self.p_min_mw = p_min
        self.p_max_mw = p_max

    def set_reactive_power_limits(
        self,
        q_min_mvar: float | None,
        q_max_mvar: float | None,
    ) -> None:
        """
        Set reactive-power operating limits.

        None represents an unbounded limit.
        """

        q_min = (
            None
            if q_min_mvar is None
            else self._validate_finite(
                q_min_mvar,
                "q_min_mvar",
            )
        )

        q_max = (
            None
            if q_max_mvar is None
            else self._validate_finite(
                q_max_mvar,
                "q_max_mvar",
            )
        )

        if (
            q_min is not None
            and q_max is not None
            and q_min > q_max
        ):
            raise ValueError(
                "q_min_mvar cannot be greater than "
                "q_max_mvar."
            )

        if (
            q_min is not None
            and self.q_mvar < q_min
        ):
            raise ValueError(
                "Existing q_mvar is below the new "
                "reactive-power minimum."
            )

        if (
            q_max is not None
            and self.q_mvar > q_max
        ):
            raise ValueError(
                "Existing q_mvar exceeds the new "
                "reactive-power maximum."
            )

        self.q_min_mvar = q_min
        self.q_max_mvar = q_max

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

        None means no upper reactive-power limit is configured.
        """

        if self.q_max_mvar is None:
            return None

        return max(
            0.0,
            self.q_max_mvar - self.q_mvar,
        )

    # ============================================================
    # INJECTION CONTRACT
    # ============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return effective network injection.

        Positive values represent injection into the network.
        """

        return (
            self.active_power_injection_mw,
            self.reactive_power_injection_mvar,
        )

    def injection(self) -> tuple[float, float]:
        """Compatibility alias for get_power()."""

        return self.get_power()

    @property
    def p_injection_mw(self) -> float:
        """Return effective active-power injection."""

        return self.active_power_injection_mw

    @property
    def q_injection_mvar(self) -> float:
        """Return effective reactive-power injection."""

        return self.reactive_power_injection_mvar

    # ============================================================
    # DYNAMIC MODEL REFERENCE
    # ============================================================

    @property
    def has_dynamic_model(self) -> bool:
        """Return whether dynamic-model metadata is present."""

        return self.dynamic_model is not None

    def attach_dynamic_model(
        self,
        dynamic_model: Any,
    ) -> None:
        """
        Attach dynamic-model metadata/reference.

        Execution remains outside the Solar model.
        """

        if dynamic_model is None:
            raise ValueError(
                "dynamic_model cannot be None."
            )

        self.dynamic_model = dynamic_model

    def detach_dynamic_model(self) -> Any:
        """Detach and return dynamic-model metadata/reference."""

        dynamic_model = self.dynamic_model
        self.dynamic_model = None
        return dynamic_model

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Solar-local engineering invariants.

        Network topology is intentionally excluded.
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
                "q_min_mvar cannot be greater than "
                "q_max_mvar."
            )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        self._validate_active_power(
            self.p_mw
        )

        self._validate_reactive_power(
            self.q_mvar
        )

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Solar terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Solar '{self.id}' terminal owner must "
                "be this Solar."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "Solar terminal role must be 'terminal'."
            )

        self._terminal.validate()

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """Return structured Solar diagnostics."""

        endpoint = self._terminal.endpoint

        endpoint_id = (
            getattr(
                endpoint,
                "id",
                endpoint,
            )
            if endpoint is not None
            else None
        )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal,

            "endpoint": endpoint_id,
            "bus": endpoint_id,
            "is_connected":
                self._terminal.is_connected,

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

            "in_service":
                self.in_service,

            "is_available":
                self.is_available,

            "has_dynamic_model":
                self.has_dynamic_model,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Solar "
            f"id={self.id}, "
            f"P={self.p_mw:.6f} MW, "
            f"Q={self.q_mvar:.6f} MVAr, "
            f"in_service={self.in_service}>"
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Validate and return a finite numeric value."""

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

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """Validate a strict boolean."""

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )

        return value

    def _validate_active_power(
        self,
        value: float,
    ) -> None:
        """Validate active power against configured limits."""

        if value < self.p_min_mw:
            raise ValueError(
                f"p_mw={value} is below "
                f"p_min_mw={self.p_min_mw}."
            )

        if value > self.p_max_mw:
            raise ValueError(
                f"p_mw={value} exceeds "
                f"p_max_mw={self.p_max_mw}."
            )

    def _validate_reactive_power(
        self,
        value: float,
    ) -> None:
        """Validate reactive power against configured limits."""

        if (
            self.q_min_mvar is not None
            and value < self.q_min_mvar
        ):
            raise ValueError(
                f"q_mvar={value} is below "
                f"q_min_mvar={self.q_min_mvar}."
            )

        if (
            self.q_max_mvar is not None
            and value > self.q_max_mvar
        ):
            raise ValueError(
                f"q_mvar={value} exceeds "
                f"q_max_mvar={self.q_max_mvar}."
            )


__all__ = [
    "Solar",
]
