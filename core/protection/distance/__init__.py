"""
GridForge Distance Protection
=============================

Transmission-line impedance protection plugin.

Provides
--------
DistanceRelay
    Baseline ANSI 21 distance-protection function.

The implementation is provided by:

    core.protection.distance.distance_relay
"""

from core.protection.distance.distance_relay import (
    DistanceRelay,
)

__all__ = [
    "DistanceRelay",
]
