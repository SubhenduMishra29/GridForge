"""Common identity and validation contract for GridForge model objects."""

from __future__ import annotations

from abc import ABC
from typing import Any


class ElectricalObject(ABC):
    """Root Core identity contract for physical engineering objects.

    ``id`` is stable, ``name`` is mutable, ``TYPE`` is canonical, and
    ``validate()`` is the public Core validation entry point.
    """

    TYPE = "ELECTRICAL_OBJECT"

    def __init__(self, id: str, name: str = "") -> None:
        if id is None: raise ValueError("Object ID cannot be None.")
        if not isinstance(id, str): raise TypeError("Object ID must be a string.")
        normalized_id = id.strip()
        if not normalized_id: raise ValueError("Object ID cannot be empty.")
        if name is None: name = ""
        if not isinstance(name, str): raise TypeError("Object name must be a string.")
        object.__setattr__(self, "_id", normalized_id)
        self.name = name.strip() or normalized_id

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        raise AttributeError("ElectricalObject.id is immutable after construction.")

    @property
    def element_type(self) -> str:
        model_type = getattr(self.__class__, "TYPE", None)
        if not isinstance(model_type, str): return self.__class__.__name__
        model_type = model_type.strip()
        return model_type or self.__class__.__name__

    def validate_parameters(self) -> bool:
        if not isinstance(self._id, str) or not self._id.strip(): raise ValueError("Object ID cannot be empty.")
        if not isinstance(self.name, str) or not self.name.strip(): raise ValueError("Object name cannot be empty.")
        return True

    def validate(self) -> bool:
        return self.validate_parameters()

    def __eq__(self, other: object) -> bool:
        if self is other: return True
        if other is None: return NotImplemented
        if type(self) is not type(other): return NotImplemented
        return self.id == other.id  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def summary(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "type": self.element_type}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


__all__ = ["ElectricalObject"]
