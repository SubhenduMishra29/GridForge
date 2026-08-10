"""
GridForge Terminal Model
========================

File:
    core/model/terminal.py

Defines the Terminal abstraction used to connect a model object
to a GridForge Bus.

A Terminal represents an electrical connection point.

Typical users include:

    - Load
    - Generator
    - Branch terminals
    - Future transformer terminals
    - Future shunt/device terminals

Responsibilities
----------------
The Terminal:

    - Holds a reference to its connected Bus.
    - Provides a common connection abstraction for model objects.
    - Keeps device models independent of Bus internals.

The Terminal does NOT:

    - Build network topology.
    - Calculate electrical quantities.
    - Build Ybus.
    - Perform power-flow calculations.
    - Perform protection calculations.
    - Manage GUI objects.

Topology management belongs to the network/container layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class Terminal:
    """
    Electrical connection point to a GridForge Bus.

    Parameters
    ----------
    bus:
        GridForge Bus object to which this terminal is connected.

    Notes
    -----
    A Terminal stores the actual Bus object reference.

    This is intentional for the model layer: devices such as
    Load and Generator can expose their connected Bus through
    the Terminal abstraction without knowing Bus implementation
    details.
    """

    def __init__(self, bus):
        # ---------------------------------------------------------
        # Connection validation
        # ---------------------------------------------------------

        if bus is None:
            raise ValueError(
                "Terminal must be connected to a valid Bus."
            )

        # Avoid importing Bus here.  The Terminal abstraction is
        # intentionally independent of the concrete Bus class,
        # preventing unnecessary circular dependencies.
        if not hasattr(bus, "id"):
            raise TypeError(
                "Terminal requires an object with a valid 'id' "
                "attribute."
            )

        # ---------------------------------------------------------
        # Store connection
        # ---------------------------------------------------------

        self.bus = bus

    # =============================================================
    # CONNECTION
    # =============================================================

    def connect(self, bus) -> None:
        """
        Reconnect this terminal to another Bus.

        Parameters
        ----------
        bus:
            New GridForge Bus object.
        """

        if bus is None:
            raise ValueError(
                "Terminal must be connected to a valid Bus."
            )

        if not hasattr(bus, "id"):
            raise TypeError(
                "Terminal requires an object with a valid 'id' "
                "attribute."
            )

        self.bus = bus

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return terminal connection information.
        """

        return {
            "bus": self.bus.id
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<Terminal "
            f"bus={self.bus.id}>"
        )
