"""
terminal.py

Defines connection points between grid elements and buses.

A Terminal represents a single electrical connection to a bus.

Used by:
- Lines (2 terminals)
- Transformers (2 terminals)
- Loads (1 terminal)
- Generators (1 terminal)
- Shunts (1 terminal)

This abstraction decouples:
- Equipment from Bus
- Topology from model structure
"""


class Terminal:
    """
    Represents a connection point to a bus.
    """

    def __init__(self, bus):
        """
        Parameters
        ----------
        bus : Bus
            The bus this terminal is connected to
        """

        if bus is None:
            raise ValueError("Terminal must be connected to a Bus")

        # Reference to Bus (no ownership)
        self.bus = bus

    def __repr__(self):
        return f"<Terminal bus={self.bus.id}>"
