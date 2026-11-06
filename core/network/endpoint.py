from __future__ import annotations
from typing import Any
from core.model import EndpointReference,EndpointReferenceKind
from .electrical_boundary import EndpointCompatibility,EndpointCompatibilityError
def resolve_terminal_bus(terminal:Any)->Any|None:
    from core.model.terminal import Terminal
    from core.model.bus import Bus
    if not isinstance(terminal,Terminal): raise TypeError("resolve_terminal_bus requires a Core Terminal.")
    endpoint=terminal.endpoint
    if endpoint is None:return None
    if isinstance(endpoint,Terminal):raise ValueError("Terminal-to-Terminal endpoint chaining is not supported.")
    if not isinstance(endpoint,Bus):raise TypeError("Terminal endpoint must be a Core Bus.")
    return endpoint
def resolve_endpoint_reference(network:Any,reference:EndpointReference)->Any:
    EndpointCompatibility.validate_reference(reference,network)
    if reference.kind is EndpointReferenceKind.BUS:return network.get_by_identity(reference.object_id)
    equipment=network.get_by_identity(reference.object_id)
    return next(t for t in equipment.terminals if t.owner is equipment and t.role==reference.terminal_role)
__all__=["EndpointCompatibility","EndpointCompatibilityError","resolve_endpoint_reference","resolve_terminal_bus"]