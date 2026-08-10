# ============================================================
# File: ui/tools/line_tool.py
# GridForge Line Tool
# ============================================================
#
# PURPOSE
# -------
# Provides the interactive tool used to create electrical
# connections between two Bus objects.
#
#
# INTERACTION FLOW
# ----------------
#
#     Mouse Click 1
#          │
#          ▼
#     SnapSystem
#          │
#          ▼
#     Start Bus
#
#     Mouse Move
#          │
#          ▼
#     SnapSystem
#          │
#          ▼
#     Cursor / Bus Position
#          │
#          ▼
#     PreviewLayer
#
#     Mouse Click 2
#          │
#          ▼
#     SnapSystem
#          │
#          ▼
#     Destination Bus
#          │
#          ▼
#     Topology Validation
#          │
#          ▼
#     Graph.add_line(...)
#          │
#          ▼
#     Controller.model_changed()
#          │
#          ▼
#     RenderSystem
#
#
# RESPONSIBILITIES
# ----------------
#
# LineTool is responsible for:
#
#   - Maintaining line-drawing interaction state
#   - Selecting the start bus
#   - Selecting the destination bus
#   - Requesting snap information from SnapSystem
#   - Managing the temporary line preview
#   - Preventing self-connections
#   - Preventing duplicate lines
#   - Requesting creation of the model line
#
#
# LineTool DOES NOT:
# ------------------
#
#   - calculate snapping distances
#   - implement its own snap algorithm
#   - create QGraphicsItems
#   - directly manipulate the QGraphicsScene
#   - own the PreviewLayer
#   - create itself
#   - manage its own lifecycle
#   - render permanent graphics
#   - calculate electrical quantities
#
#
# ARCHITECTURAL OWNERSHIP
# -----------------------
#
# Controller
#     │
#     ├── Application state
#     ├── Model reference
#     └── Tool selection
#
# ToolManager
#     │
#     └── Tool lifecycle / active instance
#
# InteractionManager
#     │
#     ├── Qt event routing
#     ├── scene coordinates
#     ├── PreviewLayer
#     └── SnapSystem
#
# LineTool
#     │
#     └── Line interaction logic
#
# Graph / Model
#     │
#     └── Persistent electrical topology
#
# RenderSystem
#     │
#     └── Model → visual representation
#
#
# IMPORTANT
# ---------
#
# This tool uses the GridForge Qt abstraction.
#
# Direct imports from:
#
#     PySide6
#     PyQt6
#     PyQt5
#
# are prohibited here.
#
# ============================================================

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QPointF
from ui.core.tool_registry import register_tool


