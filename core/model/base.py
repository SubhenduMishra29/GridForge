# core/model/base.py

"""
base.py

Foundational object definitions for the unified power system model.
"""

class GridObject:
    def __init__(self, id: str, name: str = ""):
        if not id or not isinstance(id, str):
            raise ValueError("GridObject 'id' must be a non-empty string")

        self.id = id
        self.name = name
        self.metadata: dict = {}

    def __repr__(self):
        return f"<{self.__class__.__name__} id='{self.id}'>"

    def __eq__(self, other):
        if not isinstance(other, GridObject):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class ElectricalObject(GridObject):
    def __init__(self, id: str, name: str = "", in_service: bool = True):
        super().__init__(id, name)
        self.in_service = bool(in_service)

    def is_active(self) -> bool:
        return self.in_service

    def deactivate(self):
        self.in_service = False

    def activate(self):
        self.in_service = True
