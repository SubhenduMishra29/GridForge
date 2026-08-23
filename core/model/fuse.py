# core/model/fuse.py
"""
GridForge V2 Fuse Model
=======================

Author:
    Subhendu Mishra

A fuse is a passive series protection device.

The fuse model represents the physical/electrical state of the
fuse element. Protection calculations, fault detection, network
topology management, and SLD representation remain outside this
model.

Architecture
------------

                 FUSE
          ┌─────────────────┐
          │                 │
    IN ───┤    Fuse Link    ├─── OUT
          │                 │
          └─────────────────┘

The fuse owns:

    - equipment identity
    - two electrical terminals
    - rated current
    - rated voltage
    - interrupting rating
    - service state
    - blown state
    - optional metadata

The fuse does NOT own:

    - network topology
    - Bus collections
    - fault calculations
    - short-circuit studies
    - relay logic
    - protection coordination
    - SLD state
    - GUI state
    - solver state
    - simulation state

State Semantics
---------------

A fuse conducts when:

    in_service == True
    AND
    blown == False

A blown fuse does not conduct.

Resetting a fuse changes only the fuse's local physical state.
It does not create or modify network topology.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# FUSE
# =====================================================================


class Fuse(ElectricalObject):
    """
    Static GridForge V2 fuse model.

    The fuse is a two-terminal passive series protection device.

    Its physical state is represented by:

        - in_service
        - blown

    The model does not perform protection calculations.
    """

    TYPE = "FUSE"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        rated_current_a: float = 1.0,
        rated_voltage_v: float = 1.0,
        interrupting_rating_ka: float = 0.0,
        in_service: bool = True,
        blown: bool = False,
    ) -> None:
        """
        Create a Fuse.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable equipment name.

        rated_current_a:
            Continuous rated current in amperes.

        rated_voltage_v:
            Maximum rated operating voltage in volts.

        interrupting_rating_ka:
            Maximum fault-current interrupting capability in kA.

        in_service:
            Whether the fuse is installed and in service.

        blown:
            Whether the fuse element has operated/opened.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # NAMEPLATE PARAMETERS
        # =============================================================

        self.rated_current_a = (
            self._validate_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

        self.rated_voltage_v = (
            self._validate_positive(
                rated_voltage_v,
                "rated_voltage_v",
            )
        )

        self.interrupting_rating_ka = (
            self._validate_non_negative(
                interrupting_rating_ka,
                "interrupting_rating_ka",
            )
        )

        # =============================================================
        # PHYSICAL STATE
        # =============================================================

        self.in_service = bool(in_service)
        self.blown = bool(blown)

        # =============================================================
        # ELECTRICAL TERMINALS
        # =============================================================

        self.from_terminal = Terminal(
            owner=self,
        )

        self.to_terminal = Terminal(
            owner=self,
        )

        self.validate_parameters()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """

        return self.TYPE

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the fuse's terminals in deterministic order.

        Order:

            from_terminal
            to_terminal
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    @property
    def input_terminal(self) -> Terminal:
        """
        Return the input-side terminal.

        Alias for ``from_terminal``.
        """

        return self.from_terminal

    @property
    def output_terminal(self) -> Terminal:
        """
        Return the output-side terminal.

        Alias for ``to_terminal``.
        """

        return self.to_terminal

    # =================================================================
    # PHYSICAL STATE
    # =================================================================

    @property
    def conducts(self) -> bool:
        """
        Return whether the fuse currently conducts.

        Conductivity requires both:

            in_service == True
            blown == False
        """

        return (
            self.in_service
            and not self.blown
        )

    @property
    def is_open(self) -> bool:
        """
        Return whether the fuse is electrically open.
        """

        return not self.conducts

    @property
    def is_blown(self) -> bool:
        """
        Return whether the fuse element has operated.
        """

        return self.blown

    # =================================================================
    # FUSE OPERATIONS
    # =================================================================

    def blow(self) -> None:
        """
        Operate the fuse element.

        This changes only the fuse's local physical state.

        It does not calculate the fault that caused the operation
        and does not modify network topology directly.
        """

        self.blown = True

    def reset(self) -> None:
        """
        Reset the fuse element.

        A reset fuse is conductive only if it is also in service.
        """

        self.blown = False

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the fuse service state.

        This does not modify network topology.
        """

        self.in_service = bool(in_service)

    def connect(self) -> None:
        """
        Place the fuse in service.
        """

        self.in_service = True

    def disconnect(self) -> None:
        """
        Remove the fuse from service.

        This does not change the blown state.
        """

        self.in_service = False

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def connected(self) -> bool:
        """
        Return whether both fuse terminals have endpoints.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate fuse-local engineering parameters.

        This does not validate network topology or fault studies.
        """

        self.rated_current_a = (
            self._validate_positive(
                self.rated_current_a,
                "rated_current_a",
            )
        )

        self.rated_voltage_v = (
            self._validate_positive(
                self.rated_voltage_v,
                "rated_voltage_v",
            )
        )

        self.interrupting_rating_ka = (
            self._validate_non_negative(
                self.interrupting_rating_ka,
                "interrupting_rating_ka",
            )
        )

        return True

    def validate(self) -> bool:
        """
        Public fuse validation entry point.
        """

        return self.validate_parameters()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return static fuse information and local state.

        No calculated fault or protection result is included.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "rated_current_a":
                self.rated_current_a,

            "rated_voltage_v":
                self.rated_voltage_v,

            "interrupting_rating_ka":
                self.interrupting_rating_ka,

            "in_service":
                self.in_service,

            "blown":
                self.blown,

            "conducts":
                self.conducts,

            "connected":
                self.connected,

            "from_endpoint":
                self._endpoint_id(
                    self.from_terminal
                ),

            "to_endpoint":
                self._endpoint_id(
                    self.to_terminal
                ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Fuse "
            f"id={self.id}, "
            f"rated_current="
            f"{self.rated_current_a:.3f}A, "
            f"rated_voltage="
            f"{self.rated_voltage_v:.3f}V, "
            f"blown={self.blown}, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # INTERNAL HELPERS
    # =================================================================

    @staticmethod
    def _validate_positive(
        value: float,
        field_name: str,
    ) -> float:
        """
        Validate and return a finite positive quantity.
        """

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if not isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{field_name} must be finite and "
                "greater than zero."
            )

        return value

    @staticmethod
    def _validate_non_negative(
        value: float,
        field_name: str,
    ) -> float:
        """
        Validate and return a finite non-negative quantity.
        """

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if not isfinite(value) or value < 0.0:
            raise ValueError(
                f"{field_name} must be finite and "
                "non-negative."
            )

        return value

    @staticmethod
    def _endpoint_id(
        terminal: Terminal,
    ) -> Any:
        """
        Safely return the terminal endpoint identifier.

        The Fuse does not impose a particular endpoint
        implementation on the Terminal contract.
        """

        endpoint = getattr(
            terminal,
            "endpoint",
            None,
        )

        if endpoint is None:
            return None

        return getattr(
            endpoint,
            "id",
            None,
        )


__all__ = [
    "Fuse",
]
