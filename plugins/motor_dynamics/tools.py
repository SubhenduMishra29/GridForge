"""Canvas adapter; all mutations dispatch immutable commands through Application."""
from __future__ import annotations
from typing import Any
from .commands import AddDraftMotorPlacementCommand, CommitMotorToNetworkCommand

class MotorPlacementTool:
    def __init__(self, application: Any, view: Any, command_dispatch: Any):
        self.application, self.view, self.command_dispatch = application, view, command_dispatch
        self._position = None; self._draft_id = None
    def mouse_move(self, scene_position: Any) -> None:
        self._position = (float(scene_position.x()), float(scene_position.y()))
        updater = getattr(self.view, "update_creation_draft_preview", None)
        if callable(updater): updater("motor", self._position)
    def mouse_release(self, scene_position: Any) -> Any:
        self._position = (float(scene_position.x()), float(scene_position.y()))
        lookup = getattr(self.view, "find_wire_at", None)
        hit = lookup(scene_position) if callable(lookup) else None
        if hit is None: return self.command_dispatch(AddDraftMotorPlacementCommand(self._new_id(), *self._position))
        motor_id = self._new_id()
        self.command_dispatch(AddDraftMotorPlacementCommand(motor_id, *self._position))
        wire_id, fraction = hit if isinstance(hit, tuple) else (str(hit), 0.5)
        return self.command_dispatch(CommitMotorToNetworkCommand(motor_id, str(wire_id), float(fraction)))
    @staticmethod
    def _new_id() -> str:
        from uuid import uuid4
        return "motor-" + uuid4().hex
    def cancel(self) -> None:
        self._position = None
        cancel = getattr(self.view, "clear_creation_draft_preview", None)
        if callable(cancel): cancel()
