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

InteractionManager owns:

    - raw input routing;
    - transient interaction state;
    - PreviewLayer;
    - SnapSystem;
    - observing Controller tool-selection changes.

ToolManager owns:

    - tool instance creation;
    - active tool state;
    - activation;
    - deactivation;
    - cancellation;
    - lifecycle transitions.

ToolManager does NOT:

    - process raw mouse events;
    - process keyboard events;
    - implement tool behavior;
    - render permanent graphics;
    - modify the Core model;
    - perform electrical calculations;
    - create QGraphicsItems;
    - perform snapping;
    - own application-level tool selection;
    - subscribe directly to Controller tool-selection events.

Important
---------
ToolManager is the single owner of active tool instances.

Tools are created exclusively through ToolRegistry.

Existing tools may incrementally implement:

    activate()
    deactivate()
    cancel()

These lifecycle methods remain optional for compatibility.

Cancellation
------------
Cancellation and deactivation are different operations.

    cancel()
        Abort the current interaction while keeping the
        current tool active.

    deactivate()
        Remove the current tool instance entirely.

Therefore pressing ESC must not implicitly switch tools.

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
    The Controller remains authoritative for the requested tool ID,
    while InteractionManager translates Controller selection into
    lifecycle requests.

    Parameters
    ----------
    controller:
        GridForge Controller.

        The controller is passed to ToolRegistry when a tool is
        created. ToolManager does not subscribe to Controller
        events.

    interaction_manager:
        Optional InteractionManager reference passed to newly
        created tools through ToolRegistry.

        ToolManager does not mutate InteractionManager state.

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

        self.controller = controller

        self.interaction_manager = (
            interaction_manager
        )

        self.preview = preview

        # ----------------------------------------------------
        # Active tool state.
        #
        # ToolManager is the sole owner of these references.
        # ----------------------------------------------------

        self.current_tool: Optional[Any] = None

        self.current_tool_id: Optional[str] = None

    # ========================================================
    # TOOL ACTIVATION
    # ========================================================

    def activate(
        self,
        tool_id: str,
    ) -> Any:
        """
        Activate a tool.

        If the requested tool is already active, the existing
        instance is returned unchanged.

        Lifecycle:

            deactivate old
                ↓
            clear transient state
                ↓
            create new through ToolRegistry
                ↓
            store new active tool
                ↓
            activate new tool

        Parameters
        ----------
        tool_id:
            Registered tool identifier.

        Returns
        -------
        object
            Newly activated tool instance.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        if not tool_id:
            raise ValueError(
                "tool_id cannot be empty."
            )

        # ----------------------------------------------------
        # Do not recreate an already-active tool.
        # ----------------------------------------------------

        if (
            self.current_tool_id == tool_id
            and self.current_tool is not None
        ):
            return self.current_tool

        # ----------------------------------------------------
        # Remove the previous tool before creating the new one.
        # ----------------------------------------------------

        self.deactivate()

        # ----------------------------------------------------
        # Create exclusively through ToolRegistry.
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
        # Establish manager state before activate().
        #
        # This allows the tool to query its lifecycle context
        # during activation.
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

                # --------------------------------------------
                # Never leave a partially activated tool as the
                # manager's active tool.
                # --------------------------------------------

                self.current_tool = None
                self.current_tool_id = None

                self._clear_preview()

                raise

        return tool

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(
        self,
    ) -> None:
        """
        Deactivate and release the current tool.

        Deactivation is idempotent.

        The optional tool.deactivate() callback is invoked before
        the tool reference is released.

        Transient preview graphics are always cleared.
        """

        tool = self.current_tool

        # ----------------------------------------------------
        # No active tool.
        # ----------------------------------------------------

        if tool is None:

            self._clear_preview()

            self.current_tool_id = None

            return

        # ----------------------------------------------------
        # Give the tool an opportunity to clean up its own
        # lifecycle state.
        # ----------------------------------------------------

        deactivate_method = getattr(
            tool,
            "deactivate",
            None,
        )

        if callable(deactivate_method):

            try:
                deactivate_method()

            finally:
                # --------------------------------------------
                # Preview is manager-controlled transient UI
                # state and must be cleared even if the tool
                # lifecycle callback fails.
                # --------------------------------------------

                self._clear_preview()

        else:

            self._clear_preview()

        # ----------------------------------------------------
        # Release the active tool.
        # ----------------------------------------------------

        self.current_tool = None
        self.current_tool_id = None

    # ========================================================
    # CANCELLATION
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the current tool operation.

        Cancellation does NOT deactivate the tool.

        This distinction is fundamental:

            cancel()
                =
            abort the current interaction

        whereas:

            deactivate()
                =
            remove the active tool.

        For example, a LineTool may be active while the user
        presses ESC after selecting its first endpoint.

        ESC should clear that in-progress operation while the
        LineTool itself remains the selected tool.

        Returns
        -------
        bool
            True if an active tool existed and cancellation was
            processed.

            False if no tool was active.
        """

        tool = self.current_tool

        if tool is None:

            self._clear_preview()

            return False

        # ----------------------------------------------------
        # Prefer the tool's explicit cancellation contract.
        # ----------------------------------------------------

        cancel_method = getattr(
            tool,
            "cancel",
            None,
        )

        if callable(cancel_method):

            try:
                cancel_method()

            finally:
                self._clear_preview()

            return True

        # ----------------------------------------------------
        # Legacy compatibility.
        #
        # A tool without cancel() cannot be given deactivate()
        # as a substitute because cancellation must not imply
        # tool deactivation.
        #
        # We therefore only clear manager-owned transient
        # graphics and keep the tool active.
        # ----------------------------------------------------

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

        PreviewLayer remains owned by InteractionManager.

        ToolManager merely guarantees that previews are removed
        at tool lifecycle boundaries.
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
        Return the currently active tool instance.

        Returns
        -------
        object | None
        """

        return self.current_tool

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the identifier of the currently active tool.
        """

        return self.current_tool_id

    # ========================================================
    # STATE QUERIES
    # ========================================================

    def has_active_tool(
        self,
    ) -> bool:
        """
        Return True when a tool instance is active.
        """

        return self.current_tool is not None

    # --------------------------------------------------------

    def is_tool_active(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return True when the specified tool is active.
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
        Completely reset tool lifecycle state.

        The active interaction is cancelled first.

        The active tool is then deactivated and released.

        Therefore:

            reset()
                =
            cancel current operation
                +
            remove active tool
        """

        self.cancel()
        self.deactivate()

        # ----------------------------------------------------
        # Defensive final cleanup.
        # ----------------------------------------------------

        self._clear_preview()

    # ========================================================
    # DISPOSE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release active tool resources.

        ToolManager owns no Controller subscription, so there is
        no event connection to disconnect here.

        The method exists as the lifecycle endpoint for the
        ToolManager itself and is intentionally idempotent.
        """

        self.reset()

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
