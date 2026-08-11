```python
# core/model/terminal.py

"""
GridForge Terminal Model
========================

GridForge Model Layer V2

Defines the Terminal abstraction used to connect a GridForge model
object to an electrical Bus.

A Terminal represents an electrical connection point.

Typical users include:

- Load
- Generator
- Branch terminals
- Transformer terminals
- Shunt/device terminals
- Future electrical equipment models

Responsibilities
----------------
The Terminal:

- Holds a reference to its connected Bus.
- Provides a common connection abstraction for model objects.
- Keeps device models independent of Bus implementation details.
- Provides basic connection validation.
- Provides connection diagnostics.

The Terminal does NOT:

- Build network topology.
- Calculate electrical quantities.
- Build Y-bus matrices.
- Perform power-flow calculations.
- Perform short-circuit calculations.
- Perform protection calculations.
- Manage GUI objects.
- Own network registration.

Topology management belongs to the appropriate network/container
layer.

Architecture
------------
The Terminal deliberately avoids importing the concrete Bus class.

This prevents unnecessary coupling and circular dependencies between
model objects.

Instead, Terminal uses a small structural contract: the connected
object must expose a valid ``id`` attribute.

The actual network/container layer remains responsible for ensuring
that the referenced object is a valid registered GridForge Bus.

Connection Model
----------------
A Terminal contains a direct reference to its connected Bus:

    Terminal
        │
        ▼
       Bus

This direct reference is intentional. Device models can access their
connection point without depending on the internal implementation of
the network topology manager.

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental model requirement
that cannot be satisfied through the network layer or a specialized
device model.

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
    The Terminal stores the actual Bus object reference.

    The Terminal does not own the Bus and does not register itself
    with the network.

    Network registration and topology ownership belong to the
    appropriate network/container layer.
    """

    def __init__(self, bus):
        """
        Create a Terminal connected to a Bus.
        """

        self._validate_bus(bus)

        self.bus = bus

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_bus(bus) -> None:
        """
        Validate the minimum connection contract.

        Terminal deliberately does not import the concrete ``Bus``
        class. This keeps the model dependency graph lightweight and
        avoids circular imports.

        The connected object must expose a non-empty string ``id``.
        """

        if bus is None:
            raise ValueError(
                "Terminal must be connected to a valid Bus."
            )

        if not hasattr(bus, "id"):
            raise TypeError(
                "Terminal requires an object with an 'id' attribute."
            )

        bus_id = getattr(bus, "id")

        if not isinstance(bus_id, str):
            raise TypeError(
                "Terminal Bus ID must be a string."
            )

        if not bus_id.strip():
            raise ValueError(
                "Terminal cannot connect to a Bus with an empty ID."
            )

    # =================================================================
    # CONNECTION
    # =================================================================

    def connect(self, bus) -> None:
        """
        Reconnect this Terminal to another Bus.

        Parameters
        ----------
        bus:
            New GridForge Bus object.

        Notes
        -----
        This operation changes only the local Bus reference.

        It does not:
        - modify network topology,
        - register the terminal,
        - disconnect the previous Bus,
        - update solver structures,
        - rebuild Y-bus.

        Those operations belong to the appropriate network layer.
        """

        self._validate_bus(bus)

        self.bus = bus

    # =================================================================
    # DISCONNECTION
    # =================================================================

    def disconnect(self) -> None:
        """
        Disconnect this Terminal from its current Bus.

        Notes
        -----
        A disconnected Terminal has ``bus = None``.

        This method changes only the local connection reference.
        Network topology management remains the responsibility of
        the network/container layer.
        """

        self.bus = None

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Terminal is connected to a Bus.
        """

        return self.bus is not None

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return Terminal connection information.

        Returns
        -------
        dict
            Dictionary containing the connected Bus identifier, or
            ``None`` when disconnected.
        """

        return {
            "bus": (
                self.bus.id
                if self.bus is not None
                else None
            )
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        if self.bus is None:
            return "<Terminal bus=None>"

        return (
            f"<Terminal "
            f"bus={self.bus.id}>"
        )
```
