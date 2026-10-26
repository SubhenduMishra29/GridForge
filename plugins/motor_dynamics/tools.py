"""Canvas adapter; all mutations dispatch immutable commands through Application."""
from __future__ import annotations

from typing import Any

from .commands import AddDraftMotorPlacementCommand, ConnectMotorToBusCommand


class MotorPlacementTool:
    """Place a motor draft and optionally connect it to a Bus attachment.

    Motors are one-terminal injection/load equipment, not series elements.
    This tool deliberately never inserts a motor into or splits an existing wire.
    """

    def __init__(self, application: Any, view: Any, command_dispatch: Any):
        self.application = application
        self.view = view
        self.command_dispatch = command_dispatch
        self._position = None
        self._draft_id = None

    def mouse_move(self, scene_position: Any) -> None:
        self._position = (float(scene_position.x()), float(scene_position.y()))
        updater = getattr(self.view, "update_creation_draft_preview", None)
        if callable(updater):
            updater("motor", self._position)

    def mouse_release(self, scene_position: Any) -> Any:
        self._position = (float(scene_position.x()), float(scene_position.y()))
        self._draft_id = self._new_id()

        # A Bus hit is optional. If the host canvas exposes the canonical
        # attachment hit-test, validate its result before creating any draft.
        lookup = getattr(self.view, "find_bus_attachment_at", None)
        hit = lookup(scene_position) if callable(lookup) else None
        bus_id = attachment_id = None
        if hit is not None:
            if not isinstance(hit, (tuple, list)) or len(hit) != 2:
                raise ValueError(
                    "find_bus_attachment_at must return (bus_id, attachment_id) or None."
                )
            bus_id, attachment_id = (str(value).strip() for value in hit)
            if not bus_id or not attachment_id:
                raise ValueError("Bus attachment hit-test returned an empty identity.")

        placed = self.command_dispatch(
            AddDraftMotorPlacementCommand(self._draft_id, *self._position)
        )
        if hit is None:
            return placed

        # Connection remains a separate typed Application command. If the
        # host cannot resolve/execute it, the motor remains an editable draft
        # rather than having mutated Core topology or split an existing wire.
        return self.command_dispatch(
            ConnectMotorToBusCommand(self._draft_id, bus_id, attachment_id)
        )

    @staticmethod
    def _new_id() -> str:
        from uuid import uuid4
        return "motor-" + uuid4().hex

    def cancel(self) -> None:
        self._position = None
        self._draft_id = None
        cancel = getattr(self.view, "clear_creation_draft_preview", None)
        if callable(cancel):
            cancel()
