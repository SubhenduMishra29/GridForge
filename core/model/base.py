"""
base.py

Defines the base class for all electrical objects.
"""


class ElectricalObject:
    """
    Base class for all model components.
    """

    def __init__(self, id: str, name: str = ""):
        if not id:
            raise ValueError("Object must have a non-empty ID.")

        self.id = id
        self.name = name or id

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"
