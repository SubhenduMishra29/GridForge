# ============================================================
# File: ui/tools/line_tool.py
# GridForge Line Tool
#
# Features:
#   - Snap-to-Bus through centralized SnapSystem
#   - Preview line
#   - Hover bus detection
#   - Duplicate line prevention
#   - Qt abstraction layer
#   - Topology-aware line creation
# ============================================================

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QPointF
from ui.core.tool_registry import register_tool


@register_tool("line")
class LineTool:
    """
    GridForge line drawing tool.

    Flow
    ----
    Click 1
        Select start bus through SnapSystem.

    Mouse Move
        Resolve cursor position through SnapSystem and
        update the temporary preview line.

    Click 2
        Select destination bus and create a model line.

    Responsibilities
    ----------------
    - Line interaction state
    - Line topology validation
    - Preview control
    - Requesting snapping from SnapSystem

    The tool does NOT implement spatial snapping itself.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Any,
    ) -> None:

        self.controller = controller
        self.im = interaction_manager

        # ----------------------------------------------------
        # Shared snapping service
        # ----------------------------------------------------
        #
        # InteractionManager owns the canvas interaction
        # infrastructure, including the shared SnapSystem.
        #
        # No tool-specific SnapSystem is created here.
        # ----------------------------------------------------

        self.snap_system = self.im.snap_system

        # ----------------------------------------------------
        # Line interaction state
        # ----------------------------------------------------

        self.start_bus: Optional[Any] = None
        self.current_pos: Optional[QPointF] = None

    # ========================================================
    # ACTIVATION / DEACTIVATION
    # ========================================================

    def activate(self) -> None:
        """
        Called when LineTool becomes the active tool.

        Ensures no stale drawing state remains from a
        previous interaction.
        """

        self.reset()

    # --------------------------------------------------------

    def deactivate(self) -> None:
        """
        Called when LineTool is deactivated.
        """

        self.reset()

    # ========================================================
    # STATE MANAGEMENT
    # ========================================================

    def reset(self) -> None:
        """
        Reset all temporary line-tool state.

        This does NOT modify the model.
        """

        self.start_bus = None
        self.current_pos = None

        if self.im.preview is not None:
            self.im.preview.clear()

    # ========================================================
    # SNAP / HOVER
    # ========================================================

    def get_hover_bus(self) -> Optional[Any]:
        """
        Return the bus currently under the snapping cursor.

        This method is intentionally retained because
        BusRenderer uses it for hover highlighting.

        Returns
        -------
        Bus | None
        """

        pos = self.im.get_scene_position()

        if pos is None:
            return None

        return self.snap_system.resolve_bus(pos)

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(self, event: Any) -> None:
        """
        Handle mouse press.

        First click:
            Select start bus.

        Second click:
            Validate destination bus and create line.
        """

        pos = self.im.map_to_scene(event)

        # ----------------------------------------------------
        # Resolve bus through centralized SnapSystem.
        # ----------------------------------------------------

        snapped_bus = self.snap_system.resolve_bus(pos)

        # ====================================================
        # FIRST CLICK
        # ====================================================

        if self.start_bus is None:

            if snapped_bus is not None:
                self.start_bus = snapped_bus

                # Keep preview state synchronized.
                self.current_pos = QPointF(
                    snapped_bus.x,
                    snapped_bus.y,
                )

            return

        # ====================================================
        # SECOND CLICK
        # ====================================================

        # ----------------------------------------------------
        # Invalid destination.
        #
        # Do not reset the tool.
        # User can move to another bus and try again.
        # ----------------------------------------------------

        if snapped_bus is None:
            return

        # ----------------------------------------------------
        # Prevent self-connection.
        # ----------------------------------------------------

        if snapped_bus == self.start_bus:
            return

        # ----------------------------------------------------
        # Check duplicate line.
        # ----------------------------------------------------

        if self._line_exists(
            self.start_bus.id,
            snapped_bus.id,
        ):
            self.reset()
            return

        # ----------------------------------------------------
        # Create model line.
        # ----------------------------------------------------

        graph = self.controller.model.graph

        graph.add_line(
            self.start_bus.id,
            snapped_bus.id,
            r=0.01,
            x=0.05,
            b=0.0,
        )

        # ----------------------------------------------------
        # Notify through Controller API.
        # ----------------------------------------------------

        self.controller.model_changed()

        # ----------------------------------------------------
        # Completed line interaction.
        # ----------------------------------------------------

        self.reset()

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(self, event: Any) -> None:
        """
        Update cursor state and line preview.

        Hover detection works even before the first click.
        """

        pos = self.im.map_to_scene(event)

        # ----------------------------------------------------
        # InteractionManager normally updates this itself.
        #
        # Keeping the assignment here is harmless and makes
        # the tool robust when called independently.
        # ----------------------------------------------------

        self.im.last_scene_pos = pos

        # ----------------------------------------------------
        # No line is currently being drawn.
        #
        # Hover information is still available through
        # get_hover_bus().
        # ----------------------------------------------------

        if self.start_bus is None:
            return

        # ----------------------------------------------------
        # Resolve cursor through centralized SnapSystem.
        # ----------------------------------------------------

        snap_result = self.snap_system.resolve(pos)

        self.current_pos = snap_result.position

        # ----------------------------------------------------
        # Draw temporary preview.
        # ----------------------------------------------------

        self.im.preview.show_line(
            QPointF(
                self.start_bus.x,
                self.start_bus.y,
            ),
            self.current_pos,
        )

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(self, event: Any) -> None:
        """
        Mouse release is intentionally unused.

        Line creation occurs on the second click rather than
        on mouse release.
        """

        pass

    # ========================================================
    # TOPOLOGY HELPERS
    # ========================================================

    def _line_exists(
        self,
        bus_a_id: str,
        bus_b_id: str,
    ) -> bool:
        """
        Determine whether a line already exists between
        two buses.

        Direction is ignored because the physical connection
        is treated as undirected for duplicate detection.
        """

        graph = self.controller.model.graph

        for line in graph.all_lines():

            if (
                line.from_bus == bus_a_id
                and line.to_bus == bus_b_id
            ):
                return True

            if (
                line.from_bus == bus_b_id
                and line.to_bus == bus_a_id
            ):
                return True

        return False

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return concise diagnostic state.
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
```
