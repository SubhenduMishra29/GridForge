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
        ├── active tool instance
        ├── activation
        ├── deactivation
        ├── cancellation
        └── reset
              │
              ▼
          Active Tool

ToolManager is the sole owner of concrete tool instances and
their lifecycle.

Responsibilities
----------------
ToolManager:

    - owns the active tool instance;
    - creates tool instances through the registered tool
      factories/classes;
    - responds to Controller tool-selection changes;
    - activates the requested tool;
    - deactivates the previous tool;
    - cancels active tool interaction;
    - resets tool state;
    - exposes the active tool and ID;
    - provides tool diagnostics.

ToolManager does NOT:

    - decide which tool the application should select;
    - store application-level requested tool state;
    - implement tool behavior;
    - process mouse events;
    - process keyboard events;
    - perform snapping;
    - perform selection;
    - perform navigation;
    - modify the Core model directly;
    - render permanent graphics.

Controller Ownership
--------------------
Controller owns application-level tool selection.

Controller stores the requested tool identifier and emits:

    tool_changed(new_tool_id, previous_tool_id)

ToolManager subscribes to this signal/event and translates the
requested identifier into the concrete tool lifecycle.

Therefore:

    Controller
        = selection intent

    ToolManager
        = concrete tool lifecycle

InteractionManager
------------------
InteractionManager does not subscribe to Controller's
tool_changed event.

InteractionManager only asks ToolManager for the active tool
and routes input to it.

Tool Ownership
--------------
ToolManager is the single owner of concrete tool instances.

A tool may be:

    - registered by class/factory;
    - lazily instantiated;
    - activated;
    - deactivated;
    - cancelled;
    - reset.

Tools receive the shared interaction services required by the
UI architecture.

Expected optional tool constructor contract:

    Tool(
        interaction_manager=...,
        preview=...,
    )

Lifecycle contract
------------------
Tool implementations may provide:

    activate()
    deactivate()
    cancel()
    reset()
    dispose()

Lifecycle methods are optional at the protocol level.

When absent, the corresponding lifecycle transition is treated
as a no-op.

Important
---------
ToolManager must never invoke Controller.set_tool() while
processing Controller.tool_changed.

Doing so would create a feedback loop and duplicate ownership.

