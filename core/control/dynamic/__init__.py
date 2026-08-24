"""
GridForge V2 - Dynamic Control Domain
=====================================

Author:
    Subhendu Mishra

Package:
    core.control.dynamic

Purpose
-------
Headless domain contracts for continuous/dynamic control systems.

Concrete implementations such as AVR, PSS, and Governor remain under:

    plugins/dynamics/

This package contains only Control-domain contracts and abstractions.
"""

from .base import (
    DynamicControlComponent,
    DynamicControlResult,
    DynamicStateDefinition,
)

__all__ = [
    "DynamicControlComponent",
    "DynamicControlResult",
    "DynamicStateDefinition",
]
