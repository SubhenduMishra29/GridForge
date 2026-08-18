# ============================================================
# File: ui/core/tool_manager.py
# GridForge V2 — Tool Manager
# ============================================================
"""
Central tool lifecycle manager for GridForge V2.

Architecture
------------

    Controller
        │
        │ tool_changed(tool_id, previous_tool_id)
        ▼
    ToolManager
        │
        ├── tool registry
        ├── concrete tool instances
        ├── active tool
        ├── activation
        ├── deactivation
        ├── cancellation
        └── reset
              │
              ▼
          Active Tool

Ownership
---------

Controller
    Owns application-level tool-selection intent.

ToolManager
    Owns concrete tool instances and their lifecycle.

InteractionManager
    Routes user input to the currently active tool.

Concrete Tools
    Implement tool-specific interaction behavior.

Responsibilities
----------------
ToolManager:

    - owns concrete tool instances;
    - creates tools through registered factories/classes;
    - responds to Controller tool-selection changes;
    - activates the requested tool;
    - deactivates the previous tool;
    - cancels active tool interaction;
    - resets active tool interaction;
    - disposes owned tool instances;
    - exposes active tool state;
    - provides diagnostics.

ToolManager does NOT:

    - decide which tool the application should select;
    - store application-level requested tool state;
    - implement tool behavior;
    - process mouse events;
    - process keyboard events;
    - perform snapping;
    - perform selection;
    - perform navigation;
    - modify Core directly;
    - render permanent graphics.

Lifecycle invariants
--------------------

1. Controller owns requested tool selection.
2. ToolManager owns concrete tool lifecycle.
3. ToolManager never calls Controller.set_tool().
4. An unknown tool request must not deactivate the current tool.
5. A failed tool construction must not destroy the current
   active lifecycle state.
6. A failed activation must restore the previous active tool
   when possible.
7. Active state is committed only after successful activation.
8. A successfully active tool remains active until a successful
   transition, explicit deactivation, or disposal.
9. Tool instances are lazily constructed.
10. ToolManager is the sole owner of concrete tool instances.
11. A disposed ToolManager cannot be mutated or activated.
12. Constructor TypeError from a concrete tool is never
    reinterpreted as a constructor-signature mismatch.

Tool construction
-----------------

The canonical tool constructor contract is:

    Tool(
        interaction_manager=...,
        preview=...,
    )

Factories/classes registered with ToolManager must support that
contract.

This manager deliberately does not catch TypeError from inside
the tool constructor and reinterpret it as a constructor-signature
mismatch. A tool-construction failure must propagate unchanged so
the real production error remains visible.

Qt Architecture
---------------
This module intentionally has no direct Qt dependency.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


ToolFactory = Callable[..., Any]


class ToolManager:
    """
    Central owner of GridForge concrete tool instances.

    Controller owns requested tool selection.

    ToolManager owns concrete tool lifecycle.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Any = None,
        preview: Any = None,
        tool_registry: Optional[Any] = None,
    ) -> None:
        """
        Initialize ToolManager.

        Parameters
        ----------
        controller:
            GridForge Controller.

        interaction_manager:
            Shared InteractionManager supplied to tools.

        preview:
            Shared PreviewLayer supplied to tools.

        tool_registry:
            Optional registry or mapping containing concrete
            tool factories.

        Notes
        -----
        ToolManager subscribes to Controller.tool_changed.

        ToolManager does not select a tool itself.
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
        # Tool registry.
        #
        # Contains factories/classes.
        #
        # Instantiated tools are owned separately by
        # _tool_instances.
        # ----------------------------------------------------

        self._tool_registry: dict[
            str,
            ToolFactory,
        ] = {}

        self._tool_instances: dict[
            str,
            Any,
        ] = {}

        # ----------------------------------------------------
        # Active lifecycle state.
        # ----------------------------------------------------

        self._active_tool_id: Optional[str] = None
        self._active_tool: Optional[Any] = None

        # ----------------------------------------------------
        # Manager lifecycle.
        # ----------------------------------------------------

        self._connected = False
        self._disposed = False

        # ----------------------------------------------------
        # Optional initial registry.
        # ----------------------------------------------------

        if tool_registry is not None:
            self._load_registry(
                tool_registry
            )

        # ----------------------------------------------------
        # Controller subscription.
        # ----------------------------------------------------

        self._subscribe_controller()

    # ========================================================
    # CONTROLLER SUBSCRIPTION
    # ========================================================

    def _subscribe_controller(
        self,
    ) -> None:
        """
        Subscribe to Controller.tool_changed.

        Canonical Controller contract:

            controller.subscribe(
                "tool_changed",
                callback,
            )
        """

        self._ensure_active()

        subscribe = getattr(
            self.controller,
            "subscribe",
            None,
        )

        if not callable(subscribe):
            raise TypeError(
                "controller must provide subscribe()."
            )

        subscribe(
            "tool_changed",
            self._on_tool_changed,
        )

        self._connected = True

    # --------------------------------------------------------

    def _unsubscribe_controller(
        self,
    ) -> None:
        """
        Remove the Controller tool-selection subscription.

        Controller exposes the canonical unsubscribe contract:

            controller.unsubscribe(
                "tool_changed",
                callback,
            )
        """

        unsubscribe = getattr(
            self.controller,
            "unsubscribe",
            None,
        )

        if not callable(unsubscribe):
            return

        unsubscribe(
            "tool_changed",
            self._on_tool_changed,
        )

    # ========================================================
    # TOOL REGISTRY
    # ========================================================

    def register_tool(
        self,
        tool_id: str,
        factory: ToolFactory,
    ) -> None:
        """
        Register a concrete tool factory.

        Registration does not instantiate or activate the tool.
        """

        self._ensure_active()

        self._validate_tool_id(
            tool_id
        )

        if not callable(factory):
            raise TypeError(
                "factory must be callable."
            )

        if tool_id in self._tool_registry:
            raise ValueError(
                f"Tool already registered: {tool_id!r}"
            )

        self._tool_registry[
            tool_id
        ] = factory

    # --------------------------------------------------------

    def register_tools(
        self,
        tools: dict[str, ToolFactory],
    ) -> None:
        """
        Register multiple tool factories atomically.

        Validation is performed before the registry is modified.
        """

        self._ensure_active()

        if tools is None:
            raise ValueError(
                "tools must not be None."
            )

        if not isinstance(
            tools,
            dict,
        ):
            raise TypeError(
                "tools must be a dictionary."
            )

        # ----------------------------------------------------
        # Validate the complete batch first.
        # ----------------------------------------------------

        for tool_id, factory in tools.items():

            self._validate_tool_id(
                tool_id
            )

            if not callable(factory):
                raise TypeError(
                    "factory must be callable."
                )

            if tool_id in self._tool_registry:
                raise ValueError(
                    f"Tool already registered: {tool_id!r}"
                )

        # ----------------------------------------------------
        # Commit only after complete validation.
        # ----------------------------------------------------

        self._tool_registry.update(
            tools
        )

    # --------------------------------------------------------

    def unregister_tool(
        self,
        tool_id: str,
    ) -> None:
        """
        Unregister a tool.

        The active tool cannot be unregistered.

        If disposal fails, ownership remains intact.
        """

        self._ensure_active()

        self._validate_tool_id(
            tool_id
        )

        if (
            tool_id
            == self._active_tool_id
        ):
            raise RuntimeError(
                "Cannot unregister the active tool."
            )

        instance = self._tool_instances.get(
            tool_id
        )

        # ----------------------------------------------------
        # Dispose first.
        #
        # Ownership is removed only after successful disposal.
        # ----------------------------------------------------

        if instance is not None:
            self._dispose_tool(
                instance
            )

            self._tool_instances.pop(
                tool_id
            )

        self._tool_registry.pop(
            tool_id,
            None,
        )

    # --------------------------------------------------------

    def has_tool(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return whether a tool is registered.
        """

        if self._disposed:
            return False

        if not isinstance(
            tool_id,
            str,
        ):
            return False

        return tool_id in self._tool_registry

    # --------------------------------------------------------

    def get_tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered tool identifiers in registration order.
        """

        self._ensure_active()

        return tuple(
            self._tool_registry.keys()
        )

    # --------------------------------------------------------

    def _load_registry(
        self,
        registry: Any,
    ) -> None:
        """
        Load tool factories from a registry.

        Supported forms:

            dictionary;

            object exposing get_tools();

            object exposing items().
        """

        self._ensure_active()

        if isinstance(
            registry,
            dict,
        ):
            self.register_tools(
                registry
            )
            return

        get_tools = getattr(
            registry,
            "get_tools",
            None,
        )

        if callable(get_tools):

            tools = get_tools()

            if tools is None:
                return

            if not isinstance(
                tools,
                dict,
            ):
                raise TypeError(
                    "tool registry get_tools() "
                    "must return a dictionary."
                )

            self.register_tools(
                tools
            )

            return

        items = getattr(
            registry,
            "items",
            None,
        )

        if callable(items):

            self.register_tools(
                dict(
                    items()
                )
            )

            return

        raise TypeError(
            "tool_registry must provide a tool mapping, "
            "get_tools(), or items()."
        )

    # ========================================================
    # CONTROLLER TOOL CHANGE
    # ========================================================

    def _on_tool_changed(
        self,
        new_tool_id: Optional[str],
        previous_tool_id: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Handle Controller tool_changed notification.

        This method performs lifecycle only.

        It never modifies Controller selection state.
        """

        if self._disposed:
            return

        if not self._connected:
            return

        self.activate(
            new_tool_id
        )

    # ========================================================
    # TOOL INSTANTIATION
    # ========================================================

    def _create_tool(
        self,
        tool_id: str,
    ) -> Any:
        """
        Lazily create one concrete tool.

        Canonical constructor contract:

            factory(
                interaction_manager=...,
                preview=...,
            )

        Constructor exceptions are deliberately allowed to
        propagate unchanged.
        """

        self._ensure_active()

        factory = self._tool_registry.get(
            tool_id
        )

        if factory is None:
            raise KeyError(
                f"Unknown tool ID: {tool_id!r}"
            )

        # ----------------------------------------------------
        # Do not catch TypeError here.
        #
        # A TypeError raised inside the actual tool constructor
        # is a production error and must remain visible.
        # ----------------------------------------------------

        tool = factory(
            interaction_manager=(
                self.interaction_manager
            ),
            preview=self.preview,
        )

        if tool is None:
            raise RuntimeError(
                f"Tool factory returned None: {tool_id!r}"
            )

        return tool

    # --------------------------------------------------------

    def _get_or_create_tool(
        self,
        tool_id: str,
    ) -> Any:
        """
        Return an existing tool instance or lazily create one.
        """

        self._ensure_active()

        if tool_id in self._tool_instances:
            return self._tool_instances[
                tool_id
            ]

        tool = self._create_tool(
            tool_id
        )

        self._tool_instances[
            tool_id
        ] = tool

        return tool

    # ========================================================
    # ACTIVE TOOL ACCESS
    # ========================================================

    def get_current_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the currently active tool instance.
        """

        self._ensure_active()

        return self._active_tool

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the identifier of the active tool.
        """

        self._ensure_active()

        return self._active_tool_id

    # --------------------------------------------------------

    @property
    def active_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the active tool instance.
        """

        self._ensure_active()

        return self._active_tool

    # --------------------------------------------------------

    @property
    def active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the active tool identifier.
        """

        self._ensure_active()

        return self._active_tool_id

    # ========================================================
    # ACTIVATION
    # ========================================================

    def activate(
        self,
        tool_id: Optional[str],
    ) -> Optional[Any]:
        """
        Activate a registered tool.

        Transition:

            validate
                ↓
            construct/retrieve
                ↓
            deactivate previous
                ↓
            activate new
                ↓
            commit active state

        Failure contract:

            Unknown tool:
                current lifecycle untouched.

            Construction failure:
                current lifecycle untouched.

            Activation failure:
                previous lifecycle is restored when possible.
        """

        self._ensure_active()

        # ----------------------------------------------------
        # Explicit deactivation.
        # ----------------------------------------------------

        if tool_id is None:
            self.deactivate()
            return None

        self._validate_tool_id(
            tool_id
        )

        # ----------------------------------------------------
        # Validate registration before touching the current
        # lifecycle.
        # ----------------------------------------------------

        if tool_id not in self._tool_registry:
            raise KeyError(
                f"Unknown tool ID: {tool_id!r}"
            )

        # ----------------------------------------------------
        # No transition required.
        # ----------------------------------------------------

        if (
            tool_id
            == self._active_tool_id
            and self._active_tool is not None
        ):
            return self._active_tool

        # ----------------------------------------------------
        # Construct before deactivating the current tool.
        #
        # Therefore constructor failure cannot destroy the
        # currently valid active lifecycle.
        # ----------------------------------------------------

        new_tool = self._get_or_create_tool(
            tool_id
        )

        previous_tool = self._active_tool
        previous_tool_id = self._active_tool_id

        # ----------------------------------------------------
        # Deactivate current tool.
        #
        # If this fails, the previous tool remains the manager's
        # active state and the new tool has not been activated.
        # ----------------------------------------------------

        if previous_tool is not None:
            self._deactivate_tool(
                previous_tool
            )

        # ----------------------------------------------------
        # Activate requested tool.
        #
        # Active state is not committed until activation
        # succeeds.
        # ----------------------------------------------------

        try:

            self._activate_tool(
                new_tool
            )

        except Exception:

            # ------------------------------------------------
            # New tool activation failed.
            #
            # Attempt to restore previous lifecycle.
            # ------------------------------------------------

            if previous_tool is not None:

                try:

                    self._activate_tool(
                        previous_tool
                    )

                except Exception:

                    # ----------------------------------------
                    # The previous lifecycle could not be
                    # restored. Never claim it is active.
                    # ----------------------------------------

                    self._active_tool = None
                    self._active_tool_id = None

                    self._clear_preview()

                    raise

            self._active_tool = previous_tool
            self._active_tool_id = previous_tool_id

            raise

        # ----------------------------------------------------
        # Commit active state only after successful activation.
        # ----------------------------------------------------

        self._active_tool = new_tool
        self._active_tool_id = tool_id

        return new_tool

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(
        self,
    ) -> None:
        """
        Deactivate the current tool.

        Controller selection is not modified.
        """

        self._ensure_active()

        tool = self._active_tool

        if tool is None:

            self._active_tool_id = None

            self._clear_preview()

            return

        # ----------------------------------------------------
        # Lifecycle callback is allowed to fail.
        #
        # If it fails, the manager must not falsely claim that
        # the tool was successfully deactivated.
        # ----------------------------------------------------

        self._deactivate_tool(
            tool
        )

        self._active_tool = None
        self._active_tool_id = None

        self._clear_preview()

    # ========================================================
    # CANCELLATION
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the active tool interaction.

        The active tool remains active.
        """

        self._ensure_active()

        tool = self._active_tool

        if tool is None:

            self._clear_preview()

            return False

        handler = getattr(
            tool,
            "cancel",
            None,
        )

        try:

            if callable(handler):

                result = handler()

                if result is None:
                    return True

                return bool(result)

            return True

        finally:

            self._clear_preview()

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset active tool interaction state.

        The active tool remains active.
        """

        self._ensure_active()

        tool = self._active_tool

        try:

            if tool is not None:

                handler = getattr(
                    tool,
                    "reset",
                    None,
                )

                if callable(handler):
                    handler()

        finally:

            self._clear_preview()

    # ========================================================
    # LIFECYCLE HELPERS
    # ========================================================

    @staticmethod
    def _activate_tool(
        tool: Any,
    ) -> None:
        """
        Invoke optional tool activation lifecycle.
        """

        handler = getattr(
            tool,
            "activate",
            None,
        )

        if callable(handler):
            handler()

    # --------------------------------------------------------

    @staticmethod
    def _deactivate_tool(
        tool: Any,
    ) -> None:
        """
        Invoke optional tool deactivation lifecycle.
        """

        handler = getattr(
            tool,
            "deactivate",
            None,
        )

        if callable(handler):
            handler()

    # --------------------------------------------------------

    @staticmethod
    def _dispose_tool(
        tool: Any,
    ) -> None:
        """
        Invoke optional permanent disposal lifecycle.
        """

        handler = getattr(
            tool,
            "dispose",
            None,
        )

        if callable(handler):
            handler()

    # --------------------------------------------------------

    def _clear_preview(
        self,
    ) -> None:
        """
        Clear the shared preview layer when available.
        """

        if self.preview is None:
            return

        clear = getattr(
            self.preview,
            "clear",
            None,
        )

        if callable(clear):
            clear()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot.
        """

        return {
            "connected": self._connected,
            "disposed": self._disposed,
            "registered_tools": (
                tuple(
                    self._tool_registry.keys()
                )
            ),
            "instantiated_tools": (
                tuple(
                    self._tool_instances.keys()
                )
            ),
            "active_tool_id": (
                self._active_tool_id
            ),
            "has_active_tool": (
                self._active_tool is not None
            ),
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_tool_id(
        tool_id: Any,
    ) -> None:
        """
        Validate a tool identifier.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        if not tool_id.strip():
            raise ValueError(
                "tool_id must not be empty."
            )

    # ========================================================
    # LIFECYCLE VALIDATION
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure the ToolManager has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

    # ========================================================
    # DISPOSAL
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose ToolManager and all owned tool instances.

        Disposal order:

            active tool deactivation
                    ↓
            preview cleanup
                    ↓
            concrete tool disposal
                    ↓
            Controller unsubscribe
                    ↓
            manager marked disposed
        """

        if self._disposed:
            return

        # ----------------------------------------------------
        # Deactivate active tool.
        # ----------------------------------------------------

        active_tool = self._active_tool

        if active_tool is not None:
            self._deactivate_tool(
                active_tool
            )

        self._active_tool = None
        self._active_tool_id = None

        self._clear_preview()

        # ----------------------------------------------------
        # Dispose every instantiated tool.
        #
        # tuple() protects iteration if disposal indirectly
        # modifies ownership.
        # ----------------------------------------------------

        for tool in tuple(
            self._tool_instances.values()
        ):
            self._dispose_tool(
                tool
            )

        self._tool_instances.clear()

        # ----------------------------------------------------
        # Remove Controller subscription.
        # ----------------------------------------------------

        if self._connected:

            self._unsubscribe_controller()

            self._connected = False

        # ----------------------------------------------------
        # Manager is permanently disposed.
        # ----------------------------------------------------

        self._disposed = True

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
            "ToolManager("
            f"active="
            f"{self._active_tool_id!r}, "
            f"registered="
            f"{len(self._tool_registry)}, "
            f"disposed="
            f"{self._disposed}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolManager",
]
