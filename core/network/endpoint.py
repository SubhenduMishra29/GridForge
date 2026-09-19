# ============================================================

# File: core/network/endpoint.py

# GridForge V2 — Network Endpoint Resolution

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Network Endpoint Resolution.

Provides canonical, read-only resolution from a model Terminal to its
electrical Bus.

This module interprets terminal endpoint relationships only; it does not
mutate model objects or construct topology.
"""

from __future__ import annotations

from typing import Any


# ============================================================
# TERMINAL -> BUS RESOLUTION
# ============================================================


def resolve_terminal_bus(
    terminal: Any,
) -> Any | None:
    """
    Resolve one authoritative Terminal to its electrical Bus.

    None is the only representation of a valid unconnected Terminal.
    Malformed endpoint relationships are raised so corrupted Core state is
    never silently interpreted as a disconnected terminal.
    """
    if terminal is None:
        raise TypeError("Terminal cannot be None.")

    from core.model.base import ElectricalObject
    from core.model.bus import Bus
    from core.model.terminal import Terminal

    if not isinstance(terminal, Terminal):
        raise TypeError("resolve_terminal_bus requires a Core Terminal.")

    endpoint = terminal.endpoint
    if endpoint is None:
        return None

    if isinstance(endpoint, Terminal):
        raise ValueError("Terminal-to-Terminal endpoint chaining is not supported.")

    if not isinstance(endpoint, ElectricalObject):
        raise TypeError("Terminal endpoint is not a supported Core ElectricalObject.")

    if isinstance(endpoint, Bus):
        return endpoint

    bus = getattr(endpoint, "bus", None)
    if bus is None:
        raise ValueError(
            f"Terminal endpoint '{endpoint.id}' is not a Bus and does not expose a Bus relationship."
        )
    if not isinstance(bus, Bus):
        raise TypeError("Terminal endpoint bus relationship is not a Core Bus.")
    return bus


__all__ = [
    "resolve_terminal_bus",
]
