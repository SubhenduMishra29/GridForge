"""
GridForge V2
============

File:
    ui/plugins/toolbar_plugin.py

Purpose
-------
Composition plugin responsible for creating and managing the
application toolbar area.

Architectural rules
-------------------
- ToolbarPlugin owns toolbar composition, not application state.
- Toolbar actions delegate to the tool/action system.
- ToolbarPlugin must not mutate Core directly.
- ToolbarPlugin must not perform electrical calculations.
- ToolbarPlugin must not duplicate ToolManager state.
- Concrete tools remain limited to:
    SelectTool
    BusTool
    LineTool
- MainWindow remains thin and plugin-driven.
- PySide6 is the only Qt binding used by GridForge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QButtonGroup,
    QToolBar,
    QToolButton,
    QWidget,
)

from ui.core.qt import QtWidgets


# ============================================================
# TOOLBAR ITEM SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolbarActionSpec:
    """
    Declarative description of one toolbar action.

    The specification contains presentation and dispatch metadata.
    It does not own application state.
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
        if not isinstance(
            self.action_id,
            str,
        ) or not self.action_id.strip():
            raise ValueError(
                "action_id must be a non-empty string."
            )

        if not isinstance(
            self.text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        if (
            self.tool_id is not None
            and not isinstance(
                self.tool_id,
                str,
            )
        ):
            raise TypeError(
                "tool_id must be a string or None."
            )


# ============================================================
# TOOLBAR CONTEXT
# ============================================================


@dataclass(slots=True)
class ToolbarPluginContext:
    """
    Runtime dependencies supplied to ToolbarPlugin.

    Services are references only. ToolbarPlugin does not create or own
    application/domain services.
    """

    parent: Optional[QWidget] = None

    main_window: Optional[QWidget] = None

    tool_manager: Any = None

    action_manager: Any = None

    dispatcher: Any = None

    actions: Iterable[
        ToolbarActionSpec
    ] = field(
        default_factory=tuple
    )


# ============================================================
# TOOLBAR PLUGIN
# ============================================================


class ToolbarPlugin(QObject):
    """
    Composition plugin for the GridForge main toolbar.

    The toolbar is a presentation surface. Selecting a tool delegates
    to ToolManager or the configured action/dispatch layer.
    """

    plugin_id = "toolbar"
    plugin_name = "Toolbar"
    plugin_version = "1.0"

    tool_selected = Signal(str)

    action_triggered = Signal(str)

    def __init__(
        self,
        context: Optional[
            ToolbarPluginContext
        ] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._context = (
            context
            or ToolbarPluginContext()
        )

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

        self._tool_buttons: dict[
            str,
            QToolButton,
        ] = {}

        self._tool_action_ids: dict[
            str,
            str,
        ] = {}

        self._tool_group: Optional[
            QButtonGroup
        ] = None

        self._initialized = False

        self._tool_manager_connected = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> ToolbarPluginContext:
        """Return the plugin context."""

        return self._context

    @property
    def toolbar(
        self,
    ) -> Optional[QToolBar]:
        """Return the toolbar widget."""

        return self._toolbar

    @property
    def widget(
        self,
    ) -> Optional[QToolBar]:
        """Return the toolbar as the plugin widget."""

        return self._toolbar

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    @property
    def action_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered action identifiers."""

        return tuple(
            self._actions.keys()
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Optional[
            ToolbarPluginContext
        ] = None,
    ) -> QToolBar:
        """
        Initialize the toolbar plugin.

        Initialization is idempotent.
        """

        if self._initialized:
            assert self._toolbar is not None
            return self._toolbar

        if context is not None:
            self._context = context

        self._create_toolbar()

        self._create_tool_group()

        self._register_context_actions()

        self._wire_services()

        self._initialized = True

        assert self._toolbar is not None

        return self._toolbar

    def shutdown(self) -> None:
        """
        Disconnect services and release plugin-owned bookkeeping.

        Qt ownership remains responsible for the actual toolbar widget.
        """

        self._disconnect_services()

        self._actions.clear()
        self._specs.clear()
        self._tool_buttons.clear()
        self._tool_action_ids.clear()

        self._tool_group = None
        self._toolbar = None

        self._initialized = False

    # ========================================================
    # TOOLBAR CREATION
    # ========================================================

    def _create_toolbar(self) -> None:
        """Create the QToolBar."""

        parent = self._context.main_window

        self._toolbar = QToolBar(
            "GridForge Tools",
            parent,
        )

        self._toolbar.setObjectName(
            "gridforge_tool_bar"
        )

        self._toolbar.setMovable(
            False
        )

        self._toolbar.setFloatable(
            False
        )

    def _create_tool_group(self) -> None:
        """
        Create the exclusive tool-selection group.

        Only tool actions are placed in this group. Ordinary commands
        remain independent actions.
        """

        self._tool_group = QButtonGroup(
            self
        )

        self._tool_group.setExclusive(
            True
        )

        self._tool_group.idClicked.connect(
            self._on_tool_button_clicked
        )

    # ========================================================
    # ACTION REGISTRATION
    # ========================================================

    def _register_context_actions(self) -> None:
        """Register all actions supplied through the context."""

        for spec in tuple(
            self._context.actions
        ):
            self.add_action(
                spec
            )

    def add_action(
        self,
        spec: ToolbarActionSpec,
    ) -> QAction:
        """
        Add a toolbar action.

        Action IDs must be unique.
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

        if spec.separator_before:
            self._toolbar.addSeparator()

        action = QAction(
            self
        )

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

        action.setChecked(
            spec.checked
        )

        if spec.tooltip:
            action.setToolTip(
                spec.tooltip
            )
            action.setStatusTip(
                spec.tooltip
            )

        if spec.shortcut:
            action.setShortcut(
                spec.shortcut
            )

        if spec.icon is not None:
            action.setIcon(
                spec.icon
            )

        action.triggered.connect(
            lambda _checked=False,
            action_id=spec.action_id: (
                self._on_action_triggered(
                    action_id
                )
            )
        )

        self._actions[
            spec.action_id
        ] = action

        self._specs[
            spec.action_id
        ] = spec

        self._toolbar.addAction(
            action
        )

        if spec.tool_id:
            self._register_tool_action(
                spec,
                action,
            )

        return action

    def remove_action(
        self,
        action_id: str,
    ) -> Optional[QAction]:
        """Remove a toolbar action."""

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

        if self._toolbar is not None:
            self._toolbar.removeAction(
                action
            )

        if spec and spec.tool_id:
            self._tool_action_ids.pop(
                spec.tool_id,
                None
            )

            button = self._tool_buttons.pop(
                spec.tool_id,
                None
            )

            if (
                button is not None
                and self._tool_group is not None
            ):
                self._tool_group.removeButton(
                    button
                )

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
        """
        Register an action as a tool-selection action.

        Tool actions are mutually exclusive at the presentation layer.
        Actual active-tool authority remains in ToolManager.
        """

        assert spec.tool_id is not None

        if (
            spec.tool_id
            in self._tool_action_ids
        ):
            raise ValueError(
                (
                    f"Tool {spec.tool_id!r} "
                    "already has a toolbar action."
                )
            )

        self._tool_action_ids[
            spec.tool_id
        ] = spec.action_id

        if self._toolbar is None:
            raise RuntimeError(
                "Toolbar has not been initialized."
            )

        button = self._toolbar.widgetForAction(
            action
        )

        if not isinstance(
            button,
            QToolButton,
        ):
            button = QToolButton(
                self._toolbar
            )

            button.setDefaultAction(
                action
            )

            self._toolbar.insertWidget(
                action,
                button,
            )

        button.setCheckable(
            True
        )

        if self._tool_group is not None:
            self._tool_group.addButton(
                button
            )

        self._tool_buttons[
            spec.tool_id
        ] = button

        button.setChecked(
            spec.checked
        )

    def _on_tool_button_clicked(
        self,
        button_id: int,
    ) -> None:
        """
        Dispatch a tool-selection request.

        QButtonGroup IDs are assigned from the tool-action mapping.
        """

        button = (
            self._tool_group.button(
                button_id
            )
            if self._tool_group is not None
            else None
        )

        if button is None:
            return

        for tool_id, candidate in (
            self._tool_buttons.items()
        ):
            if candidate is button:
                self.select_tool(
                    tool_id
                )
                return

    def select_tool(
        self,
        tool_id: str,
    ) -> None:
        """
        Request activation of a tool.

        ToolbarPlugin does not directly manipulate tool state.
        """

        if not isinstance(
            tool_id,
            str,
        ) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        self._dispatch_tool_selection(
            tool_id
        )

        self.tool_selected.emit(
            tool_id
        )

    # ========================================================
    # ORDINARY ACTIONS
    # ========================================================

    def trigger_action(
        self,
        action_id: str,
    ) -> None:
        """Programmatically trigger a registered action."""

        action = self._actions.get(
            action_id
        )

        if action is None:
            raise KeyError(
                f"Unknown toolbar action: "
                f"{action_id!r}"
            )

        action.trigger()

    def action(
        self,
        action_id: str,
    ) -> Optional[QAction]:
        """Return a registered QAction."""

        return self._actions.get(
            action_id
        )

    def set_action_enabled(
        self,
        action_id: str,
        enabled: bool,
    ) -> None:
        """Change presentation enabled state."""

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be bool."
            )

        action = self._actions.get(
            action_id
        )

        if action is None:
            raise KeyError(
                f"Unknown toolbar action: "
                f"{action_id!r}"
            )

        action.setEnabled(
            enabled
        )

    def set_action_checked(
        self,
        action_id: str,
        checked: bool,
    ) -> None:
        """Change presentation checked state."""

        if not isinstance(
            checked,
            bool,
        ):
            raise TypeError(
                "checked must be bool."
            )

        action = self._actions.get(
            action_id
        )

        if action is None:
            raise KeyError(
                f"Unknown toolbar action: "
                f"{action_id!r}"
            )

        action.setChecked(
            checked
        )

    # ========================================================
    # EVENT HANDLING
    # ========================================================

    def _on_action_triggered(
        self,
        action_id: str,
    ) -> None:
        """Handle a toolbar action activation."""

        spec = self._specs.get(
            action_id
        )

        if spec is None:
            return

        if spec.tool_id:
            self._dispatch_tool_selection(
                spec.tool_id
            )

            self.tool_selected.emit(
                spec.tool_id
            )

        else:
            self._dispatch_action(
                action_id
            )

        self.action_triggered.emit(
            action_id
        )

    # ========================================================
    # SERVICE DISPATCH
    # ========================================================

    def _dispatch_tool_selection(
        self,
        tool_id: str,
    ) -> None:
        """
        Request tool activation through the configured service.

        ToolManager is authoritative for active-tool state.
        """

        manager = (
            self._context.tool_manager
        )

        if manager is not None:
            if self._invoke_optional(
                manager,
                (
                    "activate_tool",
                    "select_tool",
                    "set_active_tool",
                    "activate",
                ),
                tool_id,
            ):
                return

        dispatcher = (
            self._context.dispatcher
        )

        if dispatcher is not None:
            if self._invoke_optional(
                dispatcher,
                (
                    "dispatch_tool",
                    "dispatch_tool_selection",
                    "select_tool",
                ),
                tool_id,
            ):
                return

    def _dispatch_action(
        self,
        action_id: str,
    ) -> None:
        """Dispatch an ordinary application action."""

        action_manager = (
            self._context.action_manager
        )

        if action_manager is not None:
            if self._invoke_optional(
                action_manager,
                (
                    "trigger",
                    "dispatch",
                    "execute",
                ),
                action_id,
            ):
                return

        dispatcher = (
            self._context.dispatcher
        )

        if dispatcher is not None:
            self._invoke_optional(
                dispatcher,
                (
                    "dispatch",
                    "dispatch_action",
                    "trigger",
                ),
                action_id,
            )

    # ========================================================
    # SERVICE WIRING
    # ========================================================

    def _wire_services(self) -> None:
        """Attach the toolbar to compatible services."""

        manager = (
            self._context.tool_manager
        )

        if manager is not None:
            self._invoke_optional(
                manager,
                (
                    "set_toolbar",
                    "set_tool_bar",
                    "attach_toolbar",
                ),
                self._toolbar,
            )

            self._connect_tool_manager(
                manager
            )

        action_manager = (
            self._context.action_manager
        )

        if action_manager is not None:
            self._invoke_optional(
                action_manager,
                (
                    "set_toolbar",
                    "attach_toolbar",
                ),
                self._toolbar,
            )

    def _disconnect_services(self) -> None:
        """Disconnect service references."""

        manager = (
            self._context.tool_manager
        )

        if manager is not None:
            self._invoke_optional(
                manager,
                (
                    "detach_toolbar",
                    "clear_toolbar",
                ),
                self._toolbar,
            )

        action_manager = (
            self._context.action_manager
        )

        if action_manager is not None:
            self._invoke_optional(
                action_manager,
                (
                    "detach_toolbar",
                    "clear_toolbar",
                ),
                self._toolbar,
            )

        self._tool_manager_connected = False

    def _connect_tool_manager(
        self,
        manager: Any,
    ) -> None:
        """
        Connect to optional ToolManager signals.

        This is deliberately capability-based because the tool manager
        is an application service rather than a Qt dependency.
        """

        if self._tool_manager_connected:
            return

        signal = getattr(
            manager,
            "tool_changed",
            None,
        )

        if signal is None:
            signal = getattr(
                manager,
                "active_tool_changed",
                None,
            )

        if signal is None:
            return

        connect = getattr(
            signal,
            "connect",
            None,
        )

        if not callable(connect):
            return

        connect(
            self._on_external_tool_changed
        )

        self._tool_manager_connected = True

    def _on_external_tool_changed(
        self,
        tool_id: Any,
    ) -> None:
        """
        Synchronize toolbar presentation with external tool state.

        The toolbar only reflects state; ToolManager remains
        authoritative.
        """

        if tool_id is None:
            return

        tool_id = str(
            tool_id
        )

        action_id = (
            self._tool_action_ids.get(
                tool_id
            )
        )

        if action_id is None:
            return

        action = self._actions.get(
            action_id
        )

        if action is None:
            return

        action.setChecked(
            True
        )

        button = self._tool_buttons.get(
            tool_id
        )

        if button is not None:
            button.setChecked(
                True
            )

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
        """Return whether a toolbar action represents a tool."""

        return tool_id in self._tool_action_ids

    def tool_action(
        self,
        tool_id: str,
    ) -> Optional[QAction]:
        """Return the QAction associated with a tool."""

        action_id = (
            self._tool_action_ids.get(
                tool_id
            )
        )

        if action_id is None:
            return None

        return self._actions.get(
            action_id
        )

    # ========================================================
    # INTERNAL HELPER
    # ========================================================

    @staticmethod
    def _invoke_optional(
        target: Any,
        method_names: tuple[str, ...],
        *args: Any,
    ) -> bool:
        """
        Invoke the first compatible service method.

        Exceptions from an existing method are intentionally allowed
        to propagate because they indicate an integration defect.
        """

        for method_name in method_names:
            method = getattr(
                target,
                method_name,
                None,
            )

            if callable(method):
                method(*args)
                return True

        return False


# ============================================================
# DEFAULT TOOLBAR SPECIFICATIONS
# ============================================================


def default_tool_actions() -> tuple[
    ToolbarActionSpec,
    ...
]:
    """
    Return the canonical three GridForge tool actions.

    This function intentionally exposes exactly:
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
    context: Optional[
        ToolbarPluginContext
    ] = None,
    parent: Optional[QObject] = None,
) -> ToolbarPlugin:
    """Create an uninitialized ToolbarPlugin."""

    return ToolbarPlugin(
        context=context,
        parent=parent,
    )


__all__ = [
    "ToolbarActionSpec",
    "ToolbarPluginContext",
    "ToolbarPlugin",
    "default_tool_actions",
    "create_toolbar_plugin",
]