@register_tool("line")
class LineTool:
    """
    Interactive electrical line-creation tool.

    The tool creates a connection between two existing buses.

    A line can only be created when:

        1. A valid start bus has been selected.
        2. A different destination bus has been selected.
        3. An identical connection does not already exist.

    Spatial snapping is delegated completely to SnapSystem.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Any,
    ) -> None:
        """
        Initialize the LineTool.

        Parameters
        ----------
        controller:
            GridForge Controller.

            Provides access to:
                - domain model
                - application events
                - persistent application state

        interaction_manager:
            GridForge InteractionManager.

            Provides access to:
                - scene coordinates
                - PreviewLayer
                - centralized SnapSystem
        """

        # ----------------------------------------------------
        # Controller reference
        # ----------------------------------------------------
        #
        # The Controller is used as the bridge to the
        # application model and event system.
        #
        # The LineTool does not own the model.
        # ----------------------------------------------------

        self.controller = controller

        # ----------------------------------------------------
        # InteractionManager reference
        # ----------------------------------------------------
        #
        # InteractionManager owns the interaction infrastructure.
        #
        # The tool uses it rather than accessing the QGraphicsView
        # or PreviewLayer directly.
        # ----------------------------------------------------

        self.im = interaction_manager

        # ----------------------------------------------------
        # Centralized SnapSystem
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # LineTool must NOT calculate distances to buses itself.
        #
        # All tools must use the same snapping rules.
        #
        # Therefore the tool obtains the shared SnapSystem
        # from InteractionManager.
        # ----------------------------------------------------

        self.snap_system = self.im.snap_system

        # ====================================================
        # LINE INTERACTION STATE
        # ====================================================
        #
        # These values represent temporary interaction state.
        #
        # They are NOT part of the electrical model.
        # ----------------------------------------------------

        # Bus selected by the first mouse click.
        self.start_bus: Optional[Any] = None

        # Current resolved cursor position used by the preview.
        self.current_pos: Optional[QPointF] = None

    # ========================================================
    # TOOL LIFECYCLE
    # ========================================================

    def activate(self) -> None:
        """
        Activate the LineTool.

        ToolManager owns lifecycle management.

        Activation must start with a clean interaction state
        so an unfinished line from an earlier session cannot
        leak into the new interaction.
        """

        self.reset()

    # --------------------------------------------------------

    def deactivate(self) -> None:
        """
        Deactivate the LineTool.

        Any unfinished line interaction is cancelled.

        No persistent model data is modified here.
        """

        self.reset()

    # ========================================================
    # STATE MANAGEMENT
    # ========================================================

    def reset(self) -> None:
        """
        Reset all temporary line-drawing state.

        Reset performs three operations:

            1. Forget the selected start bus.
            2. Forget the current preview position.
            3. Remove temporary preview graphics.

        IMPORTANT:
        ----------
        This method never modifies the electrical model.
        """

        self.start_bus = None
        self.current_pos = None

        # PreviewLayer is owned by InteractionManager.
        #
        # The tool only requests that the preview be cleared.
        if self.im.preview is not None:
            self.im.preview.clear()

    # ========================================================
    # HOVER / SNAP INFORMATION
    # ========================================================

    def get_hover_bus(self) -> Optional[Any]:
        """
        Return the bus currently under the cursor.

        This method is primarily used by the renderer to provide
        visual hover feedback.

        The renderer can therefore ask:

            tool.get_hover_bus()

        without implementing its own spatial query.

        Returns
        -------
        Bus | None
            The nearest bus within SnapSystem's configured
            snapping radius, or None when no bus is close enough.
        """

        # InteractionManager maintains the authoritative
        # scene-space cursor position.
        pos = self.im.get_scene_position()

        if pos is None:
            return None

        # resolve_bus() performs a bus-only snap operation.
        #
        # It intentionally does not apply grid snapping because
        # hover highlighting requires an actual Bus target.
        return self.snap_system.resolve_bus(pos)

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> None:
        """
        Handle a mouse-press event.

        Interaction sequence
        --------------------
        First click:
            Select the starting bus.

        Second click:
            Select the destination bus and attempt to create
            the electrical line.

        The actual event routing is performed by
        InteractionManager.
        """

        # ----------------------------------------------------
        # Convert the mouse position to scene coordinates.
        # ----------------------------------------------------
        #
        # InteractionManager owns coordinate conversion.
        #
        # The tool therefore does not access QGraphicsView
        # directly.
        # ----------------------------------------------------

        pos = self.im.map_to_scene(event)

        # ----------------------------------------------------
        # Ask the centralized SnapSystem for a Bus.
        # ----------------------------------------------------
        #
        # LineTool requires actual Bus objects for topology
        # creation. Therefore resolve_bus() is used instead
        # of implementing a local distance calculation.
        # ----------------------------------------------------

        snapped_bus = self.snap_system.resolve_bus(pos)

        # ====================================================
        # FIRST CLICK
        # ====================================================

        if self.start_bus is None:

            # ------------------------------------------------
            # A first click is accepted only when it resolves
            # to a valid Bus.
            # ------------------------------------------------

            if snapped_bus is not None:

                self.start_bus = snapped_bus

                # Keep the preview state aligned with the
                # selected starting bus.
                self.current_pos = QPointF(
                    snapped_bus.x,
                    snapped_bus.y,
                )

            # ------------------------------------------------
            # If no bus was selected, simply ignore the click.
            #
            # The user can move the cursor and try again.
            # ------------------------------------------------

            return

        # ====================================================
        # SECOND CLICK
        # ====================================================

        # ----------------------------------------------------
        # The second click must also resolve to a Bus.
        #
        # Do not reset the interaction if it does not.
        #
        # This allows the user to continue searching for a
        # valid destination.
        # ----------------------------------------------------

        if snapped_bus is None:
            return

        # ----------------------------------------------------
        # Prevent connecting a bus to itself.
        #
        # This is a topology rule rather than a snapping rule.
        # ----------------------------------------------------

        if snapped_bus == self.start_bus:
            return

        # ----------------------------------------------------
        # Prevent duplicate physical connections.
        #
        # Direction is ignored because:
        #
        #     A → B
        #
        # and
        #
        #     B → A
        #
        # represent the same physical line for duplicate
        # detection.
        # ----------------------------------------------------

        if self._line_exists(
            self.start_bus.id,
            snapped_bus.id,
        ):

            # The attempted operation is complete from the
            # user's perspective, so cancel the unfinished
            # interaction.
            self.reset()

            return

        # ====================================================
        # CREATE MODEL LINE
        # ====================================================

        graph = self.controller.model.graph

        # ----------------------------------------------------
        # Request the persistent topology change from the
        # domain graph.
        #
        # LineTool does not create a LineItem.
        # It only modifies the model through the graph API.
        # ----------------------------------------------------

        graph.add_line(
            self.start_bus.id,
            snapped_bus.id,
            r=0.01,
            x=0.05,
            b=0.0,
        )

        # ----------------------------------------------------
        # Notify the Controller that the model has changed.
        #
        # RenderSystem and other interested systems can respond
        # through the Controller event system.
        # ----------------------------------------------------

        self.controller.model_changed()

        # ----------------------------------------------------
        # The line has now been successfully created.
        #
        # Clear the temporary interaction.
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
        Handle mouse movement.

        Before the first click:
            No line preview is displayed.

        After the first click:
            A temporary line is displayed from the starting
            bus to the resolved cursor position.

        The InteractionManager updates last_scene_pos before
        calling this method, so LineTool does not modify that
        state itself.
        """

        # ----------------------------------------------------
        # Convert mouse position to scene coordinates.
        # ----------------------------------------------------

        pos = self.im.map_to_scene(event)

        # ----------------------------------------------------
        # No start bus means that line drawing has not started.
        #
        # Hover detection remains available through
        # get_hover_bus().
        # ----------------------------------------------------

        if self.start_bus is None:
            return

        # ----------------------------------------------------
        # Resolve the cursor position through SnapSystem.
        #
        # SnapSystem applies the application's centralized
        # snapping rules:
        #
        #     Bus
        #       ↓
        #     Grid (if enabled)
        #       ↓
        #     Original cursor position
        # ----------------------------------------------------

        snap_result = self.snap_system.resolve(pos)

        # ----------------------------------------------------
        # Store the resolved position for the preview.
        # ----------------------------------------------------

        self.current_pos = snap_result.position

        # ----------------------------------------------------
        # Draw temporary preview.
        #
        # IMPORTANT:
        #
        # This is NOT a permanent model Line.
        #
        # PreviewLayer owns the temporary visual representation.
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

    def mouse_release(
        self,
        event: Any,
    ) -> None:
        """
        Handle mouse release.

        LineTool intentionally does not create lines on release.

        Line creation occurs on the second mouse press because
        the tool follows a two-click interaction model:

            Click → Start Bus
            Click → Destination Bus
        """

        pass

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle optional keyboard interaction.

        ESC cancellation is normally handled centrally by
        InteractionManager → ToolManager.

        Therefore LineTool does not need to implement ESC here.

        Returns
        -------
        bool
            False because this tool does not consume any
            additional keyboard commands at present.
        """

        return False

    # ========================================================
    # TOPOLOGY HELPERS
    # ========================================================

    def _line_exists(
        self,
        bus_a_id: str,
        bus_b_id: str,
    ) -> bool:
        """
        Determine whether a line already exists between two buses.

        Parameters
        ----------
        bus_a_id:
            ID of the first bus.

        bus_b_id:
            ID of the second bus.

        Returns
        -------
        bool
            True if a connection already exists.

        Notes
        -----
        Direction is deliberately ignored.

        Therefore both:

            A → B

        and:

            B → A

        are considered the same physical connection for
        duplicate detection.
        """

        graph = self.controller.model.graph

        # ----------------------------------------------------
        # Search existing graph lines.
        # ----------------------------------------------------

        for line in graph.all_lines():

            # ------------------------------------------------
            # Normal direction:
            #
            #     A → B
            # ------------------------------------------------

            if (
                line.from_bus == bus_a_id
                and line.to_bus == bus_b_id
            ):
                return True

            # ------------------------------------------------
            # Reverse direction:
            #
            #     B → A
            # ------------------------------------------------

            if (
                line.from_bus == bus_b_id
                and line.to_bus == bus_a_id
            ):
                return True

        return False

    # ========================================================
    # DEBUG / INTROSPECTION
    # ========================================================

    def get_state(self) -> dict:
        """
        Return diagnostic state for debugging.

        This method is intentionally read-only.

        Returns
        -------
        dict
            Current line-tool interaction state.
        """

        return {
            "start_bus": (
                self.start_bus.id
                if self.start_bus is not None
                else None
            ),
            "current_pos": self.current_pos,
            "drawing": self.start_bus is not None,
        }

    # --------------------------------------------------------

    def __repr__(self) -> str:
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

