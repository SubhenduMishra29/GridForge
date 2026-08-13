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
        ├── PluginRegistry
        │       │
        │       └── registered tool class
        │
        └── ToolRegistry
                │
                └── runtime tool instance


Ownership
---------
Controller owns:

    - application-level tool selection;
    - requested tool identifier.

InteractionManager owns:

    - raw input routing;
    - transient interaction state;
    - PreviewLayer;
    - SnapSystem;
    - CoordinateSystem.

ToolManager owns:

    - tool instance creation;
    - active tool state;
    - activation;
    - deactivation;
    - cancellation;
    - lifecycle transitions;
    - runtime registration of created tool instances;
    - transient preview cleanup at lifecycle boundaries.

PluginRegistry owns:

    - plugin/tool class registration;
    - plugin class lookup.

ToolRegistry owns:

    - runtime references to instantiated tools.

ToolManager does NOT:

    - subscribe directly to Controller;
    - process raw mouse events;
    - process keyboard events;
    - implement tool behavior;
    - render permanent graphics;
    - modify the Core model;
    - perform electrical calculations;
    - create QGraphicsItems;
    - perform snapping;
    - own application-level tool selection.

Controller → ToolManager routing
---------------------------------
The Controller publishes the requested tool ID.

InteractionManager is the central UI input/coordinating layer
and delegates tool activation to ToolManager.

Therefore ToolManager does NOT independently subscribe to the
Controller.

This prevents duplicate activation when both Controller and
InteractionManager are present.

Tool Lifecycle
--------------

    activate(tool_id)
          │
          ▼
    deactivate(old_tool)
          │
          ▼
    clear preview
          │
          ▼
    lookup class in PluginRegistry
          │
          ▼
    instantiate tool
          │
          ▼
    register instance in ToolRegistry
          │
          ▼
    activate(new_tool)

Cancellation
------------

Cancellation aborts the current interaction but does NOT
normally remove the active tool.

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
     └── preview cleared

The selected tool remains active.

Compatibility
-------------

Existing tools may incrementally implement:

    activate()
    deactivate()
    cancel()

These lifecycle methods remain optional.

If cancel() is unavailable, deactivate() is used as a
legacy compatibility fallback. The ToolManager nevertheless
retains the tool as the active tool until an explicit
deactivation occurs.

Qt Rule
-------
This module has no direct Qt dependency.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.plugin_registry import get_plugin
from ui.core.tool_registry import ToolRegistry


