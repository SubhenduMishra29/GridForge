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

InteractionManager owns:

    - raw input routing;
    - transient interaction state;
    - PreviewLayer;
    - SnapSystem;
    - CoordinateSystem.

ToolManager does NOT:

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


Compatibility
-------------

Existing tools are not required to implement:

    activate()
    deactivate()
    cancel()

Those lifecycle callbacks are optional so existing tools can
migrate incrementally.


Qt Rule
-------
This module has no direct Qt dependency.
"""

from __future__ import annotations

from typing import Any, Optional, Type

from ui.core.plugin_registry import get_plugin


class ToolManager:
    """
    Owns the lifecycle of the currently active interaction tool.

    ToolManager is the single runtime owner of the active tool
    instance.

    The Controller remains authoritative for the requested tool
    identifier, while PluginRegistry remains authoritative for
    the corresponding registered tool class.
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
            GridForge application controller.

        interaction_manager:
            Optional InteractionManager reference supplied to
            tool constructors.

        preview:
            Optional PreviewLayer used for transient preview
            cleanup.
        """

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
        # Controller subscription state.
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
            If tool construction or activation leaves the
            manager in an invalid state.
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
        # Resolve the tool class through PluginRegistry.
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
        #
        # Tool constructors receive the application controller
        # and interaction manager. Concrete tools remain
        # responsible for their own behavior.
        # ----------------------------------------------------

        try:

            tool = tool_class(
                self.controller,
                self.interaction_manager,
            )

        except Exception:

            # No partially created tool may become active.
            self.current_tool = None
            self.current_tool_id = None

            self._clear_preview()

            raise

        if tool is None:
            self.current_tool = None
            self.current_tool_id = None

            self._clear_preview()

            raise RuntimeError(
                "Tool class returned None during construction: "
                f"'{tool_id}'."
            )

        # ----------------------------------------------------
        # Establish manager state before activate().
        #
        # This allows activate() to inspect the manager state
        # indirectly through the interaction layer if required.
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

                # ------------------------------------------------
                # If activation fails, the failed tool must never
                # remain registered as active.
                # ------------------------------------------------

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
        React to a Controller tool-selection notification.

        Controller owns the requested tool identifier.

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
        # Optional tool cleanup.
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
            # Preview cleanup is guaranteed even if the tool's
            # deactivate() implementation raises.
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

        Preferred lifecycle:

            tool.cancel()

        Compatibility fallback:

            tool.deactivate()

        The fallback exists only for legacy tools that have not
        yet implemented cancel().

        Returns
        -------
        bool
            True if an active tool existed and cancellation was
            processed.

            False if no tool was active.
        """

        tool = self.current_tool

        # ----------------------------------------------------
        # No active tool.
        # ----------------------------------------------------

        if tool is None:

            self._clear_preview()

            return False

        # ----------------------------------------------------
        # Prefer explicit cancel().
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

            else:

                # --------------------------------------------
                # Legacy compatibility.
                #
                # The tool remains logically active even when
                # deactivate() is used as the fallback.
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

            # ------------------------------------------------
            # Preview belongs to the transient interaction
            # layer and must always be cleared.
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

        ToolManager does not own PreviewLayer. It merely ensures
        lifecycle transitions cannot leave stale preview graphics
        behind.
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

        The active interaction is cancelled first, followed by
        tool deactivation and release.
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

        The operation is idempotent.
        """

        self.reset()

        if not self._connected:
            return

        unsubscribe = getattr(
            self.controller,
            "unsubscribe",
            None,
        )

        if callable(
            unsubscribe
        ):

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
            "connected": (
                self._connected
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
