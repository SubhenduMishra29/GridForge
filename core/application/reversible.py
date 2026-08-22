# ============================================================
# File: core/application/reversible.py
# GridForge V2 — Reversible Application Command Contract
# ============================================================
"""
GridForge V2
============

Module:
    core.application.reversible

Purpose
-------
Defines the explicit Application-layer contract for commands that
support undo/redo.

Undo/redo belongs to the Application layer.

The Core remains responsible for performing the actual domain
operation when invoked through its public API.

Architectural flow
------------------

    Application
        |
        v
    Reversible Command
        |
        +---- execute
        |
        +---- inverse command
        |
        v
    Application Service
        |
        v
       Core

Important
---------
Not every Application command is automatically reversible.

A command becomes reversible only when it explicitly provides an
inverse operation.

This prevents the Application layer from making unsafe assumptions
about how a domain operation should be undone.

Headless Requirement
--------------------
This module contains no dependency on:

    * Qt;
    * PySide6;
    * UI controllers;
    * SLD;
    * canvas;
    * renderers.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .command import Command


class ReversibleCommand(Command, ABC):
    """
    Base contract for an Application command that can be undone.

    A concrete reversible command must provide an inverse command.

    The inverse is itself an Application command.

    This means undo does not bypass the Application architecture.

    Example:

        CreateBusCommand
              |
              v
        DeleteBusCommand

    rather than:

        CreateBusCommand
              |
              +---- directly mutate Network   ❌
    """

    @abstractmethod
    def inverse(self) -> Command:
        """
        Construct the Application command that reverses this command.

        Returns
        -------
        Command
            Application command representing the inverse operation.

        Notes
        -----
        The inverse command must use the same Application boundary
        as any other command.

        It must never directly manipulate Core state.
        """
        raise NotImplementedError


def is_reversible(
    command: Command,
) -> bool:
    """
    Return whether a command explicitly implements reversibility.

    This helper deliberately uses capability detection rather than
    command-name conventions.
    """

    return isinstance(
        command,
        ReversibleCommand,
    )


__all__ = [
    "ReversibleCommand",
    "is_reversible",
]
