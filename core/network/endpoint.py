# ============================================================
# File: core/network/endpoint.py
# GridForge V2 — Network Endpoint Resolution
# Author: Subhendu Mishra
# ============================================================

"""
Canonical Terminal → Bus resolution.

The model layer owns Terminal and endpoint relationships.

The Network layer merely provides a common interpretation of
those relationships to topology and Y-bus consumers.

This module must not mutate terminals or buses.
"""

from __future__ import annotations

from typing import Any


def resolve_terminal_bus(
    terminal: Any,
) -> Any:
    """
    Resolve a Terminal to its electrical Bus.

    Resolution order:

        terminal.endpoint
            ↓
        endpoint.bus

    The terminal endpoint is authoritative.

    Raises
    ------
    ValueError
        If the terminal or endpoint is missing or cannot resolve
        to a Bus.
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

    bus = getattr(
        endpoint,
        "bus",
        None,
    )

    if bus is None:
        raise ValueError(
            "Terminal endpoint does not resolve to a bus."
        )

    return bus
