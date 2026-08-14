# ============================================================
# File: ui/tools/line_tool.py
# GridForge V2 — Line Tool
# ============================================================
"""
Line creation tool for GridForge V2.

LineTool implements the two-stage interaction required to create
an electrical line between two valid connection points.

Architecture
------------

    GraphicsView
         │
         ▼
    InteractionManager
         │
         ▼
      LineTool
         │
         ├── SnapSystem
         │
         └── CommandManager
                 │
                 ▼
        Application Controller
                 │
                 ▼
                Core

Interaction
------------

    First click
        │
        ▼
    acquire start point
        │
        ▼
    pointer movement
        │
        ▼
    update transient preview
        │
        ▼
    second click
        │
        ▼
    acquire end point
        │
        ▼
    submit line-creation command
        │
        ▼
    reset interaction

The electrical topology remains authoritative in Core.

Responsibilities
----------------
LineTool:

    - acquire a first connection point;
    - acquire a second connection point;
    - use the existing SnapSystem when available;
    - maintain transient endpoint state;
    - expose preview geometry information;
    - submit the canonical line-creation command;
    - cancel an incomplete line operation.

LineTool does NOT:

    - create Core Line objects directly;
    - mutate Network/Topology;
    - decide whether a connection is electrically valid;
    - own permanent graphics;
    - render the preview;
    - maintain command history;
    - bypass CommandManager;
    - invent a secondary CAD topology.

Preview
-------
LineTool exposes preview state to the canvas/rendering layer.

The tool does not create QGraphicsItems itself.

Connection points
-----------------
The preferred interaction event contract exposes an explicit
connection-point reference:

    event.connection_point

or:

    event.terminal
    event.terminal_id
    event.object_id

The SnapSystem may additionally resolve a scene position to a
valid connection target.

The exact electrical validity remains a Core concern.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.tools.tool_base import ToolBase


class LineTool(ToolBase):
    """
    Tool for creating an electrical line between two endpoints.

    A LineTool instance has at most one transient start endpoint.
    """

    TOOL_ID = "line"

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        *,
        command_manager: Optional[Any] = None,
        selection_manager: Optional[Any] = None,
        snap_system: Optional[Any] = None,
        renderer_registry: Optional[Any] = None,
    ) -> None:
        """
        Initialize LineTool.
        """

        super().__init__(
            controller,
            command_manager=command_manager,
            selection_manager=selection_manager,
            snap_system=snap_system,
            renderer_registry=renderer_registry,
        )

        self._start_point: Any = None
        self._current_point: Any = None

        self._start_position: Any = None
        self._current_position: Any = None

        self._preview_active = False

        self._creation_count = 0

    # ========================================================
    # IDENTITY
    # ========================================================

    @property
    def tool_id(
        self,
    ) -> str:
        """
        Stable ToolManager identifier.
        """

        return self.TOOL_ID

    # --------------------------------------------------------

    @property
    def name(
        self,
    ) -> str:
        """
        Human-readable tool name.
        """

        return "Line"

    # --------------------------------------------------------

    @property
    def description(
        self,
    ) -> str:
        """
        Human-readable tool description.
        """

        return "Create an electrical line between two connection points."

    # ========================================================
    # STATE
    # ========================================================

    @property
    def has_start_point(
        self,
    ) -> bool:
        """
        Return True when the first endpoint has been acquired.
        """

        return self._start_point is not None

    # --------------------------------------------------------

    @property
    def preview_active(
        self,
    ) -> bool:
        """
        Return whether a transient line preview is active.
        """

        return self._preview_active

    # --------------------------------------------------------

    @property
    def start_point(
        self,
    ) -> Any:
        """
        Return the transient first endpoint.
        """

        return self._start_point

    # --------------------------------------------------------

    @property
    def current_point(
        self,
    ) -> Any:
        """
        Return the transient current endpoint.
        """

        return self._current_point

    # --------------------------------------------------------

    @property
    def start_position(
        self,
    ) -> Any:
        """
        Return the scene-space first endpoint position.
        """

        return self._start_position

    # --------------------------------------------------------

    @property
    def current_position(
        self,
    ) -> Any:
        """
        Return the scene-space current endpoint position.
        """

        return self._current_position

    # ========================================================
    # ACTIVATION
    # ========================================================

    def on_activate(
        self,
    ) -> None:
        """
        Reset transient line state.
        """

        self._clear_state()

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def on_deactivate(
        self,
    ) -> None:
        """
        Cancel any incomplete line interaction.
        """

        self._clear_state()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def on_mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Begin or complete a line endpoint interaction.

        Press is intentionally used only to acquire endpoint
        intent. The release event completes the operation.
        """

        point = self._resolve_connection_point(
            event
        )

        position = self._resolve_position(
            event,
            point,
        )

        if point is None:
            return True

        if not self.has_start_point:
            self._start_point = point
            self._start_position = position
            self._current_point = point
            self._current_position = position
            self._preview_active = True
            return True

        self._current_point = point
        self._current_position = position

        return True

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def on_mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Update transient line preview.

        If a start endpoint has not yet been selected, movement
        is ignored.

        The SnapSystem is consulted when available.
        """

        if not self.has_start_point:
            return False

        point = self._resolve_connection_point(
            event,
            allow_position_fallback=True,
        )

        position = self._resolve_position(
            event,
            point,
        )

        if point is not None:
            self._current_point = point

        if position is not None:
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
        Acquire or complete a line endpoint.

        A valid second endpoint causes one command submission.

        An invalid/empty second endpoint leaves the first endpoint
        intact so the user can continue the operation.
        """

        point = self._resolve_connection_point(
            event
        )

        position = self._resolve_position(
            event,
            point,
        )

        if point is None:
            return True

        if not self.has_start_point:
            self._start_point = point
            self._start_position = position
            self._current_point = point
            self._current_position = position
            self._preview_active = True
            return True

        if self._same_endpoint(
            self._start_point,
            point,
        ):
            # A zero-length electrical connection is not submitted.
            # The current start point remains active.
            self._current_point = point
            self._current_position = position
            return True

        self._current_point = point
        self._current_position = position

        command = self._build_create_command(
            self._start_point,
            point,
            self._start_position,
            position,
        )

        if command is None:
            raise RuntimeError(
                "Unable to create the line command. "
                "The application controller or command manager "
                "must expose a canonical line-creation command path."
            )

        self.execute_command(
            command
        )

        self._creation_count += 1

        self._clear_state()

        return True

    # ========================================================
    # DOUBLE CLICK
    # ========================================================

    def on_mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Consume double-clicks without creating an additional line.

        Line creation remains a two-endpoint operation.
        """

        return True

    # ========================================================
    # KEYBOARD
    # ========================================================

    def on_key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle line-tool keyboard input.

        Escape is handled by ToolBase.
        """

        return False

    # ========================================================
    # CANCEL
    # ========================================================

    def on_cancel(
        self,
    ) -> bool:
        """
        Cancel an incomplete line operation.
        """

        had_state = (
            self._start_point is not None
            or self._current_point is not None
            or self._preview_active
        )

        self._clear_state()

        return had_state

    # ========================================================
    # RESET
    # ========================================================

    def on_reset(
        self,
    ) -> None:
        """
        Reset transient line state.
        """

        self._clear_state()

    # ========================================================
    # SNAP / CONNECTION RESOLUTION
    # ========================================================

    def _resolve_connection_point(
        self,
        event: Any,
        *,
        allow_position_fallback: bool = False,
    ) -> Any:
        """
        Resolve a connection point from an interaction event.

        Resolution order:

            1. Explicit event connection point.
            2. Explicit terminal reference.
            3. SnapSystem resolution.

        A raw object ID is not automatically considered a valid
        terminal because the electrical connection contract belongs
        to the topology/model layer.
        """

        if event is None:
            return None

        # ----------------------------------------------------
        # Explicit connection-point contract.
        # ----------------------------------------------------

        for attribute in (
            "connection_point",
            "connection",
            "terminal",
        ):
            value = getattr(
                event,
                attribute,
                None,
            )

            if callable(value):
                try:
                    value = value()
                except TypeError:
                    value = None

            if value is not None:
                return value

        # ----------------------------------------------------
        # Explicit terminal identifier.
        # ----------------------------------------------------

        for attribute in (
            "terminal_id",
            "connection_point_id",
        ):
            value = getattr(
                event,
                attribute,
                None,
            )

            if callable(value):
                try:
                    value = value()
                except TypeError:
                    value = None

            if value is not None:
                return value

        # ----------------------------------------------------
        # SnapSystem.
        # ----------------------------------------------------

        snap_system = self.snap_system

        if snap_system is not None:
            position = self._extract_position(
                event
            )

            if position is not None:
                result = self._snap(
                    snap_system,
                    position,
                )

                if result is not None:
                    return result

        # ----------------------------------------------------
        # A raw position is never promoted to an electrical
        # endpoint unless the caller explicitly provides such
        # a contract.
        # ----------------------------------------------------

        if allow_position_fallback:
            return None

        return None

    # --------------------------------------------------------

    @staticmethod
    def _snap(
        snap_system: Any,
        position: Any,
    ) -> Any:
        """
        Resolve a scene position through SnapSystem.

        Supports the canonical snap/resolve method names while
        keeping the tool independent of SnapSystem internals.
        """

        for method_name in (
            "snap",
            "resolve",
            "snap_position",
            "find_connection",
            "find_connection_point",
        ):
            method = getattr(
                snap_system,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                result = method(
                    position
                )
            except TypeError:
                continue

            if result is not None:
                return result

        return None

    # ========================================================
    # POSITION RESOLUTION
    # ========================================================

    @staticmethod
    def _resolve_position(
        event: Any,
        point: Any,
    ) -> Any:
        """
        Resolve the scene-space position associated with an
        endpoint.
        """

        if event is not None:
            position = LineTool._extract_position(
                event
            )

            if position is not None:
                return position

        if point is None:
            return None

        for attribute in (
            "scene_position",
            "position",
        ):
            value = getattr(
                point,
                attribute,
                None,
            )

            if callable(value):
                try:
                    value = value()
                except TypeError:
                    value = None

            if value is not None:
                return value

        return None

    # --------------------------------------------------------

    @staticmethod
    def _extract_position(
        event: Any,
    ) -> Any:
        """
        Extract scene-space position from the event.
        """

        if event is None:
            return None

        scene_position = getattr(
            event,
            "scene_position",
            None,
        )

        if callable(scene_position):
            try:
                return scene_position()
            except TypeError:
                pass

        if scene_position is not None:
            return scene_position

        position = getattr(
            event,
            "position",
            None,
        )

        if callable(position):
            try:
                return position()
            except TypeError:
                return None

        if position is not None:
            return position

        return None

    # ========================================================
    # COMMAND CREATION
    # ========================================================

    def _build_create_command(
        self,
        start_point: Any,
        end_point: Any,
        start_position: Any,
        end_position: Any,
    ) -> Any:
        """
        Resolve the canonical line-creation command.

        Preferred application-controller factories:

            create_line_command(...)
            build_create_line_command(...)

        CommandManager factories are accepted as a fallback.

        No concrete command class is imported here.
        """

        controller = self.get_controller()

        factories = (
            "create_line_command",
            "build_create_line_command",
        )

        # ----------------------------------------------------
        # Preferred controller factory.
        # ----------------------------------------------------

        for method_name in factories:
            factory = getattr(
                controller,
                method_name,
                None,
            )

            if not callable(factory):
                continue

            return self._invoke_command_factory(
                factory,
                start_point,
                end_point,
                start_position,
                end_position,
            )

        # ----------------------------------------------------
        # Optional CommandManager factory.
        # ----------------------------------------------------

        manager = self.command_manager

        if manager is not None:
            for method_name in factories:
                factory = getattr(
                    manager,
                    method_name,
                    None,
                )

                if not callable(factory):
                    continue

                return self._invoke_command_factory(
                    factory,
                    start_point,
                    end_point,
                    start_position,
                    end_position,
                )

        return None

    # --------------------------------------------------------

    @staticmethod
    def _invoke_command_factory(
        factory: Any,
        start_point: Any,
        end_point: Any,
        start_position: Any,
        end_position: Any,
    ) -> Any:
        """
        Invoke a line-command factory using the most expressive
        endpoint contract first.

        The fallback signatures exist to accommodate the current
        command/application integration without importing a
        concrete command implementation into the tool layer.
        """

        attempts = (
            (
                start_point,
                end_point,
                start_position,
                end_position,
            ),
            (
                start_point,
                end_point,
            ),
        )

        last_error: Optional[TypeError] = None

        for args in attempts:
            try:
                return factory(
                    *args
                )
            except TypeError as exc:
                last_error = exc

        if last_error is not None:
            raise last_error

        return None

    # ========================================================
    # ENDPOINT COMPARISON
    # ========================================================

    @staticmethod
    def _same_endpoint(
        first: Any,
        second: Any,
    ) -> bool:
        """
        Determine whether two endpoint references represent the
        same connection point.
        """

        if first is second:
            return True

        if first is None or second is None:
            return False

        try:
            return bool(
                first == second
            )
        except Exception:
            pass

        first_id = LineTool._endpoint_id(
            first
        )
        second_id = LineTool._endpoint_id(
            second
        )

        if (
            first_id is not None
            and second_id is not None
        ):
            return (
                first_id == second_id
            )

        return False

    # --------------------------------------------------------

    @staticmethod
    def _endpoint_id(
        endpoint: Any,
    ) -> Any:
        """
        Extract a stable identifier from an endpoint reference.
        """

        for attribute in (
            "terminal_id",
            "connection_point_id",
            "object_id",
            "entity_id",
            "id",
        ):
            value = getattr(
                endpoint,
                attribute,
                None,
            )

            if callable(value):
                try:
                    value = value()
                except TypeError:
                    value = None

            if value is not None:
                return value

        if isinstance(
            endpoint,
            (str, int),
        ):
            return endpoint

        return None

    # ========================================================
    # TRANSIENT STATE
    # ========================================================

    def _clear_state(
        self,
    ) -> None:
        """
        Clear all transient line interaction state.
        """

        self._start_point = None
        self._current_point = None

        self._start_position = None
        self._current_position = None

        self._preview_active = False

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    @property
    def creation_count(
        self,
    ) -> int:
        """
        Return the number of successful line command submissions.

        This is diagnostic UI state only.
        """

        return self._creation_count

    # --------------------------------------------------------

    def get_preview(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Return transient preview information.

        Returns None when no line operation is active.

        The rendering layer may consume this data to draw a
        temporary preview without the tool owning any graphics
        object.
        """

        if not self._preview_active:
            return None

        return {
            "start_point": self._start_point,
            "current_point": self._current_point,
            "start_position": self._start_position,
            "current_position": self._current_position,
        }

    # --------------------------------------------------------

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return LineTool diagnostic state.
        """

        state = super().get_state()

        state.update(
            {
                "start_point": self._start_point,
                "current_point": self._current_point,
                "start_position": self._start_position,
                "current_position": self._current_position,
                "preview_active": self._preview_active,
                "creation_count": self._creation_count,
            }
        )

        return state


__all__ = [
    "LineTool",
]
