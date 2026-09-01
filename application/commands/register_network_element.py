# ============================================================
# File: application/commands/register_network_element.py
# GridForge V2 — Network Element Command Registration
# Author: Subhendu Mishra
# ============================================================
"""Composition helper for the first concrete network mutation handler."""

from __future__ import annotations

from typing import Any

from .add_network_element import AddNetworkElementHandler
from .command_dispatcher import CommandDispatcher


def register_network_element_handler(
    dispatcher: CommandDispatcher,
    network: Any,
) -> AddNetworkElementHandler:
    """Register the network-element handler with the application dispatcher."""
    handler = AddNetworkElementHandler(network)
    dispatcher.register("add_network_element", handler)
    return handler


__all__ = ["register_network_element_handler"]
