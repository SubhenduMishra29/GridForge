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
        │ tool_changed(new_tool_id, previous_tool_id)
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

Controller stores the requested tool identifier and emits:

    tool_changed(new_tool_id, previous_tool_id)

ToolManager owns the resulting tool lifecycle:

    - subscription to Controller tool selection;
    - active tool instance;
    - tool creation;
    - activation;
    - deactivation;
    - cancellation;
    - lifecycle transitions;
    - transient preview cleanup at lifecycle boundaries.

InteractionManager owns:

    - raw input routing;
    - transient interaction state;
    - PreviewLayer;
    - SnapSystem;
    - CoordinateSystem.

PluginRegistry owns:

    - plugin/tool class registration;
    - plugin class lookup.

ToolManager does NOT:

    - process raw mouse events;
    - process keyboard events;
    - implement tool behavior;
    - render permanent graphics;
    - modify the Core model;
    - perform electrical calculations;
    - create QGraphicsItems;
    - perform snapping;
    - own application-level tool selection state;
    - implement canvas coordinate conversion.


Tool Selection
--------------

Controller owns the requested tool identifier.

The selection flow is:

    Controller.set_tool(tool_id)
              │
              ▼
    Controller.tool_changed
              │
              ▼
    ToolManager._on_tool_changed()
              │
              ▼
    ToolManager.activate(tool_id)


ToolManager is therefore the sole component responsible for
converting a requested tool identifier into an active tool
instance.

InteractionManager deliberately does NOT subscribe to
Controller.tool_changed.


Tool Lifecycle
--------------

    activate(new_tool)
          │
          ▼
    resolve registered class
          │
          ▼
    deactivate(old_tool)
          │
          ▼
    clear preview
          │
          ▼
    instantiate new tool
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
     ├── tool interaction state reset by tool
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

    ToolManager is the sole subscriber to the Controller's
    tool_changed event.

    Controller owns tool selection state.

    ToolManager owns the concrete tool instance and its
    lifecycle.
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
            Application/UI controller.

            The Controller owns the requested tool identifier
            and emits the tool_changed event.

        interaction_manager:
            Optional InteractionManager reference supplied to
            concrete tool constructors.

        preview:
            Optional PreviewLayer used for transient preview
            cleanup.

        Notes
        -----
        ToolManager subscribes to Controller.tool_changed.

        InteractionManager does not subscribe to that event.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        subscribe = getattr(
            controller,
            "subscribe",
            None,
        )

        if not callable(subscribe):
            raise TypeError(
                "controller must provide subscribe()."
            )

        unsubscribe = getattr(
            controller,
            "unsubscribe",
            None,
        )

        if not callable(unsubscribe):
            raise TypeError(
                "controller must provide unsubscribe()."
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

        self._subscribe_to_tool_changes()

    # ========================================================
    # CONTROLLER SUBSCRIPTION
    # ========================================================

    def _subscribe_to_tool_changes(
        self,
    ) -> None:
        """
        Subscribe to Controller tool-selection changes.

        ToolManager is the sole owner of this subscription.
        """

        if self._connected:
            return

        self.controller.subscribe(
            "tool_changed",
            self._on_tool_changed,
        )

        self._connected = True

    # --------------------------------------------------------

    def _unsubscribe_from_tool_changes(
        self,
    ) -> None:
        """
        Remove the Controller tool-selection subscription.

        The operation is idempotent.
        """

        if not self._connected:
            return

        self.controller.unsubscribe(
            "tool_changed",
            self._on_tool_changed,
        )

        self._connected = False

    # --------------------------------------------------------

    def _on_tool_changed(
        self,
        new_tool_id: str,
        previous_tool_id: Optional[str] = None,
    ) -> None:
        """
        Handle a Controller tool-selection event.

        Controller owns the selection request.

        ToolManager owns the lifecycle transition resulting
        from that request.

        Parameters
        ----------
        new_tool_id:
            Newly requested tool identifier.

        previous_tool_id:
            Previously requested tool identifier.

            The value is informational here. ToolManager uses
            its own active-tool state as the lifecycle authority.
        """

        del previous_tool_id

        self.activate(
            new_tool_id
        )

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

            validate identifier
                ↓
            resolve registered class
                ↓
            deactivate old tool
                ↓
            clear transient state
                ↓
            instantiate new tool
                ↓
            establish active state
                ↓
            activate new tool

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
        # Resolve the requested class BEFORE destroying the
        # current tool.
        #
        # This prevents an invalid tool ID from unnecessarily
        # deactivating a valid active tool.
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
        # Deactivate previous tool.
        # ----------------------------------------------------

        self.deactivate()

        # ----------------------------------------------------
        # Construct new tool.
        # ----------------------------------------------------

        try:
            tool = tool_class(
                controller=self.controller,
                interaction_manager=(
                    self.interaction_manager
                ),
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
        #
        # This allows the tool's activate() callback to observe
        # itself as the active tool through the manager.
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

        Controller selection state is deliberately not changed.

        This method is stronger than cancel().
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
        Release ToolManager resources.

        Disposal:

            - resets the active tool;
            - removes the Controller subscription;
            - becomes idempotent.

        ToolManager does not own the Controller itself.
        """

        if not self._connected:
            self.reset()
            return

        self.reset()

        self._unsubscribe_from_tool_changes()

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
            f"{self.current_tool_id!r}, "
            f"connected="
            f"{self._connected}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolManager",
]
