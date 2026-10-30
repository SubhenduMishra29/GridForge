# ============================================================
# File: core/network/__init__.py
# GridForge V2 — Network Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Network Layer
==========================

Public package boundary for the assembled electrical network.

The Network Layer assembles canonical objects from core.model into an
engineering network representation. It owns membership, endpoint
connectivity, topology and derived network state. It remains headless and
independent of SLD/UI presentation.

Y-bus construction belongs to core.numerical.
"""

from __future__ import annotations

from .network import Network
from .junction import Junction
from .junction_registry import JunctionRegistry
from .registry import NetworkRegistry
from .indexing import BusIndex
from .state import NetworkState
from .topology import TopologyManager
from .topology_endpoint_reference import (
    TopologyEndpointReference,
    TopologyEndpointReferenceKind,
)
from .connectivity import (
    ConnectivityError,
    ConnectivityResolver,
    ConnectivityStore,
    ResolvedConnectivity,
    SIMPLE_WIRE_KIND,
    SimpleWireCompatibility,
    SimpleWireConnection,
)
from .electrical_boundary import (
    ElectricalBoundary,
    ElectricalBoundaryResolver,
    ElectricalBoundaryType,
    EndpointCompatibility,
    EndpointCompatibilityError,
    conduction_state,
)
from .topology_snapshot import (
    ConductiveEdge,
    EquipmentBusAttachment,
    TopologyProvenance,
    TopologySnapshot,
)
from .ct_measurement_association import (
    CTMeasurementAssociation,
    CTMeasurementAssociationError,
    CTMeasurementAssociationResolver,
    CTMeasurementAssociationStatus,
)
from core.base.per_unit import PerUnitSystem

__all__ = [
    "Network",
    "Junction",
    "JunctionRegistry",
    "NetworkRegistry",
    "BusIndex",
    "NetworkState",
    "TopologyManager",
    "ConnectivityError",
    "ConnectivityResolver",
    "ConnectivityStore",
    "ResolvedConnectivity",
    "SIMPLE_WIRE_KIND",
    "SimpleWireCompatibility",
    "SimpleWireConnection",
    "TopologyEndpointReference",
    "TopologyEndpointReferenceKind",
    "ElectricalBoundary",
    "ElectricalBoundaryResolver",
    "ElectricalBoundaryType",
    "EndpointCompatibility",
    "EndpointCompatibilityError",
    "conduction_state",
    "ConductiveEdge",
    "EquipmentBusAttachment",
    "TopologyProvenance",
    "TopologySnapshot",
    "CTMeasurementAssociation",
    "CTMeasurementAssociationError",
    "CTMeasurementAssociationResolver",
    "CTMeasurementAssociationStatus",
    "PerUnitSystem",
]

__version__ = "2.0.0"
