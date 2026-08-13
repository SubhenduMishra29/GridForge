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
        │ lifecycle request
        ▼
    ToolManager
        │
        │ registered tool class
        ▼
    PluginRegistry
        │
        ▼
    Tool Instance
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
    - CoordinateSystem;
    - forwarding the requested tool ID to ToolManager.

ToolManager owns:

    - active tool instance;
    - tool creation;
    - activation;
    - deactivation;
    - cancellation;
    - lifecycle transitions;
    - transient preview cleanup at lifecycle boundaries.

PluginRegistry owns:

    - plugin/tool class registration;
    - plugin class lookup.

ToolManager does NOT:

    - subscribe to Controller tool-selection events;
    - process raw mouse events;
    - process keyboard events;
    - implement tool behavior;
    - render permanent graphics;
    - modify the Core model;
    - perform electrical calculations;
    - create QGraphicsItems;
    - perform snapping;
    - own application-level tool selection.

Tool Lifecycle
--------------

    activate(new_tool)
          │
          ▼
    deactivate(old_tool)
          │
          ▼
    clear preview
          │
          ▼
    lookup registered class
          │
          ▼
    instantiate tool
          │
          ▼
    activate(new_tool)


Cancellation
------------

Cancellation aborts the current interaction but does NOT
deactivate the selected tool.

    ESC
     │
     ▼
    InteractionManager
     │
     ▼
    ToolManager.cancel()
     │
     ▼
    ActiveTool.cancel()
     │
     ├── interaction state reset by tool
     └── preview cleared

The tool remains active after cancellation.

Qt Rule
-------
This module has no direct Qt dependency.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.plugin_registry import get_plugin


