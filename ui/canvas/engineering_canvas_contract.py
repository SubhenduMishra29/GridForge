# GridForge V2 — Common Engineering Canvas Interaction Contract
# Author: Subhendu Mishra
"""Presentation-level interaction vocabulary shared by engineering canvases."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

class CanvasInput(str, Enum):
    SELECT="select"; MULTI_SELECT="multi_select"; PLACE="place"; MOVE="move"; CONNECT="connect"
    DELETE="delete"; CANCEL="cancel"; ZOOM="zoom"; PAN="pan"; FIT="fit"

class CanvasFeedback(str, Enum):
    NONE="none"; PREVIEW="preview"; SELECTED="selected"; INVALID="invalid"
    WARNING="warning"; CONNECTED="connected"; DEGRADED="degraded"

class CanvasLifecycle(str, Enum):
    IDLE="idle"; TOOL_ACTIVE="tool_active"; PREVIEW="preview"; COMMITTED="committed"
    CONNECTING="connecting"; FEEDBACK="feedback"

@dataclass(frozen=True, slots=True)
class CanvasContext:
    workspace_id:str
    discipline:str
    active_tool:str|None=None
    selected_object_ids:tuple[Any,...]=()
    lifecycle:CanvasLifecycle=CanvasLifecycle.IDLE
    feedback:CanvasFeedback=CanvasFeedback.NONE
    def __post_init__(self):
        if not self.workspace_id.strip(): raise ValueError("workspace_id must not be empty.")
        if not self.discipline.strip(): raise ValueError("discipline must not be empty.")

@dataclass(frozen=True, slots=True)
class CanvasInteractionContract:
    inputs:tuple[CanvasInput,...]=tuple(CanvasInput)
    feedback_states:tuple[CanvasFeedback,...]=tuple(CanvasFeedback)
    lifecycles:tuple[CanvasLifecycle,...]=tuple(CanvasLifecycle)
    def supports(self, operation:CanvasInput)->bool: return operation in self.inputs

class CanvasInteractionAdapter:
    def __init__(self, *, workspace_id:str, discipline:str,
                 on_feedback:Callable[[CanvasFeedback,str],None]|None=None):
        self._context=CanvasContext(workspace_id=workspace_id, discipline=discipline)
        self._on_feedback=on_feedback
    @property
    def context(self): return self._context
    @property
    def contract(self): return CanvasInteractionContract()
    def set_tool(self, tool_id:str|None):
        self._context=CanvasContext(self._context.workspace_id,self._context.discipline,tool_id,
            self._context.selected_object_ids,CanvasLifecycle.TOOL_ACTIVE if tool_id else CanvasLifecycle.IDLE,self._context.feedback)
        return self._context
    def set_selection(self, object_ids:tuple[Any,...]):
        self._context=CanvasContext(self._context.workspace_id,self._context.discipline,self._context.active_tool,
            tuple(object_ids),self._context.lifecycle,self._context.feedback)
        return self._context
    def feedback(self,state:CanvasFeedback,message:str):
        lifecycle=CanvasLifecycle.FEEDBACK if state in (CanvasFeedback.INVALID,CanvasFeedback.WARNING,CanvasFeedback.DEGRADED) else self._context.lifecycle
        self._context=CanvasContext(self._context.workspace_id,self._context.discipline,self._context.active_tool,
            self._context.selected_object_ids,lifecycle,state)
        if self._on_feedback: self._on_feedback(state,str(message))
        return self._context
    def cancel(self):
        self._context=CanvasContext(self._context.workspace_id,self._context.discipline,None,
            self._context.selected_object_ids,CanvasLifecycle.IDLE,CanvasFeedback.NONE)
        return self._context

__all__=["CanvasInput","CanvasFeedback","CanvasLifecycle","CanvasContext","CanvasInteractionContract","CanvasInteractionAdapter"]
