# ============================================================
# File: ui/tools/tool_manager.py
# GridForge V2 — Tool Manager
# ============================================================

"""
GridForge V2 — Tool Manager
===========================

Central runtime manager for interactive UI tools.

Architecture
------------

    MainToolbar / UI Plugin
              │
              │ request tool
              ▼
         ToolManager
              │
              ├── SelectTool
              ├── BusTool
              └── LineTool
                     │
                     ▼
              Canvas interaction
                     │
                     ▼
              Controller / Core

Responsibilities
----------------
ToolManager is responsible for:

    - registering tool implementations;
    - resolving tools by stable identifier;
    - creating and retaining tool instances;
    - tracking the active tool;
    - activating a selected tool;
    - deactivating the previous tool;
    - providing controlled tool lifecycle;
    - dispatching interaction to the active tool when supported;
    - providing diagnostics.

ToolManager does NOT:

    - create toolbar widgets;
    - create QAction objects;
    - know about MainToolbar;
    - discover plugins;
    - modify the Core model directly;
    - perform electrical calculations;
    - perform rendering;
    - own the canvas;
    - own commands;
    - implement individual tool behavior.

Tool Ownership
--------------

ToolManager owns tool instances after registration/creation.

The individual tool class owns its interaction behavior.

Controller/canvas/application context is supplied to the tool
through the ToolManager rather than being stored as global
application state.

Registration
------------

Tools are identified by stable string identifiers.

Example:

    manager.register("select", SelectTool)
    manager.register("bus", BusTool)
    manager.register("line", LineTool)

Registration of the same class under the same identifier is
idempotent.

Registering a different class under an existing identifier is
prohibited.

Lifecycle
---------

    register()
        │
        ▼
    resolve()
        │
        ▼
    get_instance()
        │
        ▼
    activate()
        │
        ▼
    active tool
        │
        ▼
    deactivate()
        │
        ▼
    another tool / no tool

Tool Contract
-------------

A tool implementation is expected to be a class.

The manager does not require a specific inheritance hierarchy.

Supported lifecycle methods are discovered conservatively:

    activate(...)
    deactivate(...)

Optional interaction methods may be dispatched when present.

The ToolManager intentionally does not impose Qt-specific base
classes on tools.
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, Iterator, List, Optional, Type


class ToolManager:
    """
    Runtime manager for GridForge interactive tools.

    ToolManager is deliberately independent of toolbar widgets,
    Qt action objects, rendering infrastructure, and Core model
    mutation.

    Parameters
    ----------
    context:
        Optional application/tool context supplied to tools when
        they are created.

    Notes
    -----
    The context is intentionally opaque to ToolManager. The
    manager does not interpret or modify it.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        context: Any = None,
    ) -> None:
        """
        Initialize an empty ToolManager.
        """

        self._context = context

        self._tool_classes: Dict[
            str,
            Type[Any],
        ] = {}

        self._tool_instances: Dict[
            str,
            Any,
        ] = {}

        self._active_tool_id: Optional[str] = None

        self._disposed = False

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_tool_id(
        tool_id: str,
    ) -> str:
        """
        Validate and normalize a tool identifier.
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
                "tool_id must be a non-empty string."
            )

        return tool_id

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        tool_id: str,
        tool_class: Type[Any],
    ) -> Type[Any]:
        """
        Register a tool implementation class.

        Parameters
        ----------
        tool_id:
            Stable tool identifier.

        tool_class:
            Tool implementation class.

        Returns
        -------
        type
            The registered tool class.

        Raises
        ------
        RuntimeError
            If the manager has been disposed.

        TypeError
            If tool_class is not a class.

        ValueError
            If a different class is already registered under the
            same identifier.

        Notes
        -----
        Registering the exact same class under the same identifier
        is idempotent.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

        tool_id = self._validate_tool_id(
            tool_id
        )

        if not inspect.isclass(
            tool_class
        ):
            raise TypeError(
                "tool_class must be a class."
            )

        existing = self._tool_classes.get(
            tool_id
        )

        if existing is not None:

            if existing is tool_class:
                return tool_class

            raise ValueError(
                "Tool already registered with ID "
                f"'{tool_id}': "
                f"'{existing.__name__}'."
            )

        self._tool_classes[
            tool_id
        ] = tool_class

        return tool_class

    # ========================================================
    # UNREGISTER
    # ========================================================

    def unregister(
        self,
        tool_id: str,
    ) -> bool:
        """
        Remove a registered tool.

        A tool cannot be unregistered while it is active.

        Returns
        -------
        bool
            True if removed, otherwise False.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

        tool_id = self._validate_tool_id(
            tool_id
        )

        if tool_id == self._active_tool_id:
            raise ValueError(
                "Cannot unregister the active tool "
                f"'{tool_id}'."
            )

        if tool_id not in self._tool_classes:
            return False

        self._tool_classes.pop(
            tool_id
        )

        instance = self._tool_instances.pop(
            tool_id,
            None,
        )

        self._dispose_tool(
            instance
        )

        return True

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_tool_class(
        self,
        tool_id: str,
    ) -> Optional[Type[Any]]:
        """
        Return the registered tool class.

        Returns None when the identifier is not registered.
        """

        tool_id = self._validate_tool_id(
            tool_id
        )

        return self._tool_classes.get(
            tool_id
        )

    # --------------------------------------------------------

    def require_tool_class(
        self,
        tool_id: str,
    ) -> Type[Any]:
        """
        Return a registered tool class or raise KeyError.
        """

        tool_id = self._validate_tool_id(
            tool_id
        )

        tool_class = self._tool_classes.get(
            tool_id
        )

        if tool_class is None:
            raise KeyError(
                "No tool registered with ID "
                f"'{tool_id}'."
            )

        return tool_class

    # --------------------------------------------------------

    def is_registered(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return True when a tool identifier is registered.
        """

        tool_id = self._validate_tool_id(
            tool_id
        )

        return tool_id in self._tool_classes

    # ========================================================
    # TOOL INSTANCES
    # ========================================================

    def get_instance(
        self,
        tool_id: str,
    ) -> Any:
        """
        Return the tool instance for a registered tool.

        Tool instances are created lazily.

        The manager first attempts:

            ToolClass(context)

        and, when no context was supplied, permits:

            ToolClass()

        A tool implementation must therefore support one of these
        construction contracts.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

        tool_id = self._validate_tool_id(
            tool_id
        )

        existing = self._tool_instances.get(
            tool_id
        )

        if existing is not None:
            return existing

        tool_class = self.require_tool_class(
            tool_id
        )

        instance = self._create_tool_instance(
            tool_class
        )

        self._tool_instances[
            tool_id
        ] = instance

        return instance

    # --------------------------------------------------------

    def _create_tool_instance(
        self,
        tool_class: Type[Any],
    ) -> Any:
        """
        Create one tool instance.

        The manager keeps construction deliberately small and
        framework-independent.
        """

        if self._context is not None:

            try:
                return tool_class(
                    self._context
                )
            except TypeError as context_error:

                try:
                    return tool_class()
                except TypeError:
                    raise TypeError(
                        "Tool class "
                        f"'{tool_class.__name__}' must support "
                        "construction with the supplied context "
                        "or a zero-argument constructor."
                    ) from context_error

        try:
            return tool_class()
        except TypeError as error:
            raise TypeError(
                "Tool class "
                f"'{tool_class.__name__}' requires a context, "
                "but ToolManager was created without one."
            ) from error

    # ========================================================
    # ACTIVE TOOL
    # ========================================================

    @property
    def active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the identifier of the active tool.
        """

        return self._active_tool_id

    # --------------------------------------------------------

    def get_active_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the active tool instance.

        Returns None when no tool is active.
        """

        if self._active_tool_id is None:
            return None

        return self._tool_instances.get(
            self._active_tool_id
        )

    # ========================================================
    # ACTIVATION
    # ========================================================

    def activate(
        self,
        tool_id: str,
    ) -> Any:
        """
        Activate a registered tool.

        The currently active tool is deactivated before the new
        tool becomes active.

        Re-activating the currently active tool is idempotent and
        does not call its lifecycle methods again.

        Returns
        -------
        object
            The activated tool instance.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

        tool_id = self._validate_tool_id(
            tool_id
        )

        if tool_id == self._active_tool_id:

            active_tool = self.get_active_tool()

            if active_tool is None:
                raise RuntimeError(
                    "Active tool state is inconsistent."
                )

            return active_tool

        tool = self.get_instance(
            tool_id
        )

        previous_tool = self.get_active_tool()

        if previous_tool is not None:
            self._call_lifecycle(
                previous_tool,
                "deactivate",
            )

        self._active_tool_id = None

        try:

            self._call_lifecycle(
                tool,
                "activate",
            )

        except Exception:
            # ------------------------------------------------
            # Preserve the invariant that a failed activation
            # leaves the manager without a falsely active tool.
            # ------------------------------------------------
            self._active_tool_id = None
            raise

        self._active_tool_id = tool_id

        return tool

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(
        self,
    ) -> bool:
        """
        Deactivate the current tool.

        Returns
        -------
        bool
            True when a tool was active and was deactivated.
            False when no tool was active.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

        if self._active_tool_id is None:
            return False

        tool_id = self._active_tool_id

        tool = self._tool_instances.get(
            tool_id
        )

        self._active_tool_id = None

        if tool is not None:
            self._call_lifecycle(
                tool,
                "deactivate",
            )

        return True

    # ========================================================
    # LIFECYCLE
    # ========================================================

    @staticmethod
    def _call_lifecycle(
        tool: Any,
        method_name: str,
    ) -> None:
        """
        Invoke an optional tool lifecycle method.

        Lifecycle methods are intentionally optional so that
        lightweight tools are not forced to implement no-op
        methods.
        """

        method = getattr(
            tool,
            method_name,
            None,
        )

        if method is None:
            return

        if not callable(
            method
        ):
            raise TypeError(
                f"Tool lifecycle member "
                f"'{method_name}' must be callable."
            )

        method()

    # ========================================================
    # ACTIVE TOOL DISPATCH
    # ========================================================

    def dispatch(
        self,
        method_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Dispatch a method to the active tool.

        Parameters
        ----------
        method_name:
            Name of the interaction method to invoke.

        Returns
        -------
        Any
            Return value from the active tool method.

        Raises
        ------
        RuntimeError
            If no tool is active.

        AttributeError
            If the active tool does not implement the requested
            interaction method.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

        if not isinstance(
            method_name,
            str,
        ):
            raise TypeError(
                "method_name must be a string."
            )

        method_name = method_name.strip()

        if not method_name:
            raise ValueError(
                "method_name must be a non-empty string."
            )

        tool = self.get_active_tool()

        if tool is None:
            raise RuntimeError(
                "No active tool."
            )

        method = getattr(
            tool,
            method_name,
            None,
        )

        if not callable(
            method
        ):
            raise AttributeError(
                "Active tool "
                f"'{self._active_tool_id}' does not provide "
                f"callable method '{method_name}'."
            )

        return method(
            *args,
            **kwargs,
        )

    # ========================================================
    # REGISTRATION INFORMATION
    # ========================================================

    def get_tool_ids(
        self,
    ) -> List[str]:
        """
        Return registered tool identifiers.

        Registration order is preserved.
        """

        return list(
            self._tool_classes.keys()
        )

    # --------------------------------------------------------

    def get_tool_instances(
        self,
    ) -> Dict[str, Any]:
        """
        Return a detached snapshot of created tool instances.
        """

        return dict(
            self._tool_instances
        )

    # --------------------------------------------------------

    def items(
        self,
    ) -> Iterator[
        tuple[str, Type[Any]]
    ]:
        """
        Iterate over:

            (tool_id, tool_class)

        registrations.
        """

        return iter(
            self._tool_classes.items()
        )

    # ========================================================
    # CONTEXT
    # ========================================================

    def get_context(
        self,
    ) -> Any:
        """
        Return the opaque tool context.
        """

        return self._context

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic manager state.
        """

        return {
            "disposed": self._disposed,
            "tool_count": len(
                self._tool_classes
            ),
            "tool_ids": list(
                self._tool_classes.keys()
            ),
            "created_instance_count": len(
                self._tool_instances
            ),
            "active_tool_id": self._active_tool_id,
        }

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Deactivate and remove all registered tools.

        The manager remains usable after clear().
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
            )

        self.deactivate()

        instances = list(
            self._tool_instances.values()
        )

        self._tool_classes.clear()
        self._tool_instances.clear()

        for instance in instances:
            self._dispose_tool(
                instance
            )

    # ========================================================
    # TOOL DISPOSAL
    # ========================================================

    @staticmethod
    def _dispose_tool(
        tool: Any,
    ) -> None:
        """
        Call an optional dispose() method on a tool.

        ToolManager does not require a disposal interface, but
        gives tools a controlled lifecycle hook when provided.
        """

        if tool is None:
            return

        dispose = getattr(
            tool,
            "dispose",
            None,
        )

        if dispose is None:
            return

        if not callable(
            dispose
        ):
            raise TypeError(
                "Tool dispose member must be callable."
            )

        dispose()

    # ========================================================
    # DISPOSE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Permanently dispose the ToolManager.

        The operation is idempotent.
        """

        if self._disposed:
            return

        self.deactivate()

        instances = list(
            self._tool_instances.values()
        )

        self._tool_classes.clear()
        self._tool_instances.clear()

        for instance in instances:
            self._dispose_tool(
                instance
            )

        self._context = None

        self._disposed = True

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered tools.
        """

        return len(
            self._tool_classes
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

        return (
            "ToolManager("
            f"tools={list(self._tool_classes.keys())!r}, "
            f"active={self._active_tool_id!r}, "
            f"disposed={self._disposed}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolManager",
]
