"""
GridForge V2 - Logic Gates
===========================

Author:
    Subhendu Mishra

Package:
    core.control.logic.gates

Purpose
-------
Headless Boolean logic-gate implementations for the GridForge Control
domain.

The gates are domain components only. UI symbols, layout, node positions,
graphics, and editing behavior belong to the UI logic-layout canvas.
"""

from .and_gate import ANDGate
from .not_gate import NOTGate
from .or_gate import ORGate
from .xor_gate import XORGate

__all__ = [
    "ANDGate",
    "ORGate",
    "NOTGate",
    "XORGate",
]
