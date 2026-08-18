```python
"""
GridForge V2
============

File:
    ui/plugins/toolbar_plugin.py

Purpose
-------
Composition plugin responsible for creating and managing the
application toolbar.

Architectural role
------------------
ToolbarPlugin is a UI composition component.

It:
    - creates the toolbar presentation;
    - registers toolbar actions;
    - exposes the resulting QToolBar;
    - requests tool selection through the authoritative Controller;
    - reflects authoritative tool-selection state.

It does NOT:
    - own application state;
    - own tool state;
    - create or manage ToolManager;
    - create concrete tools;
    - manipulate Core directly;
    - perform electrical calculations;
    - construct controllers or services;
    - maintain a second tool/application-state model;
    - guess service APIs;
    - import Qt directly from PySide6.

Tool selection
--------------
The authoritative tool-selection path is:

    ToolbarPlugin
        |
        v
    PluginContext.controller
        |
        v
    Controller.set_tool(tool_id)
        |
        v
    authoritative application/tool state

The toolbar never treats its QAction state as authoritative.

After requesting a tool change, the toolbar synchronizes its
presentation from:

    Controller.get_current_tool_id()

Concrete tools are frozen at exactly:

    SelectTool
    BusTool
    LineTool

Canonical identifiers:

    select
    bus
    line

Qt boundary
-----------
All Qt imports come through:

    ui.core.qt

PySide6 must not be imported directly by this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ui.core.qt import (
    QAction,
    QActionGroup,
    QMainWindow,
    QObject,
    QToolBar,
    Qt,
    Signal,
)

from ui.plugins.plugin_context import PluginContext


# ============================================================
# TOOLBAR ACTION SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolbarActionSpec:
    """
    Declarative description of one toolbar action.

    ToolbarActionSpec contains presentation metadata only.

    It does not contain application state and does not reference
    controllers, ToolManager instances, or Core objects.
    """

    action_id: str

    text: str

    tool_id: Optional[str] = None

    icon: Any = None

    tooltip: Optional[str] = None

    shortcut: Optional[str] = None

    checkable: bool = False

    checked: bool = False

    enabled: bool = True

    separator_before: bool = False

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.action_id, str)
            or not self.action_id.strip()
        ):
            raise ValueError(
                "action_id must be a non-empty string."
            )

        if not isinstance(self.text, str):
            raise TypeError(
                "text must be a string."
            )

        if (
            self.tool_id is not None
            and (
                not isinstance(self.tool_id, str)
                or not self.tool_id.strip()
            )
        ):
            raise ValueError(
                "tool_id must be a non-empty string or None."
            )

        if (
            self.tool_id is not None
            and not self.checkable
        ):
            raise ValueError(
                (
                    f"Toolbar action {self.action_id!r} "
                    "represents a tool and must be checkable."
                )
            )

        if self.checked and not self.checkable:
            raise ValueError(
                (
                    f"Toolbar action {self.action_id!r} "
                    "cannot be checked when checkable=False."
                )
            )

        if not isinstance(self.enabled, bool):
            raise TypeError(
                "enabled must be bool."
            )

        if not isinstance(self.checkable, bool):
            raise TypeError(
                "checkable must be bool."
            )

        if not isinstance(self.checked, bool):
            raise TypeError(
                "checked must be bool."
            )

        if not isinstance(self.separator_before, bool):
            raise TypeError(
                "separator_before must be bool."
            )

        if (
            self.tooltip is not None
            and not isinstance(self.tooltip, str)
        ):
            raise TypeError(
                "tooltip must be a string or None."
            )

        if (
            self.shortcut is not None
            and not isinstance(self.shortcut, str)
        ):
            raise TypeError(
                "shortcut must be a string or None."
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a Mapping."
            )


# ============================================================
# TOOLBAR PLUGIN
# ============================================================


class ToolbarPlugin(QObject):
    """
    GridForge toolbar composition plugin.

    Construction
    ------------
    The plugin is constructed without PluginContext.

    Application/UI dependencies are supplied exclusively through
    initialize(context).

    Ownership
    ---------
    The plugin owns toolbar composition and presentation bookkeeping.

    Application state remains outside the plugin.

    Dependency boundary
    -------------------
    The plugin receives the shared PluginContext during initialization.

    Tool selection is delegated through the authoritative Controller:

        context.controller.set_tool(tool_id)

    The current tool is read through:

        context.controller.get_current_tool_id()

    The plugin never manipulates ToolManager directly.
    """

    plugin_id = "toolbar"
    plugin_name = "Toolbar"
    plugin_version = "2.2"
    plugin_description = (
        "GridForge application toolbar composition."
    )

    plugin_dependencies: tuple[str, ...] = ()
    plugin_optional = False

    tool_selected = Signal(str)
    action_triggered = Signal(str)

    def __init__(
        self,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Construct an uninitialized ToolbarPlugin.

        PluginContext is intentionally not a constructor dependency.
        """

        super().__init__(parent)

        self._context: Optional[
            PluginContext
        ] = None

        self._toolbar: Optional[
            QToolBar
        ] = None

        self._actions: dict[
            str,
            QAction,
        ] = {}

        self._specs: dict[
            str,
            ToolbarActionSpec,
        ] = {}

        self._tool_action_ids: dict[
            str,
            str,
        ] = {}

        self._tool_group: Optional[
            QActionGroup
        ] = None

        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> Optional[PluginContext]:
        """Return the active shared plugin context."""

        return self._context

    @property
    def toolbar(self) -> Optional[QToolBar]:
        """Return the composed toolbar."""

        return self._toolbar

    @property
    def widget(self) -> Optional[QToolBar]:
        """Return the composed toolbar as the plugin widget."""

        return self._toolbar

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    @property
    def action_ids(self) -> tuple[str, ...]:
        """Return registered toolbar action identifiers."""

        return tuple(self._actions.keys())

    @property
    def tool_ids(self) -> tuple[str, ...]:
        """Return registered toolbar tool identifiers."""

        return tuple(self._tool_action_ids.keys())

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: PluginContext,
    ) -> QToolBar:
        """
        Initialize and compose the toolbar.

        PluginContext is the sole application dependency boundary.

        Initialization is idempotent for the same lifecycle.
        """

        if not isinstance(
            context,
            PluginContext,
        ):
            raise TypeError(
                "ToolbarPlugin requires PluginContext."
            )

        if self._initialized:
            if self._context is not context:
                raise RuntimeError(
                    (
                        "ToolbarPlugin is already initialized "
                        "with a different PluginContext."
                    )
                )

            if self._toolbar is None:
                raise RuntimeError(
                    "ToolbarPlugin is initialized without a toolbar."
                )

            self._synchronize_tool_presentation()

            return self._toolbar

        self._validate_context(context)

        self._context = context

        try:
            self._create_toolbar()
            self._create_tool_group()
            self._register_default_actions()

            self._initialized = True

            if self._toolbar is None:
                raise RuntimeError(
                    "Toolbar creation produced no toolbar."
                )

            self._synchronize_tool_presentation()

            return self._toolbar

        except Exception:
            self._rollback_initialization()
            raise

    def shutdown(self) -> None:
        """
        Shut down toolbar composition.

        Application services, Controller, ToolManager, Core, and
        application state are never modified.

        Only plugin-owned presentation objects and references are
        released.
        """

        if not self._initialized:
            return

        self._remove_toolbar()

        self._actions.clear()
        self._specs.clear()
        self._tool_action_ids.clear()

        self._tool_group = None
        self._toolbar = None
        self._context = None
        self._initialized = False

    # ========================================================
    # CONTEXT VALIDATION
    # ========================================================

    @staticmethod
    def _validate_context(
        context: PluginContext,
    ) -> None:
        """
        Validate dependencies required by toolbar composition.
        """

        main_window = context.main_window

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                (
                    "PluginContext.main_window must be "
                    "QMainWindow for ToolbarPlugin."
                )
            )

        controller = context.controller

        if controller is None:
            raise RuntimeError(
                "ToolbarPlugin requires PluginContext.controller."
            )

        set_tool = getattr(
            controller,
            "set_tool",
            None,
        )

        if not callable(set_tool):
            raise TypeError(
                (
                    "PluginContext.controller must provide "
                    "set_tool(tool_id)."
                )
            )

        get_current_tool_id = getattr(
            controller,
            "get_current_tool_id",
            None,
        )

        if not callable(get_current_tool_id):
            raise TypeError(
                (
                    "PluginContext.controller must provide "
                    "get_current_tool_id()."
                )
            )

    # ========================================================
    # TOOLBAR CREATION
    # ========================================================

    def _create_toolbar(self) -> None:
        """
        Create and attach the application toolbar.

        MainWindow remains the application-level host.
        """

        context = self._context

        if context is None:
            raise RuntimeError(
                "ToolbarPlugin has no PluginContext."
            )

        main_window = context.main_window

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                (
                    "PluginContext.main_window must be "
                    "QMainWindow for ToolbarPlugin."
                )
            )

        if self._toolbar is not None:
            raise RuntimeError(
                "ToolbarPlugin already contains a toolbar."
            )

        toolbar = QToolBar(
            "GridForge Tools",
            main_window,
        )

        toolbar.setObjectName(
            "gridforge_tool_bar"
        )

        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        main_window.addToolBar(
            Qt.ToolBarArea.TopToolBarArea,
            toolbar,
        )

        self._toolbar = toolbar

    def _create_tool_group(self) -> None:
        """
        Create the exclusive QAction group used for tool
        presentation.

        QActionGroup controls presentation exclusivity only.

        It does not own or represent application tool state.
        """

        if self._tool_group is not None:
            raise RuntimeError(
                "Toolbar tool action group already exists."
            )

        self._tool_group = QActionGroup(
            self
        )

        self._tool_group.setExclusive(True)

    # ========================================================
    # ACTION REGISTRATION
    # ========================================================

    def _register_default_actions(self) -> None:
        """Register the canonical GridForge toolbar actions."""

        for spec in default_tool_actions():
            self.add_action(spec)

    def add_action(
        self,
        spec: ToolbarActionSpec,
    ) -> QAction:
        """
        Add one toolbar action.

        The action is presentation-only.

        Tool behavior is delegated through the authoritative
        Controller boundary.
        """

        if not isinstance(
            spec,
            ToolbarActionSpec,
        ):
            raise TypeError(
                "spec must be ToolbarActionSpec."
            )

        if spec.action_id in self._actions:
            raise ValueError(
                (
                    f"Toolbar action "
                    f"{spec.action_id!r} "
                    "is already registered."
                )
            )

        if self._toolbar is None:
            raise RuntimeError(
                "Toolbar has not been initialized."
            )

        if spec.tool_id is not None:
            self._validate_tool_id(spec.tool_id)

        if spec.separator_before:
            self._toolbar.addSeparator()

        action = QAction(self)

        action.setObjectName(
            spec.action_id
        )

        action.setText(
            spec.text
        )

        action.setEnabled(
            spec.enabled
        )

        action.setCheckable(
            spec.checkable
        )

        if spec.checkable:
            action.setChecked(
                spec.checked
            )

        if spec.tooltip is not None:
            action.setToolTip(
                spec.tooltip
            )
            action.setStatusTip(
                spec.tooltip
            )

        if spec.shortcut is not None:
            action.setShortcut(
                spec.shortcut
            )

        if spec.icon is not None:
            action.setIcon(
                spec.icon
            )

        action.triggered.connect(
            lambda _checked=False,
            action_id=spec.action_id:
                self._on_action_triggered(action_id)
        )

        self._actions[
            spec.action_id
        ] = action

        self._specs[
            spec.action_id
        ] = spec

        self._toolbar.addAction(action)

        try:
            if spec.tool_id is not None:
                self._register_tool_action(
                    spec,
                    action,
                )

        except Exception:
            self._toolbar.removeAction(action)

            self._actions.pop(
                spec.action_id,
                None,
            )

            self._specs.pop(
                spec.action_id,
                None,
            )

            action.deleteLater()

            raise

        return action

    def remove_action(
        self,
        action_id: str,
    ) -> Optional[QAction]:
        """Remove and return a registered toolbar action."""

        if not isinstance(
            action_id,
            str,
        ):
            raise TypeError(
                "action_id must be a string."
            )

        action = self._actions.pop(
            action_id,
            None,
        )

        spec = self._specs.pop(
            action_id,
            None,
        )

        if action is None:
            return None

        if (
            self._tool_group is not None
            and spec is not None
            and spec.tool_id is not None
        ):
            self._tool_group.removeAction(action)

            self._tool_action_ids.pop(
                spec.tool_id,
                None,
            )

        if self._toolbar is not None:
            self._toolbar.removeAction(action)

        action.deleteLater()

        return action

    # ========================================================
    # TOOL ACTIONS
    # ========================================================

    def _register_tool_action(
        self,
        spec: ToolbarActionSpec,
        action: QAction,
    ) -> None:
        """Register one action as a mutually exclusive tool action."""

        if spec.tool_id is None:
            raise ValueError(
                "Tool action must define tool_id."
            )

        if self._tool_group is None:
            raise RuntimeError(
                "Tool action group has not been initialized."
            )

        if spec.tool_id in self._tool_action_ids:
            raise ValueError(
                (
                    f"Tool {spec.tool_id!r} "
                    "already has a toolbar action."
                )
            )

        self._tool_action_ids[
            spec.tool_id
        ] = spec.action_id

        self._tool_group.addAction(action)

    # ========================================================
    # TOOL SELECTION
    # ========================================================

    def select_tool(
        self,
        tool_id: str,
    ) -> None:
        """
        Request selection of a tool through Controller.set_tool().

        Controller remains authoritative.

        The toolbar never assumes that the requested tool became
        active. After the request, the authoritative current tool
        is read from Controller.get_current_tool_id().
        """

        self._require_initialized()

        self._validate_tool_id(tool_id)

        context = self._context

        if context is None:
            raise RuntimeError(
                "ToolbarPlugin has no PluginContext."
            )

        controller = context.controller

        if controller is None:
            raise RuntimeError(
                "PluginContext.controller is required for tool selection."
            )

        set_tool = getattr(
            controller,
            "set_tool",
            None,
        )

        if not callable(set_tool):
            raise TypeError(
                (
                    "PluginContext.controller must provide "
                    "set_tool(tool_id)."
                )
            )

        get_current_tool_id = getattr(
            controller,
            "get_current_tool_id",
            None,
        )

        if not callable(get_current_tool_id):
            raise TypeError(
                (
                    "PluginContext.controller must provide "
                    "get_current_tool_id()."
                )
            )

        set_tool(tool_id)

        authoritative_tool_id = get_current_tool_id()

        if authoritative_tool_id is None:
            self._clear_tool_presentation()
            return

        self._validate_tool_id(
            authoritative_tool_id
        )

        self._set_active_tool_presentation(
            authoritative_tool_id
        )

        if authoritative_tool_id == tool_id:
            self.tool_selected.emit(
                authoritative_tool_id
            )

    def synchronize_tool(self) -> None:
        """
        Synchronize toolbar presentation from the authoritative
        Controller tool state.

        No application state is modified.
        """

        self._require_initialized()

        self._synchronize_tool_presentation()

    def _synchronize_tool_presentation(self) -> None:
        """
        Read the authoritative current tool from Controller and
        synchronize QAction presentation.
        """

        context = self._context

        if context is None:
            raise RuntimeError(
                "ToolbarPlugin has no PluginContext."
            )

        controller = context.controller

        if controller is None:
            raise RuntimeError(
                "PluginContext.controller is required."
            )

        get_current_tool_id = getattr(
            controller,
            "get_current_tool_id",
            None,
        )

        if not callable(get_current_tool_id):
            raise TypeError(
                (
                    "PluginContext.controller must provide "
                    "get_current_tool_id()."
                )
            )

        tool_id = get_current_tool_id()

        if tool_id is None:
            self._clear_tool_presentation()
            return

        self._validate_tool_id(tool_id)

        self._set_active_tool_presentation(
            tool_id
        )

    # ========================================================
    # ACTION HANDLING
    # ========================================================

    def trigger_action(
        self,
        action_id: str,
    ) -> None:
        """Programmatically trigger a registered toolbar action."""

        action = self._actions.get(action_id)

        if action is None:
            raise KeyError(
                f"Unknown toolbar action: {action_id!r}"
            )

        action.trigger()

    def _on_action_triggered(
        self,
        action_id: str,
    ) -> None:
        """
        Handle one QAction activation.

        Tool actions are routed through select_tool().

        Non-tool actions are exposed through action_triggered
        rather than being dispatched through an invented service API.
        """

        spec = self._specs.get(action_id)

        if spec is None:
            return

        if spec.tool_id is not None:
            self.select_tool(spec.tool_id)
        else:
            self.action_triggered.emit(action_id)

    # ========================================================
    # PRESENTATION SYNCHRONIZATION
    # ========================================================

    def _set_active_tool_presentation(
        self,
        tool_id: str,
    ) -> None:
        """
        Synchronize toolbar presentation with authoritative selection.

        This method changes Qt presentation only.
        """

        action_id = self._tool_action_ids.get(tool_id)

        if action_id is None:
            self._clear_tool_presentation()
            return

        action = self._actions.get(action_id)

        if action is None:
            self._clear_tool_presentation()
            return

        for candidate in self._tool_group.actions():
            candidate.setChecked(
                candidate is action
            )

    def _clear_tool_presentation(self) -> None:
        """Clear all tool-selection presentation state."""

        if self._tool_group is None:
            return

        for action in self._tool_group.actions():
            action.setChecked(False)

    # ========================================================
    # ACTION PRESENTATION
    # ========================================================

    def action(
        self,
        action_id: str,
    ) -> Optional[QAction]:
        """Return a registered QAction."""

        return self._actions.get(action_id)

    def set_action_enabled(
        self,
        action_id: str,
        enabled: bool,
    ) -> None:
        """Change an action's presentation enabled state."""

        if not isinstance(enabled, bool):
            raise TypeError(
                "enabled must be bool."
            )

        action = self._actions.get(action_id)

        if action is None:
            raise KeyError(
                f"Unknown toolbar action: {action_id!r}"
            )

        action.setEnabled(enabled)

    def set_action_checked(
        self,
        action_id: str,
        checked: bool,
    ) -> None:
        """
        Change a non-tool action's presentation checked state.

        Tool actions must use the dedicated tool-selection path.
        """

        if not isinstance(checked, bool):
            raise TypeError(
                "checked must be bool."
            )

        spec = self._specs.get(action_id)

        if spec is None:
            raise KeyError(
                f"Unknown toolbar action: {action_id!r}"
            )

        if spec.tool_id is not None:
            raise ValueError(
                (
                    f"Tool action {action_id!r} "
                    "must be synchronized through select_tool()."
                )
            )

        self._actions[action_id].setChecked(checked)

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def has_action(
        self,
        action_id: str,
    ) -> bool:
        """Return whether an action is registered."""

        return action_id in self._actions

    def has_tool(
        self,
        tool_id: str,
    ) -> bool:
        """Return whether a tool action is registered."""

        return tool_id in self._tool_action_ids

    def tool_action(
        self,
        tool_id: str,
    ) -> Optional[QAction]:
        """Return the QAction associated with a tool."""

        action_id = self._tool_action_ids.get(tool_id)

        if action_id is None:
            return None

        return self._actions.get(action_id)

    # ========================================================
    # CLEANUP
    # ========================================================

    def _remove_toolbar(self) -> None:
        """
        Remove the plugin-owned toolbar from MainWindow.

        MainWindow itself is never destroyed.
        """

        toolbar = self._toolbar

        if toolbar is None:
            return

        context = self._context

        if context is not None:
            main_window = context.main_window

            if isinstance(
                main_window,
                QMainWindow,
            ):
                main_window.removeToolBar(toolbar)

        for action in tuple(self._actions.values()):
            toolbar.removeAction(action)

        toolbar.deleteLater()

    def _rollback_initialization(self) -> None:
        """
        Roll back partially completed initialization.

        Only plugin-owned presentation state is removed.
        """

        self._remove_toolbar()

        self._actions.clear()
        self._specs.clear()
        self._tool_action_ids.clear()

        self._tool_group = None
        self._toolbar = None
        self._context = None
        self._initialized = False

    # ========================================================
    # VALIDATION
    # ========================================================

    def _require_initialized(self) -> None:
        """Require an active plugin lifecycle."""

        if not self._initialized:
            raise RuntimeError(
                "ToolbarPlugin has not been initialized."
            )

        if self._context is None:
            raise RuntimeError(
                "ToolbarPlugin is initialized without PluginContext."
            )

        if self._toolbar is None:
            raise RuntimeError(
                "ToolbarPlugin is initialized without a toolbar."
            )

    @staticmethod
    def _validate_tool_id(
        tool_id: str,
    ) -> None:
        """
        Validate a canonical GridForge toolbar tool identifier.

        The concrete tool set is intentionally frozen to exactly:

            select
            bus
            line
        """

        if (
            not isinstance(tool_id, str)
            or not tool_id.strip()
        ):
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        if tool_id not in {
            "select",
            "bus",
            "line",
        }:
            raise ValueError(
                (
                    f"Unsupported GridForge tool: "
                    f"{tool_id!r}. "
                    "The concrete tool set is limited to "
                    "select, bus, and line."
                )
            )


# ============================================================
# DEFAULT TOOLBAR SPECIFICATIONS
# ============================================================


def default_tool_actions() -> tuple[
    ToolbarActionSpec,
    ...
]:
    """
    Return the canonical GridForge toolbar tool actions.

    Exactly three concrete tools are exposed:

        SelectTool
        BusTool
        LineTool
    """

    return (
        ToolbarActionSpec(
            action_id="tool.select",
            text="Select",
            tool_id="select",
            tooltip="Select and inspect objects.",
            checkable=True,
            checked=True,
        ),
        ToolbarActionSpec(
            action_id="tool.bus",
            text="Bus",
            tool_id="bus",
            tooltip="Create a bus.",
            checkable=True,
        ),
        ToolbarActionSpec(
            action_id="tool.line",
            text="Line",
            tool_id="line",
            tooltip="Create a line connection.",
            checkable=True,
        ),
    )


# ============================================================
# FACTORY
# ============================================================


def create_toolbar_plugin(
    parent: Optional[QObject] = None,
) -> ToolbarPlugin:
    """
    Create an uninitialized ToolbarPlugin.

    PluginContext is supplied during initialize().
    """

    return ToolbarPlugin(
        parent=parent
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "ToolbarActionSpec",
    "ToolbarPlugin",
    "default_tool_actions",
    "create_toolbar_plugin",
]
```
