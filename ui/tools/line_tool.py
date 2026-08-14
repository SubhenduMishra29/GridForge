# ============================================================
# File: ui/tools/line_tool.py
# GridForge V2 — Line Tool
# ============================================================
"""
Interactive electrical line-creation tool for GridForge.

Responsibilities
----------------
LineTool is responsible for:

    - maintaining two-click line-creation state;
    - resolving buses through the centralized SnapSystem;
    - requesting temporary line previews;
    - preventing self-connections;
    - preventing duplicate connections;
    - requesting persistent line creation through Controller.

LineTool does NOT:

    - own QGraphicsScene;
    - perform coordinate conversion itself;
    - implement snapping algorithms;
    - create QGraphicsItems;
    - render permanent graphics;
    - own PreviewLayer;
    - directly mutate Core objects;
    - create commands directly;
    - perform electrical calculations.

Architecture
------------

    InteractionManager
        │
        ├── coordinate conversion
        ├── SnapSystem
        └── PreviewLayer
                │
                ▼
             LineTool
                │
                ▼
            Controller
                │
                ▼
          Command / Core
                │
                ▼
          RenderSystem

Interaction
-----------

    First click
        ↓
    Resolve start Bus
        ↓
    Mouse movement
        ↓
    Resolve preview position
        ↓
    PreviewLayer
        ↓
    Second click
        ↓
    Resolve destination Bus
        ↓
    Validate topology constraints
        ↓
    Controller.create_line(...)
        ↓
    Reset interaction

ToolManager owns activation/deactivation.

Qt Architecture
---------------

All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QPointF
from ui.core.tool_registry import register_tool


@register_tool("line")
class LineTool:
    """
    Interactive electrical line-creation tool.

    A line is created between two distinct existing buses.

    Snapping and temporary graphics are delegated to the
    centralized interaction infrastructure.
    """

    tool_id = "line"

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Any,
    ) -> None:
        """
        Initialize LineTool.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if interaction_manager is None:
            raise ValueError(
                "interaction_manager must not be None."
            )

        self.controller = controller
        self.im = interaction_manager

        self.snap_system = getattr(
            interaction_manager,
            "snap_system",
            None,
        )

        if self.snap_system is None:
            raise AttributeError(
                "InteractionManager must provide "
                "snap_system."
            )

        # ----------------------------------------------------
        # Temporary interaction state.
        # ----------------------------------------------------

        self.start_bus: Optional[Any] = None
        self.current_pos: Optional[QPointF] = None

    # ========================================================
    # TOOL LIFECYCLE
    # ========================================================

    def activate(self) -> None:
        """
        Activate the tool with a clean interaction state.
        """

        self.reset()

    # --------------------------------------------------------

    def deactivate(self) -> None:
        """
        Deactivate the tool and cancel unfinished interaction.
        """

        self.reset()

    # --------------------------------------------------------

    def reset(self) -> None:
        """
        Cancel the current line interaction.

        No persistent model state is modified.
        """

        self.start_bus = None
        self.current_pos = None

        self._clear_preview()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> None:
        """
        Handle one stage of the two-click line interaction.

        First click:
            Select start Bus.

        Second click:
            Validate destination and request line creation.
        """

        position = self.im.map_to_scene(
            event
        )

        if position is None:
            return

        snapped_bus = self._resolve_bus(
            position
        )

        # ====================================================
        # FIRST CLICK
        # ====================================================

        if self.start_bus is None:

            if snapped_bus is None:
                return

            self.start_bus = snapped_bus

            self.current_pos = QPointF(
                snapped_bus.x,
                snapped_bus.y,
            )

            return

        # ====================================================
        # SECOND CLICK
        # ====================================================

        if snapped_bus is None:
            return

        # ----------------------------------------------------
        # Prevent self-connection.
        # ----------------------------------------------------

        if self._same_bus(
            self.start_bus,
            snapped_bus,
        ):
            return

        # ----------------------------------------------------
        # Prevent duplicate connection.
        # ----------------------------------------------------

        if self._line_exists(
            self.start_bus.id,
            snapped_bus.id,
        ):
            self.reset()
            return

        # ----------------------------------------------------
        # Request persistent topology mutation through
        # Controller.
        # ----------------------------------------------------

        self._create_line(
            self.start_bus,
            snapped_bus,
        )

        # ----------------------------------------------------
        # Successful creation ends the interaction.
        # ----------------------------------------------------

        self.reset()

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> None:
        """
        Update the temporary line preview.
        """

        if self.start_bus is None:
            return

        position = self.im.map_to_scene(
            event
        )

        if position is None:
            return

        snap_result = self._resolve_position(
            position
        )

        if snap_result is None:
            return

        self.current_pos = snap_result

        self._show_preview(
            QPointF(
                self.start_bus.x,
                self.start_bus.y,
            ),
            self.current_pos,
        )

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> None:
        """
        Handle mouse release.

        Line creation intentionally occurs on the second mouse
        press, not on release.
        """

        return

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle optional keyboard interaction.

        Escape cancels the unfinished line.
        """

        if self._is_escape_key(
            event.key()
        ):
            self.reset()
            return True

        return False

    # ========================================================
    # BUS RESOLUTION
    # ========================================================

    def _resolve_bus(
        self,
        position: QPointF,
    ) -> Optional[Any]:
        """
        Resolve a Bus using the centralized SnapSystem.
        """

        resolve_bus = getattr(
            self.snap_system,
            "resolve_bus",
            None,
        )

        if not callable(resolve_bus):
            raise AttributeError(
                "SnapSystem must provide "
                "resolve_bus(position)."
            )

        return resolve_bus(
            position
        )

    # ========================================================
    # POSITION RESOLUTION
    # ========================================================

    def _resolve_position(
        self,
        position: QPointF,
    ) -> Optional[QPointF]:
        """
        Resolve a cursor position through SnapSystem.
        """

        resolve = getattr(
            self.snap_system,
            "resolve",
            None,
        )

        if not callable(resolve):
            return QPointF(
                position.x(),
                position.y(),
            )

        result = resolve(
            position
        )

        resolved_position = getattr(
            result,
            "position",
            None,
        )

        if resolved_position is None:
            return None

        return resolved_position

    # ========================================================
    # PREVIEW
    # ========================================================

    def _show_preview(
        self,
        start: QPointF,
        end: QPointF,
    ) -> None:
        """
        Request a temporary line preview.

        PreviewLayer remains owned by InteractionManager.
        """

        preview = getattr(
            self.im,
            "preview",
            None,
        )

        if preview is None:
            return

        show_line = getattr(
            preview,
            "show_line",
            None,
        )

        if callable(show_line):
            show_line(
                start,
                end,
            )

    # --------------------------------------------------------

    def _clear_preview(
        self,
    ) -> None:
        """
        Clear any temporary line preview.
        """

        preview = getattr(
            self.im,
            "preview",
            None,
        )

        if preview is None:
            return

        clear = getattr(
            preview,
            "clear",
            None,
        )

        if callable(clear):
            clear()

    # ========================================================
    # MODEL MUTATION
    # ========================================================

    def _create_line(
        self,
        start_bus: Any,
        end_bus: Any,
    ) -> Any:
        """
        Request persistent line creation through Controller.

        The tool deliberately does not call graph.add_line()
        directly.

        Controller owns the application mutation boundary.
        """

        create_line = getattr(
            self.controller,
            "create_line",
            None,
        )

        if not callable(create_line):
            raise AttributeError(
                "Controller must provide "
                "create_line()."
            )

        return create_line(
            start_bus.id,
            end_bus.id,
        )

    # ========================================================
    # TOPOLOGY VALIDATION
    # ========================================================

    def _line_exists(
        self,
        bus_a_id: str,
        bus_b_id: str,
    ) -> bool:
        """
        Determine whether a connection already exists.

        Direction is ignored because the physical connection
        between two buses is treated as identical in either
        direction.
        """

        model = getattr(
            self.controller,
            "model",
            None,
        )

        if model is None:
            raise AttributeError(
                "Controller must provide model."
            )

        graph = getattr(
            model,
            "graph",
            None,
        )

        if graph is None:
            raise AttributeError(
                "Controller model must provide graph."
            )

        all_lines = getattr(
            graph,
            "all_lines",
            None,
        )

        if not callable(all_lines):
            raise AttributeError(
                "Graph must provide all_lines()."
            )

        for line in all_lines():

            from_bus = getattr(
                line,
                "from_bus",
                None,
            )

            to_bus = getattr(
                line,
                "to_bus",
                None,
            )

            if (
                from_bus == bus_a_id
                and to_bus == bus_b_id
            ):
                return True

            if (
                from_bus == bus_b_id
                and to_bus == bus_a_id
            ):
                return True

        return False

    # --------------------------------------------------------

    @staticmethod
    def _same_bus(
        bus_a: Any,
        bus_b: Any,
    ) -> bool:
        """
        Determine whether two resolved buses represent the same
        model object.
        """

        if bus_a is bus_b:
            return True

        bus_a_id = getattr(
            bus_a,
            "id",
            None,
        )

        bus_b_id = getattr(
            bus_b,
            "id",
            None,
        )

        return (
            bus_a_id is not None
            and bus_a_id == bus_b_id
        )

    # ========================================================
    # HOVER
    # ========================================================

    def get_hover_bus(self) -> Optional[Any]:
        """
        Return the currently resolved hover Bus.

        Returns None when the cursor is not over a valid bus.
        """

        position = self._get_scene_position()

        if position is None:
            return None

        return self._resolve_bus(
            position
        )

    # --------------------------------------------------------

    def _get_scene_position(
        self,
    ) -> Optional[QPointF]:
        """
        Obtain the current scene position from
        InteractionManager.
        """

        getter = getattr(
            self.im,
            "get_scene_position",
            None,
        )

        if not callable(getter):
            return None

        return getter()

    # ========================================================
    # KEY HELPERS
    # ========================================================

    @staticmethod
    def _is_escape_key(
        key: Any,
    ) -> bool:
        """
        Detect the Qt Escape key without a direct Qt binding
        import.
        """

        key_type = type(
            key
        )

        escape = getattr(
            key_type,
            "Key_Escape",
            None,
        )

        if escape is None:
            return False

        return key == escape

    # ========================================================
    # STATE / DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return read-only diagnostic state.
        """

        return {
            "tool_id": self.tool_id,
            "start_bus": (
                self.start_bus.id
                if self.start_bus is not None
                else None
            ),
            "current_pos": self.current_pos,
            "drawing": (
                self.start_bus is not None
            ),
        }

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        start_bus_id = (
            self.start_bus.id
            if self.start_bus is not None
            else None
        )

        return (
            "LineTool("
            f"start_bus={start_bus_id!r}, "
            f"current_pos={self.current_pos!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "LineTool",
]
```
