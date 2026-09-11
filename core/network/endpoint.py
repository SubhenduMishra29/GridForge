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
) -> Any:
    """
    Resolve a Terminal to its electrical Bus.

    Resolution order:

    1. Read ``terminal.endpoint``.
    2. Reject a missing endpoint.
    3. Reject Terminal-to-Terminal chaining.
    4. Resolve ``endpoint.bus`` when present and non-None.
    5. Otherwise return the endpoint itself as the Bus-like object.

    The resolver is intentionally read-only.
    """

    if terminal is None:
        raise ValueError(
            "Terminal cannot be None."
        )

    endpoint = getattr(
        terminal,
        "endpoint",
        None,
    )

    if endpoint is None:
        raise ValueError(
            "Terminal does not have an endpoint."
        )

    # Import locally to avoid a module-level dependency cycle between
    # model and network package initialization.
    from core.model.terminal import Terminal

    if isinstance(
        endpoint,
        Terminal,
    ):
        raise ValueError(
            "Terminal-to-Terminal endpoint chaining is not supported."
        )

    resolved_bus = getattr(
        endpoint,
        "bus",
        None,
    )

    if resolved_bus is not None:
        return resolved_bus

    return endpoint


__all__ = [
    "resolve_terminal_bus",
]
