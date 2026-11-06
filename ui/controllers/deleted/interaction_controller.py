# ============================================================
# File: ui/controllers/interaction_controller.py
# GridForge V2 — Interaction Controller
# ============================================================
"""
Interaction Controller for GridForge V2.

Architecture
------------

    GraphicsView
         │
         ▼
    InteractionController
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

Purpose
-------
InteractionController is the UI orchestration boundary for
user interaction.

It provides a stable controller-level API for forwarding raw
canvas interaction to the existing InteractionManager.

Responsibilities
----------------
InteractionController:

    - route mouse interaction;
    - route keyboard interaction;
    - expose active interaction state;
    - coordinate interaction reset;
    - provide interaction diagnostics;
    - expose the underlying InteractionManager when required
      by composition code.

InteractionController does NOT:

    - implement tool behavior;
    - own tool instances;
    - select tools directly;
    - perform snapping;
    - perform navigation;
    - own application selection;
    - modify Core model objects directly;
    - render graphics;
    - perform electrical calculations.

Tool ownership remains with ToolManager / InteractionManager.

Navigation ownership remains with NavigationController.

Selection ownership remains with the authoritative application
Controller and SelectionManager.

Qt Architecture
---------------
This module intentionally contains no direct Qt dependency.

Raw Qt events are accepted as opaque event objects and are
forwarded to InteractionManager.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.canvas.interaction_manager import InteractionManager


class InteractionController:
    """
    Thin orchestration controller around InteractionManager.

    The controller does not duplicate interaction state.

    InteractionManager remains the authoritative owner of the
    active interaction/tool lifecycle.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        interaction_manager: InteractionManager,
    ) -> None:
        """
        Initialize the InteractionController.

        Parameters
        ----------
        interaction_manager:
            Existing GridForge InteractionManager.

        The InteractionController does not create or own the
        InteractionManager.
        """

        if interaction_manager is None:
            raise ValueError(
                "interaction_manager must not be None."
            )

        if not isinstance(
            interaction_manager,
            InteractionManager,
        ):
            raise TypeError(
                "interaction_manager must be an "
                "InteractionManager."
            )

        self.interaction_manager = (
            interaction_manager
        )

        self._disposed = False

    # ========================================================
    # MANAGER ACCESS
    # ========================================================

    def get_interaction_manager(
        self,
    ) -> InteractionManager:
        """
        Return the underlying InteractionManager.
        """

        self._ensure_active()

        return self.interaction_manager

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> Any:
        """
        Forward a mouse-press event to InteractionManager.

        The event is not interpreted here.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return self.interaction_manager.mouse_press(
            event
        )

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> Any:
        """
        Forward a mouse-move event to InteractionManager.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return self.interaction_manager.mouse_move(
            event
        )

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> Any:
        """
        Forward a mouse-release event to InteractionManager.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return self.interaction_manager.mouse_release(
            event
        )

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a keyboard-press event.

        Returns
        -------
        bool
            True when InteractionManager consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        result = self.interaction_manager.key_press(
            event
        )

        return bool(
            result
        )

    # ========================================================
    # KEY RELEASE
    # ========================================================

    def key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a keyboard-release event.

        Returns
        -------
        bool
            True when InteractionManager consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        result = self.interaction_manager.key_release(
            event
        )

        return bool(
            result
        )

    # ========================================================
    # ACTIVE TOOL
    # ========================================================

    def get_active_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the currently active tool.

        Tool ownership remains with InteractionManager.

        Returns None when no active tool is exposed by the
        manager.
        """

        self._ensure_active()

        manager = self.interaction_manager

        getter = getattr(
            manager,
            "get_active_tool",
            None,
        )

        if callable(getter):
            return getter()

        active_tool = getattr(
            manager,
            "active_tool",
            None,
        )

        return active_tool

    # ========================================================
    # ACTIVE TOOL ID
    # ========================================================

    def get_active_tool_id(
        self,
    ) -> Optional[Any]:
        """
        Return the identifier of the active tool when the
        InteractionManager exposes one.

        This method does not infer tool identity from the tool
        class.
        """

        self._ensure_active()

        manager = self.interaction_manager

        getter = getattr(
            manager,
            "get_active_tool_id",
            None,
        )

        if callable(getter):
            return getter()

        value = getattr(
            manager,
            "active_tool_id",
            None,
        )

        return value

    # ========================================================
    # INTERACTION STATE
    # ========================================================

    def is_active(
        self,
    ) -> bool:
        """
        Return True when the interaction system reports an
        active interaction.

        If the underlying manager does not expose an explicit
        interaction-state contract, this method returns False
        rather than guessing.
        """

        self._ensure_active()

        manager = self.interaction_manager

        getter = getattr(
            manager,
            "is_active",
            None,
        )

        if callable(getter):
            return bool(
                getter()
            )

        value = getattr(
            manager,
            "active",
            None,
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        return False

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient interaction state.

        Tool lifecycle remains owned by InteractionManager.
        """

        self._ensure_active()

        reset = getattr(
            self.interaction_manager,
            "reset",
            None,
        )

        if not callable(reset):
            raise TypeError(
                "InteractionManager must provide reset()."
            )

        reset()

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the current interaction when supported.

        Returns
        -------
        bool
            True when the underlying manager exposes and
            successfully invokes cancellation.

        Notes
        -----
        Cancellation is deliberately delegated. This controller
        does not reproduce tool-specific cancellation semantics.
        """

        self._ensure_active()

        cancel = getattr(
            self.interaction_manager,
            "cancel",
            None,
        )

        if not callable(cancel):
            return False

        result = cancel()

        if result is None:
            return True

        return bool(
            result
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic interaction snapshot.

        The authoritative interaction state remains in
        InteractionManager.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        manager_state: Any = None

        getter = getattr(
            self.interaction_manager,
            "get_state",
            None,
        )

        if callable(getter):
            manager_state = getter()

        return {
            "disposed": False,
            "active": self.is_active(),
            "active_tool": self.get_active_tool(),
            "active_tool_id": self.get_active_tool_id(),
            "manager_state": manager_state,
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose transient interaction-controller state.

        The InteractionManager itself is not disposed because
        ownership remains with the canvas composition layer.
        """

        if self._disposed:
            return

        self._disposed = True

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure this controller has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "InteractionController has been disposed."
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

        if self._disposed:
            return (
                "InteractionController("
                "disposed=True"
                ")"
            )

        return (
            "InteractionController("
            f"active={self.is_active()}, "
            f"tool={self.get_active_tool_id()!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "InteractionController",
]