Qt Architecture
---------------
All Qt dependencies must pass through:

    ui.core.qt

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
        # The registry contains tool factories/classes.
        # ToolManager owns instantiated tools separately.
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

        self._connected = False

        # ----------------------------------------------------
        # Optional initial registry.
        # ----------------------------------------------------

        if tool_registry is not None:
            self._load_registry(
                tool_registry
            )

        # ----------------------------------------------------
        # Controller subscription.
        #
        # This is the sole tool-selection subscription in the
        # canvas interaction architecture.
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

        Supported Controller subscription styles:

            controller.subscribe(
                "tool_changed",
                callback
            )

        or a compatible subscribe implementation that accepts
        the same arguments.
        """

        subscribe = getattr(
            self.controller,
            "subscribe",
            None,
        )

        if not callable(subscribe):
            raise TypeError(
                "controller must provide subscribe()."
            )

        try:
            subscribe(
                "tool_changed",
                self._on_tool_changed,
            )
        except TypeError:
            # ------------------------------------------------
            # Some lightweight controller implementations may
            # expose subscribe(callback, event_name).
            #
            # Do not silently assume that interface.
            # Retry only for the known alternate ordering.
            # ------------------------------------------------
            try:
                subscribe(
                    self._on_tool_changed,
                    "tool_changed",
                )
            except TypeError as exc:
                raise TypeError(
                    "controller.subscribe() must support "
                    "tool_changed subscription."
                ) from exc

        self._connected = True

    # --------------------------------------------------------

    def _unsubscribe_controller(
        self,
    ) -> None:
        """
        Remove the Controller tool-selection subscription when
        the Controller exposes an unsubscribe contract.

        If unsubscribe is unavailable, lifecycle remains safe;
        the manager simply marks itself disconnected.
        """

        unsubscribe = getattr(
            self.controller,
            "unsubscribe",
            None,
        )

        if not callable(unsubscribe):
            return

        try:
            unsubscribe(
                "tool_changed",
                self._on_tool_changed,
            )
        except TypeError:
            try:
                unsubscribe(
                    self._on_tool_changed,
                    "tool_changed",
                )
            except TypeError:
                # ------------------------------------------------
                # Do not make disposal fail merely because a
                # controller implementation does not expose the
                # alternate unsubscribe signature.
                # ------------------------------------------------
                pass

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

        Parameters
        ----------
        tool_id:
            Stable application-level tool identifier.

        factory:
            Callable returning a tool instance.

        Registration does not instantiate the tool and does not
        activate it.
        """

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
        Register multiple tool factories.
        """

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

        for tool_id, factory in tools.items():
            self.register_tool(
                tool_id,
                factory,
            )

    # --------------------------------------------------------

    def unregister_tool(
        self,
        tool_id: str,
    ) -> None:
        """
        Unregister a tool.

        The active tool cannot be unregistered.
        """

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

        instance = self._tool_instances.pop(
            tool_id,
            None,
        )

        if instance is not None:
            self._dispose_tool(
                instance
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

            mapping-like object

        or:

            object exposing get_tools()

        or:

            object exposing items()
        """

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
                dict(items())
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

        It does NOT call Controller.set_tool().
        """

        # ----------------------------------------------------
        # Ignore notifications after disposal.
        # ----------------------------------------------------

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
        Lazily create a tool instance.

        ToolManager owns the resulting instance.
        """

        factory = self._tool_registry.get(
            tool_id
        )

        if factory is None:
            raise KeyError(
                f"Unknown tool ID: {tool_id!r}"
            )

        # ----------------------------------------------------
        # Preferred constructor contract.
        # ----------------------------------------------------

        try:
            return factory(
                interaction_manager=(
                    self.interaction_manager
                ),
                preview=self.preview,
            )
        except TypeError as first_error:

            # ------------------------------------------------
            # Fallback for factories that intentionally expose
            # a simpler constructor.
            #
            # The fallback is deliberately limited to a
            # zero-argument factory.
            # ------------------------------------------------

            try:
                return factory()
            except TypeError as second_error:
                raise TypeError(
                    f"Unable to instantiate tool "
                    f"{tool_id!r}. Factory must support "
                    "(interaction_manager=..., preview=...) "
                    "or a zero-argument constructor."
                ) from second_error

    # --------------------------------------------------------

    def _get_or_create_tool(
        self,
        tool_id: str,
    ) -> Any:
        """
        Return an existing tool instance or lazily create one.
        """

        if tool_id in self._tool_instances:
            return self._tool_instances[
                tool_id
            ]

        tool = self._create_tool(
            tool_id
        )

        if tool is None:
            raise RuntimeError(
                f"Tool factory returned None: {tool_id!r}"
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

        return self._active_tool

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the identifier of the active tool.
        """

        return self._active_tool_id

    # --------------------------------------------------------

    @property
    def active_tool(
        self,
    ) -> Optional[Any]:
        """
        Read-only active-tool property.
        """

        return self._active_tool

    # --------------------------------------------------------

    @property
    def active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Read-only active-tool ID property.
        """

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

        Lifecycle:

            current.deactivate()
                ↓
            new tool creation
                ↓
            new.activate()
                ↓
            active state updated

        Parameters
        ----------
        tool_id:
            Requested application tool identifier.

            None deactivates the current tool.

        Returns
        -------
        object | None
            Newly active tool.
        """

        if tool_id is None:
            self.deactivate()
            return None

        self._validate_tool_id(
            tool_id
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
        # Validate before deactivating the current tool.
        #
        # This prevents the active tool from being lost when
        # Controller requests an unknown/unregistered tool.
        # ----------------------------------------------------

        if tool_id not in self._tool_registry:
            raise KeyError(
                f"Unknown tool ID: {tool_id!r}"
            )

        previous_tool = (
            self._active_tool
        )

        # ----------------------------------------------------
        # Deactivate previous tool.
        # ----------------------------------------------------

        if previous_tool is not None:
            self._deactivate_tool(
                previous_tool
            )

        # ----------------------------------------------------
        # Create or reuse requested tool.
        # ----------------------------------------------------

        new_tool = self._get_or_create_tool(
            tool_id
        )

        # ----------------------------------------------------
        # Commit active state before activate() so the tool
        # can query ToolManager indirectly through its shared
        # InteractionManager without observing stale state.
        # ----------------------------------------------------

        self._active_tool_id = tool_id
        self._active_tool = new_tool

        try:
            self._activate_tool(
                new_tool
            )
        except Exception:
            # ----------------------------------------------
            # Roll back active state if activation fails.
            # ----------------------------------------------

            self._active_tool_id = None
            self._active_tool = None

            raise

        return new_tool

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(
        self,
    ) -> None:
        """
        Deactivate the current tool.

        No Controller tool-selection mutation is performed.

        This is an important architectural boundary:

            ToolManager.deactivate()
                ≠
            Controller.set_tool(None)
        """

        tool = self._active_tool

        if tool is None:
            self._active_tool_id = None
            return

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

        Cancellation is delegated to the active tool.

        The tool itself remains active unless its cancel()
        implementation or higher-level application logic changes
        the active tool.

        Returns
        -------
        bool
            True when a cancellation target existed and the
            cancellation lifecycle was invoked.
        """

        tool = self._active_tool

        if tool is None:
            self._clear_preview()
            return False

        handler = getattr(
            tool,
            "cancel",
            None,
        )

        if callable(handler):
            result = handler()

            self._clear_preview()

            if result is None:
                return True

            return bool(result)

        # ----------------------------------------------------
        # A tool without an explicit cancel contract still
        # receives generic preview cleanup.
        # ----------------------------------------------------

        self._clear_preview()

        return True

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset tool interaction state.

        The active tool remains active.

        This is intended for canvas/model/workspace reset
        operations where tool selection itself should remain
        unchanged.
        """

        tool = self._active_tool

        if tool is not None:
            handler = getattr(
                tool,
                "reset",
                None,
            )

            if callable(handler):
                handler()

        self._clear_preview()

    # ========================================================
    # LIFECYCLE HELPERS
    # ========================================================

    @staticmethod
    def _activate_tool(
        tool: Any,
    ) -> None:
        """
        Invoke a tool's activation lifecycle callback.
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
        Invoke a tool's deactivation lifecycle callback.
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
        Dispose a tool instance when it is permanently removed.
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
            tool disposal
                    ↓
            Controller unsubscribe
        """

        if not self._connected:
            return

        # ----------------------------------------------------
        # Deactivate active tool first.
        # ----------------------------------------------------

        if self._active_tool is not None:
            self._deactivate_tool(
                self._active_tool
            )

        self._active_tool = None
        self._active_tool_id = None

        self._clear_preview()

        # ----------------------------------------------------
        # Dispose every instantiated tool.
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

        self._unsubscribe_controller()

        self._connected = False

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
            f"{len(self._tool_registry)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolManager",
]
