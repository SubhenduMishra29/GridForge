# ============================================================
# File: application/commands/add_network_element.py
# GridForge V2 — Add Network Element Command
# Author: Subhendu Mishra
# ============================================================
"""Concrete Application use case for adding an existing Core element."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .command import Command
from .command_result import CommandResult


@dataclass(frozen=True)
class AddNetworkElementCommand(Command):
    """Application intent to add one element to a Network aggregate."""

    element_type: str
    element: Any


class AddNetworkElementHandler:
    """Route an add-element command to the authoritative Network API."""

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError("network must not be None")
        self._network = network

    def handle(self, command: AddNetworkElementCommand) -> CommandResult:
        if not isinstance(command, AddNetworkElementCommand):
            raise TypeError("command must be AddNetworkElementCommand")
        if not command.element_type:
            return CommandResult.failure("element_type must not be empty")

        method: Callable[[Any], None] | None = getattr(
            self._network,
            f"add_{command.element_type}",
            None,
        )
        if method is None or not callable(method):
            return CommandResult.failure(
                f"Unsupported network element type: {command.element_type}"
            )

        try:
            method(command.element)
        except Exception as exc:
            return CommandResult.failure(str(exc))

        return CommandResult.success(
            payload={
                "element_type": command.element_type,
                "element": command.element,
            }
        )


__all__ = ["AddNetworkElementCommand", "AddNetworkElementHandler"]
