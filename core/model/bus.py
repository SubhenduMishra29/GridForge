"""
bus.py

Defines the Bus model and BusType classification.
"""

from enum import Enum
from .base import ElectricalObject


class BusType(Enum):
    PQ = 1
    PV = 2
    SLACK = 3


class Bus(ElectricalObject):
    """
    Network node.
    """

    def __init__(self, id: str, name: str = "", type: BusType = BusType.PQ):
        super().__init__(id, name)
        self.type = type

    def __repr__(self):
        return f"<Bus id={self.id}, type={self.type.name}>"
