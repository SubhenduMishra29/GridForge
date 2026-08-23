```python
"""
GridForge V2 Generic Switch Model
=================================

Author:
    Subhendu Mishra

File:
    core/model/switch.py

Purpose
-------
Defines the canonical GridForge V2 generic two-terminal switching
element.

Architectural boundary
----------------------
Switch is a Core domain object.

It owns:

    - persistent identity
    - two electrical terminals
    - open/closed state
    - service state
    - normal operating-state metadata
    - basic electrical ratings

It does NOT own:

    - network topology
    - graph state
    - connection routing
    - SLD geometry
    - rendering
    - numerical admittance/impedance representation
    - power-flow solving
    - short-circuit solving
    - protection logic
    - relay coordination
    - GUI state

The Network layer interprets the switch state when constructing
electrical topology.

A closed switch means the electrical path is available.

An open switch means the electrical path is unavailable.

The Core model deliberately does not represent an open switch with
infinite impedance or a closed switch with infinite admittance.
Those are numerical concerns belonging to the Network/Solver layer.
"""

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Switch(ElectricalObject):
    """
    Generic two-terminal electrical switch.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    endpoint_a:
        Optional electrical endpoint for terminal A.

    endpoint_b:
        Optional electrical endpoint for terminal B.

    terminal_a:
        Optional existing Terminal for terminal A.

    terminal_b:
        Optional existing Terminal for terminal B.

    closed:
        Initial switching state.

    in_service:
        Whether the switch is available for network operation.

    normally_closed:
        Configured normal operating state.

    rated_voltage_kv:
        Optional nominal voltage rating.

    rated_current_a:
        Optional continuous current rating.

    bus_a:
        Backward-compatible alias for endpoint_a.

    bus_b:
        Backward-compatible alias for endpoint_b.
    """

    TYPE = "SWITCH"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint_a: Any = None,
        endpoint_b: Any = None,
        terminal_a: Terminal | None = None,
        terminal_b: Terminal | None = None,
        closed: bool = False,
        in_service: bool = True,
        normally_closed: bool | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        bus_a: Any = None,
        bus_b: Any = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # ENDPOINT COMPATIBILITY
        # =============================================================

        if endpoint_a is not None and bus_a is not None:
            if endpoint_a is not bus_a:
                raise ValueError(
                    f"Switch '{self.id}' received conflicting "
                    "endpoint_a and bus_a values."
                )

        if endpoint_b is not None and bus_b is not None:
            if endpoint_b is not bus_b:
                raise ValueError(
                    f"Switch '{self.id}' received conflicting "
                    "endpoint_b and bus_b values."
                )

        if endpoint_a is None:
            endpoint_a = bus_a

        if endpoint_b is None:
            endpoint_b = bus_b

        # =============================================================
        # TERMINALS
        # =============================================================

        if terminal_a is None:
            terminal_a = Terminal(
                endpoint=endpoint_a,
                owner=self,
            )
        else:
            self._validate_terminal(
                terminal_a,
                "terminal_a",
            )

            if (
                endpoint_a is not None
                and terminal_a.endpoint is not endpoint_a
            ):
                raise ValueError(
                    f"Switch '{self.id}' terminal_a and endpoint_a "
                    "refer to different endpoints."
                )

        if terminal_b is None:
            terminal_b = Terminal(
                endpoint=endpoint_b,
                owner=self,
            )
        else:
            self._validate_terminal(
                terminal_b,
                "terminal_b",
            )

            if (
                endpoint_b is not None
                and terminal_b.endpoint is not endpoint_b
            ):
                raise ValueError(
                    f"Switch '{self.id}' terminal_b and endpoint_b "
                    "refer to different endpoints."
                )

        if terminal_a is terminal_b:
            raise ValueError(
                f"Switch '{self.id}' cannot use the same Terminal "
                "instance for both terminals."
            )

        self.terminal_a = terminal_a
        self.terminal_b = terminal_b

        # =============================================================
        # SWITCH STATE
        # =============================================================

        self._validate_bool(
            closed,
            "closed",
        )

        self.closed = closed

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self._validate_bool(
            in_service,
            "in_service",
        )

        self.in_service = in_service

        # =============================================================
        # NORMAL STATE
        # =============================================================

        if normally_closed is None:
            normally_closed = closed

        self._validate_bool(
            normally_closed,
            "normally_closed",
        )

        self.normally_closed = normally_closed

        # =============================================================
        # ELECTRICAL RATINGS
        # =============================================================

        self.rated_voltage_kv = (
            None
            if rated_voltage_kv is None
            else self._validate_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.rated_current_a = (
            None
            if rated_current_a is None
            else self._validate_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

        # =============================================================
        # FINAL VALIDATION
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
    def terminals(self) -> tuple[Terminal, Terminal]:
        """Return the two authoritative electrical terminals."""

        return (
            self.terminal_a,
            self.terminal_b,
        )

    @property
    def endpoint_a(self) -> Any:
        """Return terminal-A endpoint."""

        return self.terminal_a.endpoint

    @property
    def endpoint_b(self) -> Any:
        """Return terminal-B endpoint."""

        return self.terminal_b.endpoint

    @property
    def bus_a(self) -> Any:
        """Backward-compatible terminal-A endpoint accessor."""

        return self.terminal_a.bus

    @property
    def bus_b(self) -> Any:
        """Backward-compatible terminal-B endpoint accessor."""

        return self.terminal_b.bus

    @property
    def is_connected(self) -> bool:
        """
        Return whether both terminals have electrical endpoints.
        """

        return (
            self.terminal_a.is_connected
            and self.terminal_b.is_connected
        )

    # =================================================================
    # TERMINAL CONNECTION
    # =================================================================

    def connect_endpoint_a(
        self,
        endpoint: Any,
    ) -> None:
        """Attach terminal A to an endpoint."""

        if endpoint is None:
            raise ValueError(
                f"Switch '{self.id}' endpoint_a cannot be None."
            )

        self.terminal_a.connect(
            endpoint
        )

    def connect_endpoint_b(
        self,
        endpoint: Any,
    ) -> None:
        """Attach terminal B to an endpoint."""

        if endpoint is None:
            raise ValueError(
                f"Switch '{self.id}' endpoint_b cannot be None."
            )

        self.terminal_b.connect(
            endpoint
        )

    def connect(
        self,
        endpoint_a: Any,
        endpoint_b: Any,
    ) -> None:
        """
        Attach both terminals.

        This establishes terminal references only.

        Network topology remains owned by core/network.
        """

        if endpoint_a is None:
            raise ValueError(
                f"Switch '{self.id}' endpoint_a cannot be None."
            )

        if endpoint_b is None:
            raise ValueError(
                f"Switch '{self.id}' endpoint_b cannot be None."
            )

        self.terminal_a.connect(
            endpoint_a
        )

        self.terminal_b.connect(
            endpoint_b
        )

    def disconnect_endpoint_a(self) -> None:
        """Detach terminal A."""

        self.terminal_a.disconnect()

    def disconnect_endpoint_b(self) -> None:
        """Detach terminal B."""

        self.terminal_b.disconnect()

    # =================================================================
    # SWITCH STATE
    # =================================================================

    @property
    def is_closed(self) -> bool:
        """Return True when the switch is closed."""

        return self.closed

    @property
    def is_open(self) -> bool:
        """Return True when the switch is open."""

        return not self.closed

    @property
    def conducts(self) -> bool:
        """
        Return whether the switch currently represents an active
        conductive path.

        This is a domain-state property.

        Network topology must interpret this state; this property
        does not modify Network.
        """

        return (
            self.in_service
            and self.closed
        )

    @property
    def electrically_closed(self) -> bool:
        """Return whether the switch is electrically conductive."""

        return self.conducts

    @property
    def electrically_open(self) -> bool:
        """Return whether the switch is electrically unavailable."""

        return not self.electrically_closed

    def open(self) -> None:
        """Open the switch."""

        self.closed = False

    def close(self) -> None:
        """Close the switch."""

        self.closed = True

    def toggle(self) -> None:
        """Toggle the switch state."""

        self.closed = not self.closed

    def set_closed(
        self,
        value: bool,
    ) -> None:
        """Set the switch state explicitly."""

        self._validate_bool(
            value,
            "closed",
        )

        self.closed = value

    # =================================================================
    # NORMAL STATE
    # =================================================================

    @property
    def is_normal_state(self) -> bool:
        """Return whether the current state is the normal state."""

        return self.closed == self.normally_closed

    @property
    def is_abnormal_state(self) -> bool:
        """Return whether the switch differs from its normal state."""

        return not self.is_normal_state

    def set_normally_closed(
        self,
        value: bool,
    ) -> None:
        """Set the configured normal operating state."""

        self._validate_bool(
            value,
            "normally_closed",
        )

        self.normally_closed = value

    def restore_normal_state(self) -> None:
        """Restore the configured normal switching state."""

        self.closed = self.normally_closed

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the switch is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the switch is out of service."""

        return not self.in_service

    @property
    def is_available(self) -> bool:
        """Return whether the switch is available."""

        return self.in_service

    def put_in_service(self) -> None:
        """Place the switch in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the switch out of service."""

        self.in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """Set service state explicitly."""

        self._validate_bool(
            value,
            "in_service",
        )

        self.in_service = value

    # =================================================================
    # CURRENT RATING
    # =================================================================

    @property
    def has_current_rating(self) -> bool:
        """Return whether a current rating is configured."""

        return self.rated_current_a is not None

    def validate_current(
        self,
        current_a: float,
    ) -> bool:
        """
        Check a current value against the configured continuous
        current rating.

        Returns True when no rating is configured.
        """

        current_a = self._validate_finite(
            current_a,
            "current_a",
        )

        if current_a < 0.0:
            raise ValueError(
                "current_a cannot be negative."
            )

        if self.rated_current_a is None:
            return True

        return (
            current_a
            <= self.rated_current_a + 1e-12
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """Validate switch-local engineering parameters."""

        self._validate_bool(
            self.closed,
            "closed",
        )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        self._validate_bool(
            self.normally_closed,
            "normally_closed",
        )

        if self.rated_voltage_kv is not None:
            self.rated_voltage_kv = self._validate_positive(
                self.rated_voltage_kv,
                "rated_voltage_kv",
            )

        if self.rated_current_a is not None:
            self.rated_current_a = self._validate_positive(
                self.rated_current_a,
                "rated_current_a",
            )

        self._validate_terminal(
            self.terminal_a,
            "terminal_a",
        )

        self._validate_terminal(
            self.terminal_b,
            "terminal_b",
        )

        if self.terminal_a is self.terminal_b:
            raise ValueError(
                f"Switch '{self.id}' cannot use the same Terminal "
                "instance for both terminals."
            )

        return True

    def validate(self) -> bool:
        """Validate through the common ElectricalObject contract."""

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured switch diagnostics."""

        endpoint_a_id = None
        endpoint_b_id = None

        if self.endpoint_a is not None:
            endpoint_a_id = getattr(
                self.endpoint_a,
                "id",
                self.endpoint_a,
            )

        if self.endpoint_b is not None:
            endpoint_b_id = getattr(
                self.endpoint_b,
                "id",
                self.endpoint_b,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "closed": self.closed,
            "open": self.is_open,
            "conducts": self.conducts,

            "in_service": self.in_service,
            "is_available": self.is_available,

            "normally_closed":
                self.normally_closed,

            "is_normal_state":
                self.is_normal_state,

            "rated_voltage_kv":
                self.rated_voltage_kv,

            "rated_current_a":
                self.rated_current_a,

            "endpoint_a":
                endpoint_a_id,

            "endpoint_b":
                endpoint_b_id,

            "is_connected":
                self.is_connected,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        state = (
            "closed"
            if self.closed
            else "open"
        )

        return (
            f"<Switch "
            f"id={self.id}, "
            f"state={state}, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    def _validate_terminal(
        self,
        terminal: Terminal,
        name: str,
    ) -> None:
        """Validate Terminal type and ownership."""

        if not isinstance(
            terminal,
            Terminal,
        ):
            raise TypeError(
                f"{name} must be a Terminal."
            )

        if terminal.owner is not self:
            raise ValueError(
                f"{name} owner must be this Switch."
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
    "Switch",
]
```