class ToolManager:
    """
    Owns the lifecycle of the currently active interaction tool.

    ToolManager is deliberately independent of Controller
    selection events.

    InteractionManager is the bridge between Controller tool
    selection and this lifecycle manager.
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
        """
        Initialize the ToolManager.

        Parameters
        ----------
        controller:
            Application/UI controller supplied to tool
            constructors.

            ToolManager does not subscribe to Controller
            selection events.

        interaction_manager:
            Optional InteractionManager reference supplied to
            tool constructors.

        preview:
            Optional PreviewLayer used for transient preview
            cleanup.

        Notes
        -----
        Controller remains an injected dependency because
        concrete tools may require access to the application
        coordination context.

        Tool selection itself is handled upstream by
        InteractionManager.
        """

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
        Activate a registered tool.

        Lifecycle:

            deactivate old
                ↓
            clear transient state
                ↓
            lookup registered class
                ↓
            instantiate
                ↓
            activate new

        Parameters
        ----------
        tool_id:
            Registered tool identifier.

        Returns
        -------
        object
            Active tool instance.

        Raises
        ------
        TypeError
            If tool_id is not a string.

        ValueError
            If tool_id is empty or unregistered.

        RuntimeError
            If tool construction or activation produces an
            invalid state.
        """

        # ----------------------------------------------------
        # Validate identifier.
        # ----------------------------------------------------

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
        #
        # Do not recreate the same tool instance.
        # ----------------------------------------------------

        if (
            self.current_tool_id == tool_id
            and self.current_tool is not None
        ):
            return self.current_tool

        # ----------------------------------------------------
        # Deactivate previous tool first.
        # ----------------------------------------------------

        self.deactivate()

        # ----------------------------------------------------
        # Resolve registered tool class.
        # ----------------------------------------------------

        tool_class = get_plugin(
            "tool",
            tool_id,
        )

        if tool_class is None:
            raise ValueError(
                "Unknown or unregistered GridForge "
                f"tool: '{tool_id}'."
            )

        if not isinstance(
            tool_class,
            type,
        ):
            raise TypeError(
                "Registered tool must be a class: "
                f"{tool_class!r}"
            )

        # ----------------------------------------------------
        # Construct tool.
        # ----------------------------------------------------

        try:
            tool = tool_class(
                self.controller,
                self.interaction_manager,
            )

        except Exception:

            self.current_tool = None
            self.current_tool_id = None

            self._clear_preview()

            raise

        if tool is None:

            self.current_tool = None
            self.current_tool_id = None

            self._clear_preview()

            raise RuntimeError(
                "Tool class returned None during "
                f"construction: '{tool_id}'."
            )

        # ----------------------------------------------------
        # Establish manager state before activate().
        # ----------------------------------------------------

        self.current_tool = tool
        self.current_tool_id = tool_id

        # ----------------------------------------------------
        # Optional activation callback.
        # ----------------------------------------------------

        activate_method = getattr(
            tool,
            "activate",
            None,
        )

        if callable(
            activate_method
        ):

            try:
                activate_method()

            except Exception:

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

        The operation is idempotent.

        The active tool's optional deactivate() callback is
        invoked before the instance is released.

        Preview graphics are always cleared.
        """

        tool = self.current_tool

        # ----------------------------------------------------
        # No active tool.
        # ----------------------------------------------------

        if tool is None:

            self.current_tool_id = None

            self._clear_preview()

            return

        # ----------------------------------------------------
        # Optional cleanup callback.
        # ----------------------------------------------------

        deactivate_method = getattr(
            tool,
            "deactivate",
            None,
        )

        try:

            if callable(
                deactivate_method
            ):
                deactivate_method()

        finally:

            # ------------------------------------------------
            # Preview cleanup is guaranteed.
            # ------------------------------------------------

            self._clear_preview()

            self.current_tool = None
            self.current_tool_id = None

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the current tool interaction.

        Cancellation does NOT deactivate the active tool.

        A tool that does not implement cancel() simply receives
        no tool-level cancellation callback. The manager still
        clears transient preview state.

        Returns
        -------
        bool
            True if an active tool existed.

            False if no tool was active.

        Notes
        -----
        Lifecycle deactivation is deliberately NOT used as a
        cancellation fallback.

        Cancellation and deactivation are different lifecycle
        operations:

            cancel()
                → abort current interaction
                → remain active

            deactivate()
                → leave the tool
                → release active instance
        """

        tool = self.current_tool

        # ----------------------------------------------------
        # No active tool.
        # ----------------------------------------------------

        if tool is None:

            self._clear_preview()

            return False

        # ----------------------------------------------------
        # Explicit cancellation callback.
        # ----------------------------------------------------

        cancel_method = getattr(
            tool,
            "cancel",
            None,
        )

        try:

            if callable(
                cancel_method
            ):
                cancel_method()

        finally:

            # ------------------------------------------------
            # Preview belongs to transient interaction state.
            # ------------------------------------------------

            self._clear_preview()

        return True

    # ========================================================
    # PREVIEW CLEANUP
    # ========================================================

    def _clear_preview(
        self,
    ) -> None:
        """
        Clear transient preview graphics when PreviewLayer is
        available.

        ToolManager does not own PreviewLayer.

        It only guarantees that lifecycle transitions do not
        leave stale transient preview graphics behind.
        """

        if self.preview is None:
            return

        clear_method = getattr(
            self.preview,
            "clear",
            None,
        )

        if callable(
            clear_method
        ):
            clear_method()

    # ========================================================
    # ACTIVE TOOL ACCESS
    # ========================================================

    def get_current_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the active tool instance.

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
        Return the identifier of the active tool.
        """

        return self.current_tool_id

    # ========================================================
    # STATE QUERIES
    # ========================================================

    def has_active_tool(
        self,
    ) -> bool:
        """
        Return True when an active tool instance exists.
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
        Return True when the specified tool is active.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            return False

        return (
            self.current_tool is not None
            and self.current_tool_id
            == tool_id.strip()
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Completely reset tool lifecycle state.

        The current interaction is cancelled first, followed
        by deactivation and release of the active tool.

        This method is intentionally stronger than cancel().
        """

        self.cancel()

        self.deactivate()

        self._clear_preview()

    # ========================================================
    # DISPOSE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release the active tool resources.

        ToolManager has no Controller subscription and therefore
        has no subscription-disconnection step.

        The operation is idempotent.
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
