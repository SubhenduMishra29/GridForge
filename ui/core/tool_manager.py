# ============================================================
# File: ui/core/tool_manager.py
# GridForge V2 — Tool Manager
# ============================================================
"""
Central lifecycle manager for GridForge interaction tools.

Architecture
------------

    Controller
        │
        │ requested tool ID
        ▼
    InteractionManager
        │
        │ activation request
        ▼
    ToolManager
        │
        ▼
    ToolRegistry
        │
        ▼
    Active Tool

Ownership
---------
Controller owns application-level tool selection.

ToolManager owns:

    - tool instance creation;
    - active tool state;
    - activation;
    - deactivation;
    - cancellation;
    - lifecycle transitions.

InteractionManager owns:

    - raw input routing;
    - transient interaction state;
    - PreviewLayer;
    - SnapSystem.

ToolManager does NOT:

    - process raw mouse events;
    - process keyboard events;
    - implement tool behavior;
    - render permanent graphics;
    - modify the Core model;
    - perform electrical calculations;
    - create QGraphicsItems;
    - decide snapping policy.

Important
---------
ToolManager is the single owner of tool instances.

Tools are created through ToolRegistry.

Existing tools may incrementally implement:

    activate()
    deactivate()
    cancel()

Those lifecycle methods remain optional for compatibility.

Qt Rule
-------
This module has no direct Qt dependency.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.tool_registry import create_tool


class ToolManager:
    """
    Owns the lifecycle of the currently active interaction tool.

    ToolManager does not own application-level tool selection.
    The Controller remains authoritative for the requested tool ID.

    Parameters
    ----------
    controller:
        GridForge Controller.

    interaction_manager:
        Optional InteractionManager reference.

        Kept for compatibility and future integration, but
        ToolManager does not mutate its active-tool state.

    preview:
        Optional PreviewLayer used for guaranteed transient
        preview cleanup during lifecycle transitions.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Optional[Any] = None,
        preview: Optional[Any] = None,
    ) -> None:

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if not callable(
            getattr(
                controller,
                "subscribe",
                None,
            )
        ):
            raise TypeError(
                "controller must provide subscribe()."
            )

        self.controller = controller

        self.interaction_manager = (
            interaction_manager
        )

        self.preview = preview

        # ----------------------------------------------------
        # Active tool state.
        # ----------------------------------------------------

        self.current_tool: Optional[Any] = None

        self.current_tool_id: Optional[str] = None

        # ----------------------------------------------------
        # Controller subscription.
        #
        # ToolManager owns lifecycle, but InteractionManager
        # remains responsible for routing activation requests.
        #
        # This callback is retained only for compatibility with
        # direct Controller-driven tool selection.
        # ----------------------------------------------------

        self._connected = False

        self.controller.subscribe(
            "tool_changed",
            self._on_controller_tool_changed,
        )

        self._connected = True

    # ========================================================
    # TOOL ACTIVATION
    # ========================================================

    def activate(
        self,
        tool_id: str,
    ) -> Any:
        """
        Activate the requested tool.

        If the requested tool is already active, the existing
        instance is returned unchanged.

        Lifecycle:

            deactivate old
                ↓
            clear transient state
                ↓
            create new
                ↓
            activate new
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        tool_id = tool_id.strip()

        if not tool_id:
            raise ValueError(
                "tool_id cannot be empty."
            )

        # ----------------------------------------------------
        # Already active.
        # ----------------------------------------------------

        if (
            self.current_tool_id == tool_id
            and self.current_tool is not None
        ):
            return self.current_tool

        # ----------------------------------------------------
        # Remove previous tool.
        # ----------------------------------------------------

        self.deactivate()

        # ----------------------------------------------------
        # Create through the central registry.
        # ----------------------------------------------------

        tool = create_tool(
            tool_id,
            self.controller,
            self.interaction_manager,
        )

        if tool is None:
            raise ValueError(
                f"Unknown tool: {tool_id}"
            )

        # ----------------------------------------------------
        # Store authoritative lifecycle state before calling
        # activate(), so a tool can query its manager through
        # its activation callback if necessary.
        # ----------------------------------------------------

        self.current_tool = tool
        self.current_tool_id = tool_id

        # ----------------------------------------------------
        # Optional lifecycle callback.
        # ----------------------------------------------------

        activate_method = getattr(
            tool,
            "activate",
            None,
        )

        if callable(activate_method):
            try:
                activate_method()
            except Exception:
                # Do not leave a partially activated tool behind.
                self.current_tool = None
                self.current_tool_id = None
                self._clear_preview()
                raise

        return tool

    # ========================================================
    # CONTROLLER CALLBACK
    # ========================================================

    def _on_controller_tool_changed(
        self,
        tool_id: Optional[str],
    ) -> None:
        """
        React to Controller tool-selection changes.

        Controller owns the requested tool ID.

        ToolManager owns the resulting tool lifecycle.
        """

        if tool_id is None:
            self.deactivate()
            return

        self.activate(
            tool_id
        )

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(
        self,
    ) -> None:
        """
        Deactivate and release the current tool.

        The operation is idempotent.
        """

        tool = self.current_tool

        if tool is None:
            self._clear_preview()
            self.current_tool_id = None
            return

        # ----------------------------------------------------
        # Give the tool an opportunity to clean up.
        # ----------------------------------------------------

        deactivate_method = getattr(
            tool,
            "deactivate",
            None,
        )

        if callable(deactivate_method):
            deactivate_method()

        # ----------------------------------------------------
        # Preview graphics are manager-owned transient state.
        # ----------------------------------------------------

        self._clear_preview()

        # ----------------------------------------------------
        # Release the tool.
        # ----------------------------------------------------

        self.current_tool = None
        self.current_tool_id = None

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the current tool operation.

        Cancellation does NOT deactivate the tool.

        This distinction is important:

            cancel()
                =
            abort current interaction

        whereas:

            deactivate()
                =
            remove the active tool itself.

        Returns
        -------
        bool
            True if an active tool existed.
        """

        tool = self.current_tool

        if tool is None:
            self._clear_preview()
            return False

        cancel_method = getattr(
            tool,
            "cancel",
            None,
        )

        if callable(cancel_method):

            cancel_method()

        else:

            # ------------------------------------------------
            # Compatibility fallback.
            #
            # Older tools without cancel() receive deactivate()
            # as the safest available lifecycle operation.
            #
            # Note:
            # this does NOT release the manager's tool instance.
            # The manager remains logically active.
            # ------------------------------------------------

            deactivate_method = getattr(
                tool,
                "deactivate",
                None,
            )

            if callable(deactivate_method):
                deactivate_method()

        self._clear_preview()

        return True

    # ========================================================
    # PREVIEW CLEANUP
    # ========================================================

    def _clear_preview(
        self,
    ) -> None:
        """
        Clear transient preview graphics.

        PreviewLayer remains outside ToolManager ownership;
        ToolManager merely guarantees cleanup at lifecycle
        boundaries.
        """

        if self.preview is None:
            return

        clear_method = getattr(
            self.preview,
            "clear",
            None,
        )

        if callable(clear_method):
            clear_method()

    # ========================================================
    # ACTIVE TOOL ACCESS
    # ========================================================

    def get_current_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the active tool instance.
        """

        return self.current_tool

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the active tool identifier.
        """

        return self.current_tool_id

    # ========================================================
    # STATE QUERIES
    # ========================================================

    def has_active_tool(
        self,
    ) -> bool:
        """
        Return True if a tool instance is active.
        """

        return self.current_tool is not None

    # --------------------------------------------------------

    def is_tool_active(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return True if the specified tool is active.
        """

        return (
            self.current_tool is not None
            and self.current_tool_id == tool_id
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset tool lifecycle state.

        The active tool is cancelled first, then deactivated.
        """

        self.cancel()
        self.deactivate()
        self._clear_preview()

    # ========================================================
    # DISCONNECT
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Disconnect the Controller subscription and release
        active tool resources.
        """

        self.reset()

        if not self._connected:
            return

        unsubscribe = getattr(
            self.controller,
            "unsubscribe",
            None,
        )

        if callable(unsubscribe):
            unsubscribe(
                "tool_changed",
                self._on_controller_tool_changed,
            )

        self._connected = False

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of ToolManager state.
        """

        return {
            "current_tool_id": (
                self.current_tool_id
            ),
            "has_active_tool": (
                self.has_active_tool()
            ),
            "connected": self._connected,
        }

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "ToolManager("
            f"current_tool="
            f"{self.current_tool_id!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolManager",
]
