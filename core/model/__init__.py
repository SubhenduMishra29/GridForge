"""Public API for the authoritative GridForge V2 Model Layer."""

from __future__ import annotations

from .base import ElectricalObject
from .terminal import Terminal
from .injection import Injection
from .bus import Bus
from .branch import Branch
from .line import Line
from .cable import Cable
from .transformer import ImpedanceBasis, Transformer
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
from .endpoint_reference import EndpointReference, EndpointReferenceKind, EquipmentType

# Relay is a physical Core model and participates in the canonical identity
# contract without introducing a second identity implementation. The mature
# Relay constructor is preserved, while its public identity is made immutable
# and its canonical model TYPE is explicit.
Relay.TYPE = "RELAY"

def _relay_id_get(self):
    return self._id

def _relay_id_set(self, value):
    if hasattr(self, "_id"):
        raise AttributeError("Relay.id is immutable after construction.")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Relay.id must be a non-empty string.")
    self._id = value.strip()

Relay.id = property(_relay_id_get, _relay_id_set)
Relay.element_type = property(lambda self: "RELAY")
ElectricalObject.register(Relay)

__all__ = (
    "ElectricalObject", "Terminal", "Injection", "Bus", "Branch", "Line", "Cable", "ImpedanceBasis", "Transformer", "Switch",
    "Breaker", "Disconnector", "Fuse", "Load", "Generator", "SynchronousMachine", "SyncMachine", "Motor",
    "Shunt", "Capacitor", "Reactor", "Solar", "Battery", "Grid", "CTPolarity", "CurrentTransformer", "PT",
    "PotentialTransformer", "CVT", "Relay", "EndpointReference", "EndpointReferenceKind", "EquipmentType",
)
