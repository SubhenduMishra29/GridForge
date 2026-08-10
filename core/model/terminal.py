"""
terminal.py

Defines the Terminal abstraction.

A Terminal connects a device (load, generator, branch)
to a Bus without the device needing to know bus internals.
"""


class Terminal:
    """
    Represents a connection point to a Bus.
    """

    def __init__(self, bus):
        if bus is None:
            raise ValueError("Terminal must be connected to a valid Bus.")

        self.bus = bus

    def __repr__(self):
        return f"<Terminal bus={self.bus.id}>"
