# ============================================================
# File: ui/editors/study/study_tool_runtime.py
# GridForge V2 — Study Tool Runtime
# Author: Subhendu Mishra
# ============================================================

"""Lightweight Study editor runtime over the Application study boundary."""

from __future__ import annotations

from typing import Any
from ui.tools.tool_definition import ToolDefinition


class StudyToolRuntime:
    """Own contextual Study actions without becoming a second study authority."""

    TOOL_DEFINITIONS = (
        ToolDefinition("run_study", "Run Study", "Execute the selected Study Case through Application.", icon_id="run_study", editor_types=("study",), capabilities=("study",), supported_modes=("select", "edit"), default_mode="edit", category="study"),
        ToolDefinition("inspect_result", "Inspect Result", "Inspect the selected Study Result.", icon_id="inspect_result", editor_types=("study",), capabilities=("result", "inspect"), supported_modes=("select",), default_mode="select", category="results"),
        ToolDefinition("compare_results", "Compare Results", "Select Study Results for comparison.", icon_id="compare_results", editor_types=("study",), capabilities=("result", "compare"), supported_modes=("select",), default_mode="select", category="results"),
        ToolDefinition("plot", "Plot", "Prepare the selected Study Result for plotting.", icon_id="plot", editor_types=("study",), capabilities=("result", "plot"), supported_modes=("select",), default_mode="select", category="results"),
        ToolDefinition("filter", "Filter", "Filter visible Study Results.", icon_id="filter", editor_types=("study",), capabilities=("result", "filter"), supported_modes=("select",), default_mode="select", category="results"),
        ToolDefinition("export", "Export", "Export the selected Study Result through the presentation/Application boundary.", icon_id="export", editor_types=("study",), capabilities=("result", "export"), supported_modes=("select",), default_mode="select", category="results"),
        ToolDefinition("navigate", "Navigate", "Navigate Study result views.", icon_id="navigate", editor_types=("study",), capabilities=("view", "navigate"), supported_modes=("pan", "zoom"), default_mode="pan", category="view"),
    )

    def __init__(self, *, application: Any, study_case_controller: Any | None = None) -> None:
        if application is None:
            raise ValueError("application is required.")
        self._application = application
        self._study_case_controller = study_case_controller
        self._active_tool_id = "inspect_result"

    @property
    def active_tool_id(self) -> str:
        return self._active_tool_id

    @property
    def definitions(self) -> tuple[ToolDefinition, ...]:
        return self.TOOL_DEFINITIONS

    def bind_study_case_controller(self, controller: Any) -> None:
        if controller is None or not callable(getattr(controller, "run_study", None)):
            raise TypeError("controller must expose run_study().")
        self._study_case_controller = controller

    def activate(self, tool_id: str) -> str:
        normalized = str(tool_id).strip()
        if normalized not in {item.tool_id for item in self.TOOL_DEFINITIONS}:
            raise KeyError(f"Unknown Study tool: {tool_id!r}")
        self._active_tool_id = normalized
        return normalized

    def run_selected(self, study_id: object) -> object:
        if self._study_case_controller is None:
            raise RuntimeError("StudyCaseController is not bound.")
        return self._study_case_controller.run_study(study_id)

    def active_tool(self) -> ToolDefinition:
        return next(item for item in self.TOOL_DEFINITIONS if item.tool_id == self._active_tool_id)


__all__ = ["StudyToolRuntime"]
