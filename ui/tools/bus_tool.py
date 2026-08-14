# ============================================================
# File: ui/tools/bus_tool.py
# GridForge V2 — Bus Tool
# ============================================================
"""
Bus creation tool for GridForge V2.

BusTool converts canvas interaction into bus-creation intent.

Architecture
------------

    GraphicsView
         │
         ▼
    InteractionManager
         │
         ▼
       BusTool
         │
         ▼
    CommandManager
         │
         ▼
   Application Controller
         │
         ▼
        Core

Responsibilities
----------------
BusTool:

    - receive a canvas click;
    - obtain the requested scene position;
    - submit a bus-creation command through CommandManager;
    - reset transient interaction state;
    - support cancellation.

BusTool does NOT:

    - create Core Bus objects directly;
    - mutate the Network;
    - perform electrical validation;
    - perform rendering;
    - own the graphics item;
    - manipulate QGraphicsScene directly;
    - implement navigation;
    - maintain command history;
    - bypass CommandManager.

Coordinate authority
--------------------
The tool does not convert viewport coordinates itself.

The event reaching the tool is expected to expose a scene-space
position through the GridForge interaction event contract.

If an application-specific command requires a different payload,
the command/application layer is responsible for that conversion.

Current concrete tool set
-------------------------
GridForge V2 intentionally exposes exactly three concrete tools:

    SelectTool
    BusTool
    LineTool

No additional tool is created by this module.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.tools.tool_base import ToolBase


class BusTool(ToolBase):
    """
    Tool for creating a bus at a canvas position.

    One left-click creates one bus-creation intent.

    The actual mutation is performed by the application/Core
    command path.
    """

    TOOL_ID = "bus"

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
        Initialize BusTool.

        Dependencies are injected by the UI composition layer.
        """

        super().__init__(
            controller,
            command_manager=command_manager,
            selection_manager=selection_manager,
            snap_system=snap_system,
            renderer_registry=renderer_registry,
        )

        self._last_position: Any = None
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

        return "Bus"

    # --------------------------------------------------------

    @property
    def description(
        self,
    ) -> str:
        """
        Human-readable tool description.
        """

        return "Create a bus on the electrical canvas."

    # ========================================================
    # ACTIVATION
    # ========================================================

    def on_activate(
        self,
    ) -> None:
        """
        Reset transient creation state.
        """

        self._last_position = None

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def on_deactivate(
        self,
    ) -> None:
        """
        Clear transient creation state.
        """

        self._last_position = None

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def on_mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a bus-placement mouse press.

        The tool creates on release rather than press so the
        interaction follows the standard press/release lifecycle.
        """

        self._last_position = self._extract_position(
            event
        )

        return True

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def on_mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Track the latest scene-space cursor position.

        No preview graphics are created here. Preview ownership
        belongs to the canvas preview/rendering layer.
        """

        position = self._extract_position(
            event
        )

        if position is not None:
            self._last_position = position

        return True

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def on_mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Create a bus at the released scene-space position.
        """

        position = self._extract_position(
            event
        )

        if position is None:
            position = self._last_position

        if position is None:
            self._clear_state()
            return True

        self._last_position = position

        command = self._build_create_command(
            position
        )

        if command is None:
            raise RuntimeError(
                "Unable to create the bus command. "
                "The application controller or command manager "
                "must expose a canonical bus-creation command path."
            )

        self.execute_command(
            command
        )

        self._creation_count += 1

        self._clear_state()

        return True

    # ========================================================
    # KEYBOARD
    # ========================================================

    def on_key_press(
        self,
        event: Any,
    ) -> bool:
        """
        BusTool has no additional keyboard behavior.

        Escape is handled by ToolBase and invokes cancel().
        """

        return False

    # ========================================================
    # CANCEL
    # ========================================================

    def on_cancel(
        self,
    ) -> bool:
        """
        Cancel the current placement interaction.
        """

        had_state = (
            self._last_position is not None
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
        Reset transient bus-placement state.
        """

        self._clear_state()

    # ========================================================
    # COMMAND CREATION
    # ========================================================

    def _build_create_command(
        self,
        position: Any,
    ) -> Any:
        """
        Resolve the canonical bus-creation command.

        Command construction remains outside Core mutation.

        The preferred contract is an application-controller
        factory:

            controller.create_bus_command(position)

        A command-manager factory is accepted when explicitly
        provided by the existing UI composition layer.

        No concrete command class is imported here. This prevents
        the tool layer from becoming coupled to command-module
        implementation details.
        """

        controller = self.get_controller()

        # ----------------------------------------------------
        # Preferred application-controller command factory.
        # ----------------------------------------------------

        for method_name in (
            "create_bus_command",
            "build_create_bus_command",
        ):
            factory = getattr(
                controller,
                method_name,
                None,
            )

            if callable(factory):
                return factory(
                    position
                )

        # ----------------------------------------------------
        # Optional command-manager factory.
        # ----------------------------------------------------

        manager = self.command_manager

        if manager is not None:
            for method_name in (
                "create_bus_command",
                "build_create_bus_command",
            ):
                factory = getattr(
                    manager,
                    method_name,
                    None,
                )

                if callable(factory):
                    return factory(
                        position
                    )

        return None

    # ========================================================
    # POSITION EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_position(
        event: Any,
    ) -> Any:
        """
        Extract the scene-space position from an interaction
        event.

        Supported event contracts:

            event.scene_position()
            event.scene_position
            event.position()
            event.position

        The tool never performs coordinate conversion itself.
        """

        if event is None:
            return None

        # ----------------------------------------------------
        # Preferred explicit scene-space contract.
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Generic position contract.
        #
        # InteractionManager/GraphicsView is expected to ensure
        # this represents scene coordinates before forwarding
        # the event to the tool.
        # ----------------------------------------------------

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
    # TRANSIENT STATE
    # ========================================================

    def _clear_state(
        self,
    ) -> None:
        """
        Clear transient placement state.
        """

        self._last_position = None

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    @property
    def creation_count(
        self,
    ) -> int:
        """
        Return the number of successful command submissions made
        by this tool instance.

        This is diagnostic UI state only.

        It is not authoritative project state.
        """

        return self._creation_count

    # --------------------------------------------------------

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return BusTool diagnostic state.
        """

        state = super().get_state()

        state.update(
            {
                "last_position": self._last_position,
                "creation_count": self._creation_count,
            }
        )

        return state


__all__ = [
    "BusTool",
]
