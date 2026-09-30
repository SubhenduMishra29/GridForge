"""Presentation-side engineering context shared by the GridForge workstation.

Author: Subhendu Mishra

This context is read/interaction state only. It never owns Core engineering
truth and never performs mutations.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable


@dataclass(frozen=True, slots=True)
class EngineeringContext:
    """Immutable workstation context retained while changing discipline."""

    project_id: str | None = None
    project_name: str | None = None
    plant_id: str | None = None
    system_id: str | None = None
    study_id: str | None = None
    system_state: str | None = None
    discipline: str = "sld"
    active_tool: str | None = None
    selected_ids: tuple[str, ...] = ()

    def with_updates(self, **changes: Any) -> "EngineeringContext":
        allowed = set(self.__dataclass_fields__)
        unknown = set(changes).difference(allowed)
        if unknown:
            raise TypeError("Unknown engineering context fields: " + ", ".join(sorted(unknown)))
        if "selected_ids" in changes:
            changes["selected_ids"] = tuple(str(value) for value in (changes["selected_ids"] or ()))
        if "discipline" in changes and not str(changes["discipline"]).strip():
            raise ValueError("discipline must not be empty.")
        return replace(self, **changes)

    @classmethod
    def from_application(cls, application: Any, *, discipline: str = "sld",
                         active_tool: str | None = None,
                         selected_ids: Iterable[Any] = ()) -> "EngineeringContext":
        lifecycle = getattr(application, "project_lifecycle", None)
        project = getattr(lifecycle, "context", None)
        return cls(
            project_id=str(getattr(project, "project_id", "")) or None,
            project_name=str(getattr(project, "name", "")) or None,
            discipline=str(discipline),
            active_tool=active_tool,
            selected_ids=tuple(str(value) for value in selected_ids),
        )


class EngineeringContextStore:
    """Single presentation-side context store with explicit change observers."""

    def __init__(self, context: EngineeringContext | None = None) -> None:
        self._current = context or EngineeringContext()
        self._observers: list[Callable[[EngineeringContext], None]] = []

    @property
    def current(self) -> EngineeringContext:
        return self._current

    def update(self, **changes: Any) -> EngineeringContext:
        self._current = self._current.with_updates(**changes)
        for observer in tuple(self._observers):
            observer(self._current)
        return self._current

    def subscribe(self, observer: Callable[[EngineeringContext], None]) -> None:
        if not callable(observer):
            raise TypeError("observer must be callable.")
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: Callable[[EngineeringContext], None]) -> None:
        if observer in self._observers:
            self._observers.remove(observer)


__all__ = ["EngineeringContext", "EngineeringContextStore"]

