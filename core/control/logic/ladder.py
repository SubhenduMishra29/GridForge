"""Semantic Ladder Logic program structure for GridForge V2.

Author: Subhendu Mishra

The model is deliberately headless. It describes program/rung membership while
LogicEngine remains the single execution authority for component semantics,
signals, dependencies, state and evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .base import LogicControlComponent
from .engine import LogicConnection, LogicDependency, LogicEngine


class LadderModelError(ValueError):
    """Invalid Ladder program structure."""


@dataclass(frozen=True, slots=True)
class LadderElementRef:
    """Reference to one Core logic component placed in a rung."""

    component_id: str
    position: int

    def __post_init__(self) -> None:
        component_id = str(self.component_id).strip()
        if not component_id:
            raise LadderModelError("component_id cannot be empty.")
        if int(self.position) < 0:
            raise LadderModelError("position cannot be negative.")
        object.__setattr__(self, "component_id", component_id)
        object.__setattr__(self, "position", int(self.position))


@dataclass(frozen=True, slots=True)
class LadderRung:
    """Ordered Ladder rung containing component references only."""

    rung_id: str
    order: int
    elements: tuple[LadderElementRef, ...] = ()
    enabled: bool = True

    def __post_init__(self) -> None:
        rung_id = str(self.rung_id).strip()
        if not rung_id:
            raise LadderModelError("rung_id cannot be empty.")
        if int(self.order) < 0:
            raise LadderModelError("rung order cannot be negative.")
        elements = tuple(self.elements)
        seen: set[str] = set()
        for element in elements:
            if not isinstance(element, LadderElementRef):
                raise LadderModelError("rung elements must be LadderElementRef instances.")
            if element.component_id in seen:
                raise LadderModelError(f"Component '{element.component_id}' appears twice in rung '{rung_id}'.")
            seen.add(element.component_id)
        object.__setattr__(self, "rung_id", rung_id)
        object.__setattr__(self, "order", int(self.order))
        object.__setattr__(self, "elements", elements)


class LadderProgram:
    """Single semantic Ladder program backed by the existing LogicEngine."""

    def __init__(self, program_id: str, *, engine: LogicEngine | None = None) -> None:
        program_id = str(program_id).strip()
        if not program_id:
            raise LadderModelError("program_id cannot be empty.")
        self._program_id = program_id
        self._engine = engine if engine is not None else LogicEngine()
        self._rungs: dict[str, LadderRung] = {}

    @property
    def program_id(self) -> str:
        return self._program_id

    @property
    def engine(self) -> LogicEngine:
        """Return the sole execution engine owned by this program."""
        return self._engine

    def add_rung(self, rung_id: str, *, order: int | None = None, enabled: bool = True) -> LadderRung:
        rung_id = str(rung_id).strip()
        if not rung_id:
            raise LadderModelError("rung_id cannot be empty.")
        if rung_id in self._rungs:
            raise LadderModelError(f"Rung '{rung_id}' already exists.")
        if order is None:
            order = len(self._rungs)
        order = int(order)
        if order < 0 or any(r.order == order for r in self._rungs.values()):
            raise LadderModelError(f"Invalid or occupied rung order: {order}.")
        rung = LadderRung(rung_id=rung_id, order=order, enabled=enabled)
        self._rungs[rung_id] = rung
        return rung

    def remove_rung(self, rung_id: str) -> LadderRung:
        try:
            return self._rungs.pop(str(rung_id).strip())
        except KeyError as exc:
            raise LadderModelError(f"Unknown rung '{rung_id}'.") from exc

    def rung(self, rung_id: str) -> LadderRung:
        try:
            return self._rungs[str(rung_id).strip()]
        except KeyError as exc:
            raise LadderModelError(f"Unknown rung '{rung_id}'.") from exc

    def rungs(self) -> tuple[LadderRung, ...]:
        return tuple(sorted(self._rungs.values(), key=lambda rung: (rung.order, rung.rung_id)))

    def add_component(self, component: LogicControlComponent, *, rung_id: str, position: int | None = None) -> None:
        rung = self.rung(rung_id)
        if self._engine.contains(component.component_id):
            raise LadderModelError(f"Component '{component.component_id}' already exists.")
        if any(e.component_id == component.component_id for r in self._rungs.values() for e in r.elements):
            raise LadderModelError(f"Component '{component.component_id}' is already placed in the program.")
        if position is None:
            position = len(rung.elements)
        position = int(position)
        if position < 0 or position > len(rung.elements):
            raise LadderModelError("Component position is outside the rung.")
        self._engine.register(component)
        elements = list(rung.elements)
        elements.insert(position, LadderElementRef(component.component_id, position))
        self._replace_rung(rung, elements)

    def remove_component(self, component_id: str) -> LogicControlComponent:
        component_id = str(component_id).strip()
        component = self._engine.unregister(component_id)
        for rung in tuple(self._rungs.values()):
            if any(e.component_id == component_id for e in rung.elements):
                elements = [e for e in rung.elements if e.component_id != component_id]
                self._replace_rung(rung, elements)
                break
        return component

    def move_component(self, component_id: str, *, rung_id: str, position: int) -> None:
        component_id = str(component_id).strip()
        rung = self.rung(rung_id)
        if not self._engine.contains(component_id):
            raise LadderModelError(f"Unknown component '{component_id}'.")
        if position < 0 or position > len(rung.elements):
            raise LadderModelError("Component position is outside the rung.")
        for old_rung in tuple(self._rungs.values()):
            if any(e.component_id == component_id for e in old_rung.elements):
                remaining = [e for e in old_rung.elements if e.component_id != component_id]
                self._replace_rung(old_rung, remaining)
                break
        elements = list(rung.elements)
        elements.insert(position, LadderElementRef(component_id, position))
        self._replace_rung(rung, elements)

    def connections(self) -> tuple[LogicConnection, ...]:
        return self._engine.connections()

    def dependencies(self) -> tuple[LogicDependency, ...]:
        return self._engine.dependencies()

    def _replace_rung(self, rung: LadderRung, elements: Iterable[LadderElementRef]) -> None:
        normalized = tuple(
            LadderElementRef(element.component_id, index)
            for index, element in enumerate(elements)
        )
        self._rungs[rung.rung_id] = LadderRung(
            rung_id=rung.rung_id,
            order=rung.order,
            elements=normalized,
            enabled=rung.enabled,
        )


__all__ = ["LadderModelError", "LadderElementRef", "LadderRung", "LadderProgram"]
