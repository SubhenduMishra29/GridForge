# ============================================================
# File: ui/tools/tool_base.py
# GridForge V2 — Tool Base Contract
# ============================================================
"""
Base contract for GridForge V2 UI tools.

Tools represent user intent at the UI boundary.

Architecture
------------

    QGraphicsView / UI Event
             │
             ▼
     InteractionManager
             │
             ▼
          ToolBase
             │
             ▼
        CommandManager
             │
             ▼
      Application Controller
             │
             ▼
            Core

Concrete tools
--------------
The concrete GridForge V2 tool set is intentionally limited to:

    SelectTool
    BusTool
    LineTool

ToolBase defines interaction lifecycle and common context
access. It does not implement concrete electrical behavior.

Rules
-----
ToolBase must NOT:

    - own Core model state;
    - mutate Core directly;
    - implement electrical validation;
    - implement rendering;
    - implement navigation;
    - own application selection;
    - maintain command history;
    - bypass CommandManager;
    - instantiate other tools.

Concrete tools convert user interaction into application
commands. Core remains authoritative for validation and
mutation.

Qt
--
This module intentionally contains no direct Qt dependency.
Events are accepted as opaque objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class ToolBase(ABC):
    """
    Abstract base class for all GridForge UI tools.

    A ToolBase instance represents one interaction mode.

    The tool receives already-routed UI events from the
    InteractionManager and translates those events into intent.

    Tool lifecycle:

        created
          │
          ▼
        activate()
          │
          ▼
        event handling
          │
          ▼
        deactivate()
          │
          ▼
        disposed

    A tool must not assume that activate() is called only once
    during its lifetime.
    """

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
        Initialize the common tool context.

        Parameters
        ----------
        controller:
            Authoritative application/controller boundary.

        command_manager:
            CommandManager used to submit user intent.

        selection_manager:
            SelectionManager used for UI selection operations.

        snap_system:
            Existing SnapSystem used by tools requiring snapping.

        renderer_registry:
            RendererRegistry used only when a concrete tool
            explicitly requires renderer coordination.

        Notes
        -----
        Dependencies are injected.

        ToolBase does not construct application services.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        self.controller = controller

        self.command_manager = command_manager
        self.selection_manager = selection_manager
        self.snap_system = snap_system
        self.renderer_registry = renderer_registry

        self._active = False
        self._disposed = False

    # ========================================================
    # IDENTITY
    # ========================================================

    @property
    @abstractmethod
    def tool_id(
        self,
    ) -> str:
        """
        Stable identifier used by ToolManager.

        Concrete tools must provide an explicit identifier.

        Examples
        --------
        SelectTool:
            "select"

        BusTool:
            "bus"

        LineTool:
            "line"
        """

        raise NotImplementedError

    # --------------------------------------------------------

    @property
    def name(
        self,
    ) -> str:
        """
        Human-readable tool name.

        Concrete tools may override this.

        The default derives the name from tool_id.
        """

        return self.tool_id.replace(
            "_",
            " ",
        ).title()

    # --------------------------------------------------------

    @property
    def description(
        self,
    ) -> str:
        """
        Human-readable tool description.

        Concrete tools may override this.
        """

        return self.name

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def activate(
        self,
    ) -> None:
        """
        Activate this tool.

        The base implementation only changes lifecycle state.

        Concrete tools may override this method but should call
        super().activate().
        """

        self._ensure_not_disposed()

        if self._active:
            return

        self._active = True

        self.on_activate()

    # --------------------------------------------------------

    def deactivate(
        self,
    ) -> None:
        """
        Deactivate this tool.

        Concrete tools may override this method but should call
        super().deactivate().
        """

        self._ensure_not_disposed()

        if not self._active:
            return

        self.on_deactivate()

        self._active = False

    # --------------------------------------------------------

    def on_activate(
        self,
    ) -> None:
        """
        Activation hook for concrete tools.

        Default implementation does nothing.
        """

    # --------------------------------------------------------

    def on_deactivate(
        self,
    ) -> None:
        """
        Deactivation hook for concrete tools.

        Default implementation does nothing.
        """

    # ========================================================
    # STATE
    # ========================================================

    @property
    def is_active(
        self,
    ) -> bool:
        """
        Return whether this tool is currently active.
        """

        return self._active

    # --------------------------------------------------------

    @property
    def disposed(
        self,
    ) -> bool:
        """
        Return whether this tool has been disposed.
        """

        return self._disposed

    # ========================================================
    # MOUSE EVENTS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a mouse-press event.

        Returns
        -------
        bool
            True when the event was consumed.

        Default
        -------
        The base tool does not consume the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.on_mouse_press(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a mouse-move event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.on_mouse_move(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a mouse-release event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.on_mouse_release(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a mouse-double-click event.

        The default implementation does not consume it.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.on_mouse_double_click(
                event
            )
        )

    # ========================================================
    # MOUSE HOOKS
    # ========================================================

    def on_mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Concrete-tool hook for mouse press.
        """

        return False

    # --------------------------------------------------------

    def on_mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Concrete-tool hook for mouse move.
        """

        return False

    # --------------------------------------------------------

    def on_mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Concrete-tool hook for mouse release.
        """

        return False

    # --------------------------------------------------------

    def on_mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Concrete-tool hook for mouse double-click.
        """

        return False

    # ========================================================
    # KEYBOARD EVENTS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a keyboard-press event.

        Escape is treated as a standard cancellation request.
        Other keys are delegated to the concrete tool.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        if self._is_escape_event(
            event
        ):
            return bool(
                self.cancel()
            )

        return bool(
            self.on_key_press(
                event
            )
        )

    # --------------------------------------------------------

    def key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a keyboard-release event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.on_key_release(
                event
            )
        )

    # ========================================================
    # KEYBOARD HOOKS
    # ========================================================

    def on_key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Concrete-tool hook for keyboard press.
        """

        return False

    # --------------------------------------------------------

    def on_key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Concrete-tool hook for keyboard release.
        """

        return False

    # ========================================================
    # CANCELLATION
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the current transient tool operation.

        Concrete tools should override this when they have
        temporary state such as:

            - preview geometry;
            - a pending first endpoint;
            - a drag operation;
            - a temporary selection operation.

        Returns
        -------
        bool
            True when cancellation was handled.

        The base implementation reports that no transient
        operation existed.
        """

        self._ensure_active()

        return bool(
            self.on_cancel()
        )

    # --------------------------------------------------------

    def on_cancel(
        self,
    ) -> bool:
        """
        Concrete-tool cancellation hook.

        Default implementation does nothing.
        """

        return False

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient tool state.

        Concrete tools should override this when required.
        """

        self._ensure_not_disposed()

        self.on_reset()

    # --------------------------------------------------------

    def on_reset(
        self,
    ) -> None:
        """
        Concrete-tool reset hook.

        Default implementation does nothing.
        """

    # ========================================================
    # COMMAND SUBMISSION
    # ========================================================

    def execute_command(
        self,
        command: Any,
    ) -> Any:
        """
        Submit a command through CommandManager.

        This is the canonical route for tool-generated
        application mutations.

        Core is never mutated directly by ToolBase.
        """

        self._ensure_active()

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        if self.command_manager is None:
            raise RuntimeError(
                "command_manager is not configured."
            )

        execute = getattr(
            self.command_manager,
            "execute",
            None,
        )

        if not callable(execute):
            raise TypeError(
                "command_manager must provide execute()."
            )

        return execute(
            command
        )

    # ========================================================
    # SELECTION ACCESS
    # ========================================================

    def get_selection_manager(
        self,
    ) -> Any:
        """
        Return the injected SelectionManager.

        Raises
        ------
        RuntimeError
            If no SelectionManager was configured.
        """

        self._ensure_not_disposed()

        if self.selection_manager is None:
            raise RuntimeError(
                "selection_manager is not configured."
            )

        return self.selection_manager

    # ========================================================
    # SNAP ACCESS
    # ========================================================

    def get_snap_system(
        self,
    ) -> Any:
        """
        Return the injected SnapSystem.

        Raises
        ------
        RuntimeError
            If no SnapSystem was configured.
        """

        self._ensure_not_disposed()

        if self.snap_system is None:
            raise RuntimeError(
                "snap_system is not configured."
            )

        return self.snap_system

    # ========================================================
    # RENDERER ACCESS
    # ========================================================

    def get_renderer_registry(
        self,
    ) -> Any:
        """
        Return the injected RendererRegistry.

        Raises
        ------
        RuntimeError
            If no RendererRegistry was configured.
        """

        self._ensure_not_disposed()

        if self.renderer_registry is None:
            raise RuntimeError(
                "renderer_registry is not configured."
            )

        return self.renderer_registry

    # ========================================================
    # CONTROLLER ACCESS
    # ========================================================

    def get_controller(
        self,
    ) -> Any:
        """
        Return the authoritative application controller.
        """

        self._ensure_not_disposed()

        return self.controller

    # ========================================================
    # EVENT COORDINATES
    # ========================================================

    @staticmethod
    def event_position(
        event: Any,
    ) -> Any:
        """
        Extract an event position without assuming a specific
        concrete event class.

        The method supports the common GridForge UI event
        contracts:

            event.position()
            event.position

        No coordinate conversion is performed here.

        Coordinate conversion belongs to CoordinateSystem /
        GraphicsView.
        """

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        position = getattr(
            event,
            "position",
            None,
        )

        if callable(position):
            return position()

        if position is not None:
            return position

        raise AttributeError(
            "event does not expose position()."
        )

    # ========================================================
    # ESCAPE DETECTION
    # ========================================================

    @staticmethod
    def _is_escape_event(
        event: Any,
    ) -> bool:
        """
        Detect an Escape key event without introducing a direct
        Qt dependency.

        Qt-specific key constants may be exposed by the event
        object or by a key() method.

        If the event cannot be identified as Escape, False is
        returned.
        """

        key = getattr(
            event,
            "key",
            None,
        )

        if callable(key):
            try:
                key = key()
            except TypeError:
                return False

        if key is None:
            return False

        # Qt.Key_Escape is 16777216.

        if key == 16777216:
            return True

        # Some test doubles expose the symbolic key directly.

        if key == "Escape":
            return True

        if key == "Key_Escape":
            return True

        return False

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of this tool.
        """

        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "active": self._active,
            "disposed": self._disposed,
            "has_command_manager": (
                self.command_manager is not None
            ),
            "has_selection_manager": (
                self.selection_manager is not None
            ),
            "has_snap_system": (
                self.snap_system is not None
            ),
            "has_renderer_registry": (
                self.renderer_registry is not None
            ),
        }

    # ========================================================
    # LIFECYCLE / DISPOSAL
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose the tool.

        Disposal deactivates the tool and prevents further use.

        Concrete resources should be released by overriding
        on_dispose().
        """

        if self._disposed:
            return

        if self._active:
            self.deactivate()

        self.on_dispose()

        self._disposed = True

    # --------------------------------------------------------

    def on_dispose(
        self,
    ) -> None:
        """
        Disposal hook for concrete tools.
        """

    # ========================================================
    # VALIDATION
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure the tool is active and usable.
        """

        self._ensure_not_disposed()

        if not self._active:
            raise RuntimeError(
                f"Tool '{self.tool_id}' "
                "is not active."
            )

    # --------------------------------------------------------

    def _ensure_not_disposed(
        self,
    ) -> None:
        """
        Ensure the tool has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                f"Tool '{self.tool_id}' "
                "has been disposed."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            f"{type(self).__name__}("
            f"id={self.tool_id!r}, "
            f"active={self._active}, "
            f"disposed={self._disposed}"
            ")"
        )


__all__ = [
    "ToolBase",
]
