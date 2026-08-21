# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/tools/line_tool.py
#
# Purpose:
#     SLD line-connection interaction tool.
#
# Architectural Role:
#     LineTool resolves two scene-space endpoints through the
#     canonical SnapSystem and maintains only transient drawing
#     intent.
#
# IMPORTANT:
#     The current repository does not expose a confirmed
#     Core CreateLine command/factory. Therefore this tool does
#     NOT invent one and does NOT mutate Core directly.
#
# ============================================================

from __future__ import annotations

from typing import Any, Optional, Tuple

from .tool_base import ToolBase


class LineTool(ToolBase):
    """
    SLD line-connection tool.

    Interaction model:

        first endpoint
            ↓
        transient preview
            ↓
        second endpoint
            ↓
        Core-backed line creation command

    The final Core mutation remains outside this tool until the
    actual Core command contract exists.
    """

    TOOL_ID = "line"

    def __init__(
        self,
        controller: Any,
        command_manager: Any,
        selection_manager: Any,
        snap_system: Any,
        renderer_registry: Any,
    ) -> None:
        super().__init__(
            controller=controller,
            command_manager=command_manager,
            selection_manager=selection_manager,
            snap_system=snap_system,
            renderer_registry=renderer_registry,
        )

        self._start_position: Optional[
            Tuple[float, float]
        ] = None

        self._current_position: Optional[
            Tuple[float, float]
        ] = None

        self._preview_active = False

    # ========================================================
    # METADATA
    # ========================================================

    @property
    def tool_id(self) -> str:
        """Return the stable tool identifier."""
        return self.TOOL_ID

    @property
    def name(self) -> str:
        """Return the user-facing tool name."""
        return "Line"

    @property
    def description(self) -> str:
        """Return the SLD line-connection tool description."""
        return "Create a connection between two SLD endpoints."

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def on_activate(self) -> None:
        """Reset transient line state."""
        self._clear_state()

    def on_deactivate(self) -> None:
        """Clear transient line state."""
        self._clear_state()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def on_mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Start or finish a line interaction.

        First click:
            establish start endpoint.

        Second click:
            establish end endpoint and request the Core
            command boundary.
        """

        self._ensure_active()

        position = self._snap_position(event)

        if position is None:
            return False

        if self._start_position is None:
            self._start_position = position
            self._current_position = position
            self._preview_active = True
            return True

        self._current_position = position

        self._require_line_command_boundary()

        return False

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def on_mouse_move(
        self,
        event: Any,
    ) -> bool:
        """Update the transient line preview."""

        self._ensure_active()

        if self._start_position is None:
            return False

        position = self._snap_position(event)

        if position is None:
            return False

        self._current_position = position
        self._preview_active = True

        return True

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def on_mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Release the pointer without independently committing
        the line.

        Line completion is intentionally controlled by the
        endpoint-selection interaction in on_mouse_press().
        """

        self._ensure_active()

        return self._start_position is not None

    # --------------------------------------------------------

    def on_mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        A double-click does not introduce a separate line
        creation path.
        """

        return self.on_mouse_press(event)

    # ========================================================
    # KEYBOARD
    # ========================================================

    def on_key_press(
        self,
        event: Any,
    ) -> bool:
        """Handle keyboard input owned by LineTool."""

        self._ensure_active()

        if self._is_escape_event(event):
            return self.on_cancel()

        return False

    # ========================================================
    # CANCEL / RESET
    # ========================================================

    def on_cancel(self) -> bool:
        """Cancel the current line preview."""

        self._ensure_active()

        had_state = (
            self._start_position is not None
            or self._current_position is not None
            or self._preview_active
        )

        self._clear_state()

        return had_state

    def on_reset(self) -> None:
        """Reset transient line state."""

        self._ensure_active()
        self._clear_state()

    # ========================================================
    # SNAP
    # ========================================================

    def _snap_position(
        self,
        event: Any,
    ) -> Optional[Tuple[float, float]]:
        """
        Resolve a scene-space pointer position through the
        canonical SnapSystem.snap() API.
        """

        scene_position = self.event_position(event)

        snap_system = self.get_snap_system()

        snap = getattr(
            snap_system,
            "snap",
            None,
        )

        if not callable(snap):
            raise TypeError(
                "SnapSystem must provide snap()."
            )

        result = snap(
            scene_position,
            allow_grid=True,
            allow_object=True,
        )

        position = getattr(
            result,
            "position",
            None,
        )

        if position is None:
            return None

        return self._position_tuple(position)

    # ========================================================
    # COMMAND BOUNDARY
    # ========================================================

    @staticmethod
    def _require_line_command_boundary() -> None:
        """
        Fail explicitly until the Core line-creation command is
        defined.

        This prevents speculative command factories and direct
        model mutation.
        """

        raise RuntimeError(
            "Line creation requires a confirmed Core line-creation "
            "command. No CreateLine command is currently exposed "
            "by the GridForge Core command API."
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _position_tuple(
        position: Any,
    ) -> Tuple[float, float]:
        """Convert a QPointF-like object or pair to a tuple."""

        if hasattr(position, "x") and hasattr(position, "y"):
            x = position.x()
            y = position.y()
            return float(x), float(y)

        if isinstance(position, (tuple, list)) and len(position) >= 2:
            return float(position[0]), float(position[1])

        raise TypeError(
            "SnapResult.position must provide x/y coordinates "
            "or a two-element position."
        )

    # --------------------------------------------------------

    @staticmethod
    def _is_escape_event(
        event: Any,
    ) -> bool:
        """Recognize Escape without importing Qt."""

        if event is None:
            return False

        key = getattr(
            event,
            "key",
            None,
        )

        if callable(key):
            key = key()

        if isinstance(event, dict):
            key = event.get(
                "key",
                key,
            )

        if key in (
            "Escape",
            "escape",
            0x01000000,
        ):
            return True

        return False

    # --------------------------------------------------------

    def _clear_state(self) -> None:
        """Clear all transient line state."""

        self._start_position = None
        self._current_position = None
        self._preview_active = False

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """Return the base tool state plus line state."""

        state = super().get_state()

        state.update(
            {
                "start_position": self._start_position,
                "current_position": self._current_position,
                "preview_active": self._preview_active,
            }
        )

        return state


__all__ = [
    "LineTool",
]
