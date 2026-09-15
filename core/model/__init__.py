"""Public API for the authoritative GridForge V2 Model Layer."""

from __future__ import annotations

from .base import ElectricalObject
from .terminal import Terminal
from .injection import Injection
from .bus import Bus
from .branch import Branch
from .line import Line
from .cable import Cable
from .transformer import Transformer
from .switch import Switch
from .breaker import Breaker
from .disconnector import Disconnector
from .fuse import Fuse
from .load import Load
from .generator import Generator
from .synchronous_machine import SynchronousMachine, SyncMachine
from .motor import Motor
from .shunt import Shunt
from .capacitor import Capacitor
from .reactor import Reactor
from .solar import Solar
from .battery import Battery
from .grid import Grid
from .ct import CTPolarity, CurrentTransformer
from .pt import PT
PotentialTransformer = PT
from .cvt import CVT
from .relay import Relay

# Relay is a physical Core model and participates in the same identity,
# validation and persistence contract as the canonical ElectricalObject tree.
# Registration is virtual to preserve the mature Relay implementation while
# removing a second identity contract.
ElectricalObject.register(Relay)

__all__ = (
    "ElectricalObject", "Terminal", "Injection", "Bus", "Branch", "Line", "Cable", "Transformer", "Switch",
    "Breaker", "Disconnector", "Fuse", "Load", "Generator", "SynchronousMachine", "SyncMachine", "Motor",
    "Shunt", "Capacitor", "Reactor", "Solar", "Battery", "Grid", "CTPolarity", "CurrentTransformer", "PT",
    "PotentialTransformer", "CVT", "Relay",
)
