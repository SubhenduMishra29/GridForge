"""Canonical temperature-sensor Core identities and terminal contracts.

This module models only physical sensor identity and terminal ownership.
Calibration, compensation tables, acquisition, channel scaling and UI
projection remain outside Core.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class RTDWiringConfiguration(str, Enum):
    TWO_WIRE = "2_WIRE"
    THREE_WIRE = "3_WIRE"
    FOUR_WIRE = "4_WIRE"


class ThermocoupleType(str, Enum):
    J = "J"
    K = "K"
    T = "T"
    E = "E"
    N = "N"
    R = "R"
    S = "S"
    B = "B"


class RTD(ElectricalObject):
    """Physical RTD element with configuration-specific lead terminals."""

    TYPE = "RTD"
    __slots__ = ("_wiring_configuration", "_in_service", "_terminals")

    def __init__(
        self, id: str, *, name: str = "",
        wiring_configuration: RTDWiringConfiguration | str = RTDWiringConfiguration.THREE_WIRE,
        in_service: bool = True,
        endpoints: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(id=id, name=name)
        try:
            configuration = RTDWiringConfiguration(wiring_configuration)
        except (TypeError, ValueError) as exc:
            raise ValueError("RTD wiring_configuration must be 2_WIRE, 3_WIRE or 4_WIRE.") from exc
        if not isinstance(in_service, bool):
            raise TypeError("RTD in_service must be boolean.")
        roles = {
            RTDWiringConfiguration.TWO_WIRE: ("A", "B"),
            RTDWiringConfiguration.THREE_WIRE: ("A", "B1", "B2"),
            RTDWiringConfiguration.FOUR_WIRE: ("A1", "A2", "B1", "B2"),
        }[configuration]
        supplied = dict(endpoints or {})
        if set(supplied) - set(roles):
            raise ValueError("RTD endpoints contain roles not present in its declared wiring configuration.")
        terminals = []
        for role in roles:
            terminal = Terminal(owner=self, role=role)
            if supplied.get(role) is not None:
                terminal.attach(supplied[role])
            terminals.append(terminal)
        self._wiring_configuration = configuration
        self._in_service = in_service
        self._terminals = tuple(terminals)

    @property
    def wiring_configuration(self) -> RTDWiringConfiguration:
        return self._wiring_configuration

    @property
    def in_service(self) -> bool:
        return self._in_service

    @in_service.setter
    def in_service(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("RTD in_service must be boolean.")
        self._in_service = value

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        return self._terminals

    def validate_parameters(self) -> bool:
        super().validate_parameters()
        expected = {
            RTDWiringConfiguration.TWO_WIRE: {"A", "B"},
            RTDWiringConfiguration.THREE_WIRE: {"A", "B1", "B2"},
            RTDWiringConfiguration.FOUR_WIRE: {"A1", "A2", "B1", "B2"},
        }[self._wiring_configuration]
        if {terminal.role for terminal in self._terminals} != expected:
            raise ValueError("RTD terminal roles do not match its declared wiring configuration.")
        return True


class Thermocouple(ElectricalObject):
    """Physical thermocouple element with explicit polarity terminals."""

    TYPE = "THERMOCOUPLE"
    __slots__ = ("_thermocouple_type", "_in_service", "_positive_terminal", "_negative_terminal")

    def __init__(
        self, id: str, *, name: str = "",
        thermocouple_type: ThermocoupleType | str = ThermocoupleType.K,
        in_service: bool = True,
        positive_endpoint: Any = None,
        negative_endpoint: Any = None,
    ) -> None:
        super().__init__(id=id, name=name)
        try:
            kind = ThermocoupleType(thermocouple_type)
        except (TypeError, ValueError) as exc:
            raise ValueError("Unsupported thermocouple type; use a declared IEC/industry type J, K, T, E, N, R, S or B.") from exc
        if not isinstance(in_service, bool):
            raise TypeError("Thermocouple in_service must be boolean.")
        self._thermocouple_type = kind
        self._in_service = in_service
        self._positive_terminal = Terminal(owner=self, role="POSITIVE", endpoint=positive_endpoint)
        self._negative_terminal = Terminal(owner=self, role="NEGATIVE", endpoint=negative_endpoint)

    @property
    def thermocouple_type(self) -> ThermocoupleType:
        return self._thermocouple_type

    @property
    def in_service(self) -> bool:
        return self._in_service

    @in_service.setter
    def in_service(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("Thermocouple in_service must be boolean.")
        self._in_service = value

    @property
    def positive_terminal(self) -> Terminal:
        return self._positive_terminal

    @property
    def negative_terminal(self) -> Terminal:
        return self._negative_terminal

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        return self._positive_terminal, self._negative_terminal

    def validate_parameters(self) -> bool:
        super().validate_parameters()
        if not isinstance(self._thermocouple_type, ThermocoupleType):
            raise ValueError("Thermocouple type is not canonical.")
        return True


__all__ = ["RTDWiringConfiguration", "ThermocoupleType", "RTD", "Thermocouple"]
