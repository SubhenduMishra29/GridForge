# File: core/numerical/**init**.py

# GridForge V2

# Author: Subhendu Mishra

"""
GridForge V2 — Numerical Layer.

The Numerical layer owns derived mathematical representations and
numerical state produced from authoritative electrical Network/Model
data.

## Ownership boundary

Network owns:
- canonical electrical models
- Network membership
- topology
- terminal relationships
- authoritative BusIndex
- topology revision

Numerical owns:
- numerical state
- numerical representations
- Y-bus construction
- derived numerical artifacts

Solver owns:
- numerical solution algorithms

Numerical must not:
- own physical equipment models;
- own Network topology;
- own NetworkState;
- own the authoritative BusIndex;
- mutate Network;
- implement study orchestration;
- implement solver algorithms;
- depend on UI or plugins.

## Public API

BusState
DynamicState
YBus
YBusBuilder
"""

from .state import BusState, DynamicState
from .ybus import YBus, YBusBuilder

__all__ = [
"BusState",
"DynamicState",
"YBus",
"YBusBuilder",
]