class ToolManager:
    """
    Owns the lifecycle of the currently active interaction tool.

    ToolManager is the lifecycle authority for tool instances.

    Controller remains authoritative for the requested tool ID.

    PluginRegistry remains authoritative for registered tool
    classes.

    ToolRegistry stores instantiated runtime tool references.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Optional[Any] = None,
        preview: Optional[Any] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        """
        Initialize the ToolManager.

        Parameters
        ----------
        controller:
            GridForge UI Controller.

        interaction_manager:
            InteractionManager supplied to concrete tools.

        preview:
            PreviewLayer used for transient preview cleanup.

        tool_registry:
            Runtime registry for instantiated tool objects.

            If omitted, a private ToolRegistry is created.

        Notes
        -----
        ToolManager intentionally does NOT subscribe to Controller.

        Controller tool-change notifications are routed through
        InteractionManager, which then calls activate().
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

        self.tool_registry = (
            tool_registry
            if tool_registry is not None
            else ToolRegistry()
        )

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
        Activate the requested tool.

        Lifecycle:

            deactivate old
                ↓
            clear preview
                ↓
            resolve registered class
                ↓
            construct instance
                ↓
            register instance
                ↓
            establish active state
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
            If tool construction returns None.
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
        # Do not recreate the current tool.
        # ----------------------------------------------------

        if (
            self.current_tool_id == tool_id
            and self.current_tool is not None
        ):
            return self.current_tool

        # ----------------------------------------------------
        # Remove previous active tool.
        # ----------------------------------------------------

        self.deactivate()

        # ----------------------------------------------------
        # Resolve tool class through PluginRegistry.
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
        # Construct the tool.
        # ----------------------------------------------------

        try:

            tool = tool_class(
                self.controller,
                self.interaction_manager,
            )

        except Exception:

            self._clear_preview()

            raise

        if tool is None:
            self._clear_preview()

            raise RuntimeError(
                "Tool class returned None during construction: "
                f"'{tool_id}'."
            )

        # ----------------------------------------------------
        # Register the runtime instance.
        #
        # ToolRegistry stores the instance.
        # ToolManager remains the lifecycle authority.
        # ----------------------------------------------------

        try:

            self.tool_registry.register(
                tool_id,
                tool,
            )

        except Exception:

            self._clear_preview()

            raise

        # ----------------------------------------------------
        # Establish authoritative active state BEFORE calling
        # activate().
        # ----------------------------------------------------

        self.current_tool = tool
        self.current_tool_id = tool_id

        # ----------------------------------------------------
        # Optional activation lifecycle callback.
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

                # --------------------------------------------
                # The tool failed during activation.
                #
                # Remove it from both active manager state
                # and runtime registry.
                # --------------------------------------------

                self.current_tool = None
                self.current_tool_id = None

                self.tool_registry.unregister(
                    tool_id
                )

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
        Deactivate and release the current active tool.

        The operation is idempotent.

        Lifecycle:

            tool.deactivate()
                ↓
            clear preview
                ↓
            unregister runtime instance
                ↓
            clear active state

        The ToolRegistry does not perform lifecycle operations.
        """

        tool = self.current_tool
        tool_id = self.current_tool_id

        # ----------------------------------------------------
        # No active tool.
        # ----------------------------------------------------

        if tool is None:

            if tool_id is not None:
                self.tool_registry.unregister(
                    tool_id
                )

            self.current_tool = None
            self.current_tool_id = None

            self._clear_preview()

            return

        # ----------------------------------------------------
        # Tool lifecycle callback.
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
            # Regardless of lifecycle callback outcome, the
            # manager must not retain a stale active reference.
            # ------------------------------------------------

            self._clear_preview()

            if tool_id is not None:

                self.tool_registry.unregister(
                    tool_id
                )

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

        Cancellation does NOT normally deactivate the active
        tool.

        Preferred lifecycle:

            tool.cancel()

        Legacy compatibility fallback:

            tool.deactivate()

        Returns
        -------
        bool
            True when an active tool existed.

            False when no tool was active.

        Notes
        -----
        When an explicit cancel() method exists, the tool
        remains active.

        The fallback to deactivate() is retained solely for
        older tools that have not yet implemented cancel().
        The manager still retains the tool as the active
        instance until deactivate() is explicitly requested.
        """

        tool = self.current_tool

        # ----------------------------------------------------
        # No active tool.
        # ----------------------------------------------------

        if tool is None:

            self._clear_preview()

            return False

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

            else:

                # --------------------------------------------
                # Legacy compatibility.
                # --------------------------------------------

                deactivate_method = getattr(
                    tool,
                    "deactivate",
                    None,
                )

                if callable(
                    deactivate_method
                ):
                    deactivate_method()

        finally:

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

        ToolManager does not own PreviewLayer.

        It merely guarantees that lifecycle boundaries do not
        leave stale transient graphics behind.
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
        Return the currently active tool instance.
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
        Return True when an active tool exists.
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
        Reset the active tool lifecycle.

        The current interaction is cancelled first, followed
        by explicit deactivation and release.
        """

        self.cancel()

        self.deactivate()

        self._clear_preview()

    # ========================================================
    # TOOL REGISTRY ACCESS
    # ========================================================

    def get_tool_registry(
        self,
    ) -> ToolRegistry:
        """
        Return the runtime ToolRegistry.

        The registry stores instantiated runtime tools.

        ToolManager remains responsible for their lifecycle.
        """

        return self.tool_registry

    # ========================================================
    # DISPOSE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release the active tool and reset the manager.

        Controller subscription management is intentionally
        absent because ToolManager does not subscribe directly
        to Controller.

        InteractionManager owns Controller event routing.
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
            "registered_tool_ids": (
                self.tool_registry.list_tools()
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
