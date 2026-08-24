"""
GridForge V2 - Control Module
=============================

Author:
    Subhendu Mishra

File:
    core/control/__init__.py

Purpose
-------
Public package boundary for the headless GridForge Control subsystem.

The Control package owns control-state, signal, limit, controller,
dynamic-control, and logic-control contracts.

This module intentionally contains no runtime initialization,
registration, UI imports, or application-shell behavior.

Architecture
------------
    UI / Application
           |
           v
    Control public contracts
           |
           v
    Headless Control implementation

The package exports only stable public Control interfaces.
"""

from .state import (
    ControlState,
)

from .signals import (
    ControlSignal,
)

from .limits import (
    ControlLimits,
)

from .controller import (
    Controller,
)

__all__ = [
    "ControlState",
    "ControlSignal",
    "ControlLimits",
    "Controller",
]
