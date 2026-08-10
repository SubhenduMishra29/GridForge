```python
# ============================================================
# File: ui/core/tool_manager.py
# GridForge Tool Manager
# ============================================================
#
# PURPOSE
# -------
# Manages the complete lifecycle of GridForge interaction
# tools.
#
# The ToolManager sits between:
#
#     Controller
#          │
#          ▼
#     ToolManager
#          │
#          ▼
#     Active Tool
#
#
# RESPONSIBILITIES
# ----------------
#
# 1. Create tools through the existing ToolRegistry mechanism
# 2. Activate a tool
# 3. Deactivate the previous tool
# 4. Cancel the active tool
# 5. Handle tool switching
# 6. Clear transient interaction state
# 7. Provide a central Esc/cancel entry point
#
#
# IMPORTANT DESIGN RULE
# ---------------------
#
# ToolManager does NOT:
#
#     - process raw mouse events
#     - render graphics
#     - modify the Core model
#     - implement individual tool behavior
#
# Those responsibilities remain with:
#
#     InteractionManager → event routing
#     Tool               → interaction behavior
#     RenderSystem       → model → view
#     Controller         → application state
#
#
# TOOL LIFECYCLE
# --------------
#
#     deactivate old tool
#             ↓
#     clear transient state
#             ↓
#     create new tool
#             ↓
#     activate new tool
#
#
# CANCELLATION
# ------------
#
# Pressing ESC should result in:
#
#     Esc
#      ↓
#     ToolManager.cancel()
#      ↓
#     ActiveTool.cancel()
#      ↓
#     Preview cleared
#      ↓
#     Tool returns to idle state
#
#
# BACKWARD COMPATIBILITY
# ----------------------
#
# Existing tools are NOT required to implement activate(),
# deactivate(), or cancel() immediately.
#
# ToolManager checks whether those methods exist before
# calling them.
#
# This allows the existing GridForge tools to migrate
# incrementally.
#
#
# QT RULE
# -------
#
# No direct PySide6/PyQt imports are required here.
#
# ============================================================


from __future__ import annotations

from typing import Optional, Any


from ui.core.tool_registry import create_tool


class ToolManager:
    """
    Central manager for GridForge interaction-tool lifecycle.

    Parameters
    ----------
    controller:
        GridForge Controller.

    interaction_manager:
        InteractionManager responsible for routing raw events
        to the active tool.

    preview:
        Optional PreviewLayer.

        If supplied, ToolManager can guarantee that transient
        preview graphics are removed during cancellation and
        tool switching.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller,
        interaction_manager=None,
        preview=None,
    ) -> None:

        self.controller = controller

        self.interaction_manager = (
            interaction_manager
        )

        self.preview = preview

        # ----------------------------------------------------
        # Currently active tool instance.
        # ----------------------------------------------------

        self.current_tool: Optional[Any] = None

        # ----------------------------------------------------
        # ID of the currently active tool.
        # ----------------------------------------------------

        self.current_tool_id: Optional[str] = None

        # ----------------------------------------------------
        # Subscribe to Controller tool changes.
        # ----------------------------------------------------

        self.controller.subscribe(
            "tool_changed",
            self._on_controller_tool_changed,
        )

    # ========================================================
    # TOOL ACTIVATION
    # ========================================================

    def activate(
        self,
        tool_id: str,
    ):
        """
        Activate a tool.

        The previous tool is first deactivated and any
        transient state is cleared.

        Parameters
        ----------
        tool_id:
            Registered tool identifier.

        Returns
        -------
        object
            Newly created tool instance.
        """

        if not tool_id:
            raise ValueError(
                "tool_id cannot be empty."
            )

        # ----------------------------------------------------
        # If the requested tool is already active, do not
        # recreate it unnecessarily.
        # ----------------------------------------------------

        if (
            self.current_tool_id == tool_id
            and self.current_tool is not None
        ):
            return self.current_tool

        # ----------------------------------------------------
        # Deactivate existing tool.
        # ----------------------------------------------------

        self.deactivate()

        # ----------------------------------------------------
        # Create new tool using the existing registry.
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
        # Store active tool.
        # ----------------------------------------------------

        self.current_tool = tool

        self.current_tool_id = tool_id

        # ----------------------------------------------------
        # Give the tool an activation callback if supported.
        # ----------------------------------------------------

        activate_method = getattr(
            tool,
            "activate",
            None,
        )

        if callable(activate_method):
            activate_method()

        # ----------------------------------------------------
        # Update InteractionManager.
        #
        # This avoids requiring every existing part of the
        # application to know about ToolManager.
        # ----------------------------------------------------

        if self.interaction_manager is not None:

            self.interaction_manager.current_tool = (
                tool
            )

        print(
            f"[ToolManager] Activated tool: "
            f"{tool_id}"
        )

        return tool

    # ========================================================
    # CONTROLLER CALLBACK
    # ========================================================

    def _on_controller_tool_changed(
        self,
        tool_id: str,
    ) -> None:
        """
        Respond to Controller.set_tool().

        The Controller remains the authority for the requested
        tool while ToolManager owns the actual tool lifecycle.
        """

        self.activate(tool_id)

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(self) -> None:
        """
        Deactivate the current tool.

        If the tool implements deactivate(), that method is
        called.

        Transient preview graphics are then removed.
        """

        if self.current_tool is None:
            self._clear_preview()
            return

        # ----------------------------------------------------
        # Give the tool an opportunity to clean up its own
        # state.
        # ----------------------------------------------------

        deactivate_method = getattr(
            self.current_tool,
            "deactivate",
            None,
        )

        if callable(deactivate_method):
            deactivate_method()

        # ----------------------------------------------------
        # Clear transient graphics.
        # ----------------------------------------------------

        self._clear_preview()

        print(
            f"[ToolManager] Deactivated tool: "
            f"{self.current_tool_id}"
        )

        # ----------------------------------------------------
        # Remove references.
        # ----------------------------------------------------

        self.current_tool = None
        self.current_tool_id = None

        if self.interaction_manager is not None:

            self.interaction_manager.current_tool = None

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel(self) -> bool:
        """
        Cancel the current tool operation.

        This is the primary entry point for ESC handling.

        Example
        -------
        LineTool:

            Click Bus A
                 ↓
            Start line
                 ↓
            ESC
                 ↓
            cancel()
                 ↓
            start_bus = None
                 ↓
            preview cleared

        Returns
        -------
        bool
            True if a tool existed and cancellation was
            processed.

            False if no tool was active.
        """

        if self.current_tool is None:

            self._clear_preview()

            return False

        # ----------------------------------------------------
        # Prefer the tool's own cancel() implementation.
        # ----------------------------------------------------

        cancel_method = getattr(
            self.current_tool,
            "cancel",
            None,
        )

        if callable(cancel_method):

            cancel_method()

        else:

            # ------------------------------------------------
            # Legacy compatibility.
            #
            # Older tools may not yet implement cancel().
            # In that case, deactivate() is the safest
            # available lifecycle operation.
            # ------------------------------------------------

            deactivate_method = getattr(
                self.current_tool,
                "deactivate",
                None,
            )

            if callable(deactivate_method):
                deactivate_method()

        # ----------------------------------------------------
        # Always clear transient preview graphics.
        # ----------------------------------------------------

        self._clear_preview()

        print(
            "[ToolManager] Active tool operation cancelled"
        )

        return True

    # ========================================================
    # PREVIEW CLEANUP
    # ========================================================

    def _clear_preview(self) -> None:
        """
        Clear the PreviewLayer if one is available.

        Preview graphics are transient UI state and must never
        become part of the Core model.
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
    # TOOL QUERY
    # ========================================================

    def get_current_tool(self):
        """
        Return the currently active tool instance.

        Returns
        -------
        object or None
        """

        return self.current_tool

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the ID of the currently active tool.
        """

        return self.current_tool_id

    # ========================================================
    # STATE QUERY
    # ========================================================

    def has_active_tool(self) -> bool:
        """
        Return True when a tool is currently active.
        """

        return (
            self.current_tool is not None
        )

    # --------------------------------------------------------

    def is_tool_active(
        self,
        tool_id: str,
    ) -> bool:
        """
        Check whether a particular tool is active.
        """

        return (
            self.current_tool_id == tool_id
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset(self) -> None:
        """
        Completely reset tool interaction state.

        This is useful when:

            - closing a canvas
            - loading a new model
            - resetting the workspace
            - recovering from an invalid interaction state
        """

        self.cancel()

        self.deactivate()

        self._clear_preview()

        print(
            "[ToolManager] Tool state reset"
        )

    # ========================================================
    # DEBUG
    # ========================================================

    def get_state(self) -> dict:
        """
        Return ToolManager state for debugging.
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
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return concise diagnostic representation.
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
```
