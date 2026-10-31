# ============================================================
# File: core/model/generator.py
# GridForge V2 — Generator Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Generator Model
==============================

Authoritative electrical-domain model for a controllable
generator / power-injection element.

Architecture
------------

    ElectricalObject
          +
      Injection
          |
          v
      Generator
          |
          v
       Terminal
          |
          v
    Terminal.endpoint

The Generator owns:

    - generator identity
    - active/reactive power state
    - voltage setpoint
    - reactive-power limits
    - one authoritative Terminal
    - operational state
    - optional plugin references

The Generator does NOT own:

    - Network registration
    - global topology
    - Bus state
    - Y-Bus construction
    - power-flow solving
    - fault analysis
    - protection
    - dynamics
    - UI/SLD state

Terminal Contract
-----------------

The canonical Terminal contract is:

    Terminal
    ├── owner
    ├── role
    ├── endpoint
    ├── attach()
    ├── detach()
    ├── is_connected
    └── validate()

Therefore:

    connect(endpoint) -> Terminal.attach(endpoint)
    disconnect()      -> Terminal.detach()

The Generator never maintains a duplicate endpoint/bus
reference.

The ``endpoint`` property is derived from Terminal state.

The ``bus`` property is retained only as a read-only
compatibility accessor.

Operational State
-----------------

Electrical connectivity and operational state are distinct.

    connect(endpoint)
        -> establishes terminal connectivity

    disconnect()
        -> removes terminal connectivity

    put_in_service()
        -> changes operational state

    take_out_of_service()
        -> changes operational state

Power convention
----------------

Generator injection into the electrical network is:

    P > 0  -> active power injection
    Q > 0  -> reactive power injection

Therefore:

    get_power() -> (P, Q)

Reactive-power limits
---------------------

The Generator may locally enforce:

    Qmin <= Q <= Qmax

