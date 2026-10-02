# ============================================================
# File: ui/workspace/engineering_context.py
# GridForge V2 — Engineering and Editor Context
# Author: Subhendu Mishra
# ============================================================
"""Presentation-side immutable context contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Iterable, Mapping

from ui.tools.tool_mode import ToolMode
from ui.tools.tool_settings import ToolSettings


@dataclass(frozen=True, slots=True)
class EngineeringContext:
    """Immutable engineering context retained while changing discipline."""

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


@dataclass(frozen=True, slots=True)
class EditorContext:
    """Immutable presentation context for the active editor situation.

    This context describes state; it does not own runtime services, widgets,
    Core models, Application, ToolManager, or SelectionManager.
    """

    workspace: Any = None
    area: Any = None
    editor: Any = None
    region: Any = None
    engineering: EngineeringContext = field(default_factory=EngineeringContext)
    selection_context: Mapping[str, object] = field(default_factory=dict)
    active_tool: str | None = None
    tool_mode: ToolMode = ToolMode.IDLE
    tool_settings: ToolSettings | None = None
    interaction_state: Mapping[str, object] = field(default_factory=dict)
    view_state: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.engineering, EngineeringContext):
            raise TypeError("engineering must be an EngineeringContext.")
        if not isinstance(self.tool_mode, ToolMode):
            raise TypeError("tool_mode must be a ToolMode.")
        for name in ("selection_context", "interaction_state", "view_state"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise TypeError(f"{name} must be a mapping.")
            object.__setattr__(self, name, dict(value))
        if self.active_tool is not None:
            if not isinstance(self.active_tool, str) or not self.active_tool.strip():
                raise ValueError("active_tool must be None or a non-empty string.")
            object.__setattr__(self, "active_tool", self.active_tool.strip())
        if self.tool_settings is not None and not isinstance(self.tool_settings, ToolSettings):
            raise TypeError("tool_settings must be ToolSettings or None.")

    def with_updates(self, **changes: Any) -> "EditorContext":
        allowed = set(self.__dataclass_fields__)
        unknown = set(changes).difference(allowed)
        if unknown:
            raise TypeError("Unknown editor context fields: " + ", ".join(sorted(unknown)))
        return replace(self, **changes)


class EngineeringContextStore:
    """Single presentation-side engineering context store."""

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


__all__ = ["EngineeringContext", "EngineeringContextStore", "EditorContext"]
