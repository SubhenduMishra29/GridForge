"""
GridForge V2
============

File:
    ui/canvas/interaction_manager.py

Purpose
-------
Central interaction routing boundary for the GridForge SLD Canvas.

InteractionManager translates view-level input events into calls to the
already-created ToolManager.

Architectural role
------------------
    GraphicsView
         │
         ▼
    InteractionManager
         │
         ▼
     ToolManager
         │
         ▼
   Active Tool
         │
         ▼
     Controller
         │
         ▼
       Core

Ownership rules
---------------
- InteractionManager does NOT create ToolManager.
- InteractionManager does NOT own ToolManager.
- InteractionManager does NOT dispose ToolManager.
- ToolManager is supplied by the application/plugin composition layer.
- InteractionManager only routes interaction events.
- InteractionManager does not implement tool behaviour.
- InteractionManager does not implement snapping.
- InteractionManager does not implement selection.
- InteractionManager does not implement navigation.
- InteractionManager does not implement rendering.
- InteractionManager does not modify the electrical Core directly.
"""

from __future__ import annotations

from typing import Any, Optional


class InteractionManager:
    """
    Route Canvas input events to the shared ToolManager.

    InteractionManager is deliberately thin.

    It is a bridge between the Qt/view layer and the application's
    authoritative ToolManager.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        *,
        view: Any = None,
        controller: Any = None,
        tool_manager: Any,
        coordinate_system: Any = None,
        snap_system: Any = None,
        preview_layer: Any = None,
        selection_manager: Any = None,
        command_manager: Any = None,
    ) -> None:
        """
        Construct an InteractionManager.

        Parameters
        ----------
        view:
            GraphicsView / viewport using this interaction manager.

        controller:
            Application/UI Controller.

        tool_manager:
            The application's existing authoritative ToolManager.

            InteractionManager never constructs or owns this object.

        coordinate_system:
            Shared Canvas coordinate system.

        snap_system:
            Shared snapping system.

        preview_layer:
            Shared preview layer.

        selection_manager:
            Shared selection manager.

        command_manager:
            Shared command manager.
        """

        if tool_manager is None:
            raise ValueError(
                "InteractionManager requires an existing ToolManager."
            )

        self.view = view
        self.controller = controller

        # --------------------------------------------------------
        # SHARED SERVICES
        # --------------------------------------------------------
        #
        # These are references supplied by composition.
        # InteractionManager does not construct them.
        # --------------------------------------------------------

        self.tool_manager = tool_manager
        self.coordinate_system = coordinate_system
        self.snap_system = snap_system
        self.preview_layer = preview_layer
        self.selection_manager = selection_manager
        self.command_manager = command_manager

        # --------------------------------------------------------
        # LIFECYCLE
        # --------------------------------------------------------

        self._disposed = False

    # ============================================================
    # STATE
    # ============================================================

    @property
    def disposed(self) -> bool:
        """
        Return whether this interaction manager has been disposed.
        """

        return self._disposed

    # ============================================================
    # TOOL ACCESS
    # ============================================================

    @property
    def active_tool(self) -> Optional[Any]:
        """
        Return the currently active tool.

        ToolManager remains the authoritative owner of active-tool
        state.
        """

        if self._disposed:
            return None

        manager = self.tool_manager

        # Prefer the canonical ToolManager property.
        value = getattr(
            manager,
            "active_tool",
            None,
        )

        if value is not None:
            return value

        # Compatibility with managers exposing get_active_tool().
        getter = getattr(
            manager,
            "get_active_tool",
            None,
        )

        if callable(getter):
            return getter()

        return None

    # ============================================================
    # MOUSE EVENTS
    # ============================================================

    def mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-press event to ToolManager.

        Returns
        -------
        bool
            True when the event was accepted/handled.
        """

        if self._disposed:
            return False

        return self._dispatch_event(
            "mouse_press",
            event,
        )

    # ------------------------------------------------------------

    def mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-move event to ToolManager.
        """

        if self._disposed:
            return False

        return self._dispatch_event(
            "mouse_move",
            event,
        )

    # ------------------------------------------------------------

    def mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-release event to ToolManager.
        """

        if self._disposed:
            return False

        return self._dispatch_event(
            "mouse_release",
            event,
        )

    # ------------------------------------------------------------

    def mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-double-click event to ToolManager.
        """

        if self._disposed:
            return False

        return self._dispatch_event(
            "mouse_double_click",
            event,
        )

    # ============================================================
    # KEYBOARD EVENTS
    # ============================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a keyboard press event to ToolManager.
        """

        if self._disposed:
            return False

        return self._dispatch_event(
            "key_press",
            event,
        )

    # ------------------------------------------------------------

    def key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a keyboard release event to ToolManager.
        """

        if self._disposed:
            return False

        return self._dispatch_event(
            "key_release",
            event,
        )

    # ============================================================
    # EVENT DISPATCH
    # ============================================================

    def _dispatch_event(
        self,
        method_name: str,
        event: Any,
    ) -> bool:
        """
        Dispatch an event to the shared ToolManager.

        This method deliberately contains no tool-specific logic.
        """

        manager = self.tool_manager

        handler = getattr(
            manager,
            method_name,
            None,
        )

        if not callable(handler):
            return False

        result = handler(event)

        # ToolManager implementations may either explicitly return
        # a boolean or simply consume the event.
        if result is None:
            return True

        return bool(result)

    # ============================================================
    # RESET
    # ============================================================

    def reset(self) -> None:
        """
        Reset transient interaction state.

        The ToolManager remains application-owned.

        InteractionManager therefore does not replace, recreate, or
        dispose it.
        """

        if self._disposed:
            return

        manager = self.tool_manager

        reset = getattr(
            manager,
            "reset",
            None,
        )

        if callable(reset):
            reset()

    # ============================================================
    # TOOL COMMANDS
    # ============================================================

    def activate_tool(
        self,
        tool_id: str,
    ) -> Any:
        """
        Activate a tool through the shared ToolManager.

        InteractionManager does not know how concrete tools work.
        """

        if self._disposed:
            raise RuntimeError(
                "InteractionManager has been disposed."
            )

        if not isinstance(
            tool_id,
            str,
        ) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        manager = self.tool_manager

        activate = getattr(
            manager,
            "activate_tool",
            None,
        )

        if not callable(activate):
            raise AttributeError(
                "ToolManager does not provide activate_tool()."
            )

        return activate(
            tool_id
        )

    # ------------------------------------------------------------

    def deactivate_tool(self) -> Any:
        """
        Deactivate the active tool through ToolManager.
        """

        if self._disposed:
            return None

        manager = self.tool_manager

        deactivate = getattr(
            manager,
            "deactivate_tool",
            None,
        )

        if callable(deactivate):
            return deactivate()

        reset = getattr(
            manager,
            "reset",
            None,
        )

        if callable(reset):
            return reset()

        return None

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return a diagnostic snapshot.

        This is observational only and does not create a second
        source of application state.
        """

        if self._disposed:
            return {
                "disposed": True,
                "has_tool_manager": False,
                "active_tool": None,
            }

        active = self.active_tool

        return {
            "disposed": False,
            "has_tool_manager": (
                self.tool_manager is not None
            ),
            "active_tool": self._tool_identifier(
                active
            ),
        }

    # ------------------------------------------------------------

    @staticmethod
    def _tool_identifier(
        tool: Any,
    ) -> Optional[str]:
        """
        Extract a diagnostic tool identifier.
        """

        if tool is None:
            return None

        value = getattr(
            tool,
            "tool_id",
            None,
        )

        if isinstance(
            value,
            str,
        ):
            return value

        value = getattr(
            tool,
            "id",
            None,
        )

        if isinstance(
            value,
            str,
        ):
            return value

        return type(tool).__name__

    # ============================================================
    # DISPOSAL
    # ============================================================

    def dispose(self) -> None:
        """
        Dispose the interaction layer.

        IMPORTANT
        ---------
        ToolManager is application-owned and therefore is NOT
        disposed here.

        Only InteractionManager's own references are released.
        """

        if self._disposed:
            return

        # --------------------------------------------------------
        # End transient interaction state.
        # --------------------------------------------------------

        try:
            self.reset()
        except Exception:
            # Disposal should still complete its ownership
            # boundary even if a transient reset fails.
            pass

        # --------------------------------------------------------
        # Release references owned by this interaction boundary.
        # --------------------------------------------------------

        self.view = None
        self.controller = None
        self.coordinate_system = None
        self.snap_system = None
        self.preview_layer = None
        self.selection_manager = None
        self.command_manager = None

        # --------------------------------------------------------
        # DO NOT dispose self.tool_manager.
        #
        # It belongs to the application composition layer.
        # --------------------------------------------------------

        self.tool_manager = None

        self._disposed = True


__all__ = [
    "InteractionManager",
]
