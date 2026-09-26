"""Presentation-only Control port identity for Ladder interaction.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ControlPortDirection(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


@dataclass(frozen=True, slots=True)
class ControlPortPresentation:
    component_id: str
    port_name: str
    direction: ControlPortDirection
    signal_type: str
    scene_position: tuple[float, float]


__all__ = ["ControlPortDirection", "ControlPortPresentation"]
