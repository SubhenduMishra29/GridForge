"""
GridForge V2 Reactor Model
Author: Subhendu Mishra
"""
# GridForge/core/model/reactor.py

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Reactor(ElectricalObject, Injection):
    """
    Shunt reactor model.

    Negative reactive power represents absorption from the network.
    """

    TYPE = "REACTOR"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        terminal: Terminal | None = None,
        reactive_power_injection_mvar: float = 0.0,
        bus: Any = None,
        in_service: bool = True,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )

        self.terminal = (
            terminal
            if terminal is not None
            else Terminal(
                endpoint=bus,
                owner=self,
            )
        )

        if not isinstance(self.terminal, Terminal):
            raise TypeError("terminal must be a Terminal.")

        if self.terminal.owner is not self:
            raise ValueError(
                "terminal owner must be this Reactor."
            )

        self.reactive_power_injection_mvar = float(
            reactive_power_injection_mvar
        )

        if self.reactive_power_injection_mvar > 0.0:
            raise ValueError(
                "Reactor reactive_power_injection_mvar "
                "must be zero or negative."
            )

        if not isinstance(in_service, bool):
            raise TypeError("in_service must be boolean.")

        self.in_service = in_service

        self.validate()

    @property
    def element_type(self) -> str:
        return self.TYPE

    @property
    def terminals(self) -> tuple[Terminal]:
        return (self.terminal,)

    @property
    def bus(self) -> Any:
        return self.terminal.endpoint

    @property
    def q_injection_mvar(self) -> float:
        return self.reactive_power_injection_mvar

    @property
    def reactive_power_mvar(self) -> float:
        return self.reactive_power_injection_mvar

    @property
    def conducts(self) -> bool:
        return self.in_service

    def get_power(self) -> tuple[float, float]:
        """Return active and reactive network injection."""

        if not self.in_service:
            return (0.0, 0.0)

        return (
            0.0,
            self.reactive_power_injection_mvar,
        )

    def validate_parameters(self) -> bool:
        if not isinstance(self.terminal, Terminal):
            raise TypeError("terminal must be a Terminal.")

        if self.terminal.owner is not self:
            raise ValueError(
                "terminal owner must be this Reactor."
            )

        if not isinstance(self.in_service, bool):
            raise TypeError("in_service must be boolean.")

        if self.reactive_power_injection_mvar > 0.0:
            raise ValueError(
                "Reactor reactive power must be non-positive."
            )

        return True


__all__ = ["Reactor"]