PV/PQ operating-mode decisions belong to the
analysis/control layer, not to this model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Generator(ElectricalObject, Injection):
    """
    Controllable electrical generator model.

    A Generator may exist before being connected to a network.

    The Generator has exactly one authoritative electrical
    Terminal.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint:
        Initial electrical endpoint. May be None.

    p:
        Active power injection.

    q:
        Reactive power injection.

    V_setpoint:
        Generator voltage setpoint in per-unit.

    q_limits:
        Tuple ``(Qmin, Qmax)``.

    name:
        Human-readable generator name.

    bus:
        Backward-compatible alias for endpoint.

    in_service:
        Initial operational state.
    """

    TYPE = "GENERATOR"

    def __init__(
        self,
        id: str,
        endpoint: Any = None,
        p: float = 0.0,
        q: float = 0.0,
        V_setpoint: float = 1.0,
        q_limits: tuple[float, float] = (
            -float("inf"),
            float("inf"),
        ),
        name: str = "",
        *,
        bus: Any = None,
        terminal: Terminal | None = None,
        in_service: bool = True,
        z1_subtransient_pu: complex | None = None,
        z2_pu: complex | None = None,
        z0_pu: complex | None = None,
        impedance_base_mva: float | None = None,
        impedance_base_voltage_kv: float | None = None,
        short_circuit_internal_voltage_pu: float | None = None,
        short_circuit_internal_angle_deg: float = 0.0,
        neutral_grounded: bool = False,
        neutral_grounding_impedance_ohm: complex | None = None,
    ) -> None:
        """
        Construct a Generator.

        Endpoint mutation is performed exclusively through the
        authoritative Terminal.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint:
            Initial electrical endpoint.

        p:
            Active power injection.

        q:
            Reactive power injection.

        V_setpoint:
            Voltage setpoint in per-unit.

        q_limits:
            Reactive-power limits ``(Qmin, Qmax)``.

        name:
            Human-readable name.

        bus:
            Compatibility alias for endpoint.

        terminal:
            Optional pre-created Terminal owned by this Generator.

        in_service:
            Initial operational state.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Endpoint / compatibility handling
        # --------------------------------------------------------

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Generator '{self.id}' received both "
                "'endpoint' and 'bus' with different values."
            )

        if endpoint is None:
            endpoint = bus

        # --------------------------------------------------------
        # Electrical state
        # --------------------------------------------------------

        self.p = self._validate_finite(
            p,
            "p",
        )

        self.q = self._validate_finite(
            q,
            "q",
        )

        self.V_setpoint = self._validate_positive(
            V_setpoint,
            "V_setpoint",
        )

        self.q_min, self.q_max = self._validate_q_limits(
            q_limits
        )

        self._validate_q_value(
            self.q,
            self.q_min,
            self.q_max,
        )

        # --------------------------------------------------------
        # Authoritative Terminal
        # --------------------------------------------------------

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
                    f"Generator '{self.id}' terminal owner "
                    "must be this Generator."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "Generator terminal role must be "
                    "'terminal'."
                )

            self._terminal = terminal

        # --------------------------------------------------------
        # Initial physical connection
        # --------------------------------------------------------

        if endpoint is not None:
            self._terminal.attach(
                endpoint
            )

        # --------------------------------------------------------
        # Operational state
        # --------------------------------------------------------

        self.in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        # Explicit short-circuit construction data. Load-flow P/Q and
        # V_setpoint are deliberately not substituted for machine data.
        self.z1_subtransient_pu = self._validate_optional_complex_impedance(
            z1_subtransient_pu, "z1_subtransient_pu"
        )
        self.z2_pu = self._validate_optional_complex_impedance(z2_pu, "z2_pu")
        self.z0_pu = self._validate_optional_complex_impedance(z0_pu, "z0_pu")
        self.impedance_base_mva = self._validate_optional_positive(
            impedance_base_mva, "impedance_base_mva"
        )
        self.impedance_base_voltage_kv = self._validate_optional_positive(
            impedance_base_voltage_kv, "impedance_base_voltage_kv"
        )
        self.short_circuit_internal_voltage_pu = self._validate_optional_positive(
            short_circuit_internal_voltage_pu, "short_circuit_internal_voltage_pu"
        )
        self.short_circuit_internal_angle_deg = self._validate_finite(
            short_circuit_internal_angle_deg, "short_circuit_internal_angle_deg"
        )
        self.neutral_grounded = self._validate_bool(neutral_grounded, "neutral_grounded")
        self.neutral_grounding_impedance_ohm = self._validate_optional_complex_impedance(
            neutral_grounding_impedance_ohm, "neutral_grounding_impedance_ohm",
            allow_zero=True
        )
        self._validate_short_circuit_contract()

        # --------------------------------------------------------
        # Optional plugin references
        # --------------------------------------------------------

        self._plugins: dict[str, Any] = {}

        self.validate()

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
    # TERMINAL
    # ============================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative Generator Terminal.

        The Terminal object is returned for domain inspection
        and controlled terminal operations. Endpoint ownership
        remains exclusively inside Terminal.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return all Generator terminals.

        Generator has exactly one electrical terminal.
        """

        return (
            self._terminal,
        )

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    @property
    def endpoint(self) -> Any | None:
        """
        Return the authoritative physical endpoint.

        Terminal.endpoint is the source of truth.
        """

        return self._terminal.endpoint

    @property
    def bus(self) -> Any | None:
        """
        Compatibility accessor for the terminal endpoint.

        This is derived state and is never authoritative.
        """

        return self._terminal.endpoint

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Generator terminal is connected.
        """

        return self._terminal.is_connected

    def connect(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the Generator terminal to an endpoint.

        This operation changes electrical connectivity only.
        It does not change operational service state.
        """

        if endpoint is None:
            raise ValueError(
                f"Generator '{self.id}' endpoint "
                "cannot be None."
            )

        self._terminal.attach(
            endpoint
        )

    def disconnect(self) -> None:
        """
        Disconnect the Generator terminal.

        This operation changes electrical connectivity only.
        It does not change operational service state.
        """

        self._terminal.detach()

    # ============================================================
    # INJECTION CONTRACT
    # ============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network power injection.

        Positive values represent injection into the network.

        Returns
        -------
        tuple[float, float]
            ``(P, Q)``
        """

        if not self.in_service:
            return (
                0.0,
                0.0,
            )

        return (
            self.p,
            self.q,
        )

    # ============================================================
    # POWER CONTROL
    # ============================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set active and reactive power.

        The requested Q must remain within the configured
        local Q limits.
        """

        p_value = self._validate_finite(
            p,
            "p",
        )

        q_value = self._validate_finite(
            q,
            "q",
        )

        self._validate_q_value(
            q_value,
            self.q_min,
            self.q_max,
        )

        self.p = p_value
        self.q = q_value

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """
        Set active power injection.
        """

        self.p = self._validate_finite(
            p,
            "p",
        )

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set reactive power injection.

        The value must remain within Q limits.
        """

        q_value = self._validate_finite(
            q,
            "q",
        )

        self._validate_q_value(
            q_value,
            self.q_min,
            self.q_max,
        )

        self.q = q_value

    @property
    def active_power(self) -> float:
        """
        Return active power injection.
        """

        return self.p

    @property
    def reactive_power(self) -> float:
        """
        Return reactive power injection.
        """

        return self.q

    # ============================================================
    # VOLTAGE CONTROL
    # ============================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float,
    ) -> None:
        """
        Set generator voltage setpoint.
        """

        self.V_setpoint = self._validate_positive(
            V_setpoint,
            "V_setpoint",
        )

    # ============================================================
    # REACTIVE POWER LIMITS
    # ============================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """
        Return ``(Qmin, Qmax)``.
        """

        return (
            self.q_min,
            self.q_max,
        )

    def set_q_limits(
        self,
        q_min: float,
        q_max: float,
    ) -> None:
        """
        Set generator reactive-power limits.

        The existing Generator operating point must remain
        inside the new limits.
        """

        new_min, new_max = self._validate_q_limits(
            (
                q_min,
                q_max,
            )
        )

        self._validate_q_value(
            self.q,
            new_min,
            new_max,
        )

        self.q_min = new_min
        self.q_max = new_max

    def q_limit_status(
        self,
        tolerance: float = 1e-6,
    ) -> str:
        """
        Return current reactive-power limit status.

        Returns
        -------
        str
            ``LOW``, ``HIGH`` or ``NORMAL``.
        """

        tolerance = self._validate_non_negative(
            tolerance,
            "tolerance",
        )

        if self.q < self.q_min - tolerance:
            return "LOW"

        if self.q > self.q_max + tolerance:
            return "HIGH"

        return "NORMAL"

    def enforce_q_limits(self) -> bool:
        """
        Clamp reactive power to the configured Q limits.

        Returns
        -------
        bool
            True when Q was changed.

        This method does not determine PV/PQ operating mode.
        """

        old_q = self.q

        self.q = min(
            max(
                self.q,
                self.q_min,
            ),
            self.q_max,
        )

        return self.q != old_q

    # ============================================================
    # OPERATIONAL STATE
    # ============================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the Generator is in service.
        """

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the Generator is out of service.
        """

        return not self.in_service

    def put_in_service(self) -> None:
        """
        Place Generator in service.

        This does not alter terminal connectivity.
        """

        self.in_service = True

    def take_out_of_service(self) -> None:
        """
        Remove Generator from service.

        This does not alter terminal connectivity.
        """

        self.in_service = False

    def close(self) -> None:
        """
        Compatibility alias for putting Generator in service.

        This does not connect the electrical Terminal.
        """

        self.put_in_service()

    def trip(self) -> None:
        """
        Compatibility alias for taking Generator out of service.

        This does not disconnect the electrical Terminal.
        """

        self.take_out_of_service()

    # ============================================================
    # PLUGIN REFERENCES
    # ============================================================

    def attach_plugin(
        self,
        key: str,
        plugin: Any,
    ) -> None:
        """
        Attach a plugin reference.

        Plugin execution remains outside the Generator model.
        """

        if not isinstance(
            key,
            str,
        ) or not key.strip():
            raise ValueError(
                "Generator plugin key must be "
                "a non-empty string."
            )

        if plugin is None:
            raise ValueError(
                "Generator plugin cannot be None."
            )

        self._plugins[key] = plugin

    def get_plugin(
        self,
        key: str,
    ) -> Any | None:
        """
        Return a plugin reference if present.
        """

        return self._plugins.get(
            key
        )

    def has_plugin(
        self,
        key: str,
    ) -> bool:
        """
        Return True when the plugin exists.
        """

        return key in self._plugins

    def detach_plugin(
        self,
        key: str,
    ) -> Any | None:
        """
        Remove and return a plugin reference.
        """

        return self._plugins.pop(
            key,
            None,
        )


    @staticmethod
    def _validate_optional_complex_impedance(value: complex | None, name: str, *, allow_zero: bool = False) -> complex | None:
        if value is None:
            return None
        if isinstance(value, bool):
            raise TypeError(f"{name} must be a finite complex impedance.")
        try:
            result = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a finite complex impedance.") from exc
        if not math.isfinite(result.real) or not math.isfinite(result.imag) or result.real < 0.0:
            raise ValueError(f"{name} must be finite with non-negative resistance.")
        if not allow_zero and result == 0j:
            raise ValueError(f"{name} must be non-zero when supplied.")
        return result

    def _validate_short_circuit_contract(self) -> None:
        sequence_data = any(value is not None for value in (self.z1_subtransient_pu, self.z2_pu, self.z0_pu))
        if not sequence_data:
            if any(value is not None for value in (self.impedance_base_mva, self.impedance_base_voltage_kv, self.short_circuit_internal_voltage_pu)):
                raise ValueError("Generator short-circuit bases/internal voltage require declared sequence impedance data.")
        else:
            if self.z1_subtransient_pu is None:
                raise ValueError("Generator sequence data requires positive-sequence subtransient impedance z1_subtransient_pu.")
            if self.impedance_base_mva is None or self.impedance_base_voltage_kv is None:
                raise ValueError("Generator sequence impedances require explicit impedance_base_mva and impedance_base_voltage_kv.")
            if self.short_circuit_internal_voltage_pu is None:
                raise ValueError("Generator sequence impedances require explicit short_circuit_internal_voltage_pu; V_setpoint is not a substitute.")
        if self.neutral_grounded and self.neutral_grounding_impedance_ohm is None:
            raise ValueError("A grounded Generator neutral requires explicit neutral_grounding_impedance_ohm; use 0j for solid grounding.")
        if not self.neutral_grounded and self.neutral_grounding_impedance_ohm is not None:
            raise ValueError("neutral_grounding_impedance_ohm is invalid unless neutral_grounded is true.")

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Generator-local invariants.

        Network topology is deliberately not resolved here.
        """

        self.p = self._validate_finite(
            self.p,
            "p",
        )

        self.q = self._validate_finite(
            self.q,
            "q",
        )

        self.V_setpoint = self._validate_positive(
            self.V_setpoint,
            "V_setpoint",
        )

        self.q_min, self.q_max = self._validate_q_limits(
            (
                self.q_min,
                self.q_max,
            )
        )

        self._validate_q_value(
            self.q,
            self.q_min,
            self.q_max,
        )

        self.in_service = self._validate_bool(
            self.in_service,
            "in_service",
        )
        self.z1_subtransient_pu = self._validate_optional_complex_impedance(self.z1_subtransient_pu, "z1_subtransient_pu")
        self.z2_pu = self._validate_optional_complex_impedance(self.z2_pu, "z2_pu")
        self.z0_pu = self._validate_optional_complex_impedance(self.z0_pu, "z0_pu")
        self.impedance_base_mva = self._validate_optional_positive(self.impedance_base_mva, "impedance_base_mva")
        self.impedance_base_voltage_kv = self._validate_optional_positive(self.impedance_base_voltage_kv, "impedance_base_voltage_kv")
        self.short_circuit_internal_voltage_pu = self._validate_optional_positive(self.short_circuit_internal_voltage_pu, "short_circuit_internal_voltage_pu")
        self.short_circuit_internal_angle_deg = self._validate_finite(self.short_circuit_internal_angle_deg, "short_circuit_internal_angle_deg")
        self.neutral_grounded = self._validate_bool(self.neutral_grounded, "neutral_grounded")
        self.neutral_grounding_impedance_ohm = self._validate_optional_complex_impedance(self.neutral_grounding_impedance_ohm, "neutral_grounding_impedance_ohm", allow_zero=True)
        self._validate_short_circuit_contract()

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Generator terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Generator '{self.id}' terminal owner "
                "must be this Generator."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "Generator terminal role must be "
                "'terminal'."
            )

        self._terminal.validate()

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Generator diagnostics.
        """

        endpoint = self._terminal.endpoint

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal,

            "endpoint": (
                endpoint.id
                if endpoint is not None
                and hasattr(endpoint, "id")
                else endpoint
            ),

            "bus": (
                endpoint.id
                if endpoint is not None
                and hasattr(endpoint, "id")
                else endpoint
            ),

            "p": self.p,
            "q": self.q,
            "V_setpoint": self.V_setpoint,

            "q_min": self.q_min,
            "q_max": self.q_max,
            "q_limit_status":
                self.q_limit_status(),

            "is_connected":
                self._terminal.is_connected,

            "in_service":
                self.in_service,

            "z1_subtransient_pu": self.z1_subtransient_pu,
            "z2_pu": self.z2_pu,
            "z0_pu": self.z0_pu,
            "impedance_base_mva": self.impedance_base_mva,
            "impedance_base_voltage_kv": self.impedance_base_voltage_kv,
            "short_circuit_internal_voltage_pu": self.short_circuit_internal_voltage_pu,
            "short_circuit_internal_angle_deg": self.short_circuit_internal_angle_deg,
            "neutral_grounded": self.neutral_grounded,
            "neutral_grounding_impedance_ohm": self.neutral_grounding_impedance_ohm,

            "injection":
                self.get_power(),

            "plugin_count":
                len(self._plugins),
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        endpoint = self._terminal.endpoint

        endpoint_id = (
            endpoint.id
            if endpoint is not None
            and hasattr(endpoint, "id")
            else endpoint
        )

        return (
            f"<Generator "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"V={self.V_setpoint:.6f}, "
            f"Qlim=({self.q_min}, {self.q_max}), "
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
        """
        Convert a value to float and require it to be finite.
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
        Return a finite value greater than zero.
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
        Return a finite non-negative value.
        """

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric < 0.0:
            raise ValueError(
                f"{name} must be greater than or equal "
                "to zero."
            )

        return numeric

    @classmethod
    def _validate_q_limits(
        cls,
        q_limits: tuple[float, float],
    ) -> tuple[float, float]:
        """
        Validate reactive-power limits.

        Infinite Q limits are permitted.
        """

        if (
            not isinstance(q_limits, (tuple, list))
            or len(q_limits) != 2
        ):
            raise ValueError(
                "q_limits must contain exactly "
                "(q_min, q_max)."
            )

        try:
            q_min = float(q_limits[0])
            q_max = float(q_limits[1])
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "q_limits values must be numeric."
            ) from exc

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                "q_limits cannot contain NaN."
            )

        if q_min > q_max:
            raise ValueError(
                "q_min must be less than or equal to q_max."
            )

        return (
            q_min,
            q_max,
        )

    @classmethod
    def _validate_q_value(
        cls,
        q: float,
        q_min: float,
        q_max: float,
        tolerance: float = 1e-9,
    ) -> float:
        """
        Validate Q against the supplied limits.

        A small numerical tolerance is permitted.
        """

        q = cls._validate_finite(
            q,
            "q",
        )

        if (
            q < q_min - tolerance
            or q > q_max + tolerance
        ):
            raise ValueError(
                "q must be within q_limits."
            )

        return q

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a strict boolean.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Generator",
]
