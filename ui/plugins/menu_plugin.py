# ============================================================
# File: ui/plugins/menu_plugin.py
# GridForge V2 — Application Menu Composition
# Author: Subhendu Mishra
# ============================================================
"""Canonical application menu composition boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ui.core.qt import QAction, QMainWindow, QMenu, QMenuBar, QObject
from ui.core.action_router import UIActionRouter
from ui.plugins.plugin_context import PluginContext


@dataclass(frozen=True, slots=True)
class MenuActionSpec:
    action_id: str
    text: str
    shortcut: str | None = None
    separator_before: bool = False


@dataclass(frozen=True, slots=True)
class MenuSpec:
    menu_id: str
    title: str
    actions: tuple[MenuActionSpec, ...]


class MenuPlugin(QObject):
    """Compose menus and route every action through UIActionRouter."""

    plugin_id = "menu"
    plugin_name = "Menu"
    plugin_version = "1.0"
    plugin_description = "Canonical GridForge application menu composition."
    plugin_dependencies: tuple[str, ...] = ()
    plugin_optional = False

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._context: PluginContext | None = None
        self._menu_bar: QMenuBar | None = None
        self._menus: dict[str, QMenu] = {}
        self._actions: dict[str, QAction] = {}
        self._initialized = False

    @property
    def menu_bar(self) -> QMenuBar | None:
        return self._menu_bar

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self, context: PluginContext) -> QMenuBar:
        if not isinstance(context, PluginContext):
            raise TypeError("MenuPlugin requires PluginContext.")
        if self._initialized:
            if self._context is not context:
                raise RuntimeError("MenuPlugin is already initialized with a different PluginContext.")
            return self._require_menu_bar()

        main_window = context.main_window
        router = context.action_router
        if not isinstance(main_window, QMainWindow):
            raise TypeError("PluginContext.main_window must be QMainWindow for MenuPlugin.")
        if not isinstance(router, UIActionRouter):
            raise TypeError("MenuPlugin requires PluginContext.action_router.")

        menu_bar = QMenuBar(main_window)
        menu_bar.setObjectName("GridForgeMenuBar")
        main_window.setMenuBar(menu_bar)
        self._context = context
        self._menu_bar = menu_bar
        try:
            for spec in default_menus():
                menu = menu_bar.addMenu(spec.title)
                menu.setObjectName(f"menu.{spec.menu_id}")
                self._menus[spec.menu_id] = menu
                for action_spec in spec.actions:
                    router.require(action_spec.action_id)
                    if action_spec.separator_before:
                        menu.addSeparator()
                    action = QAction(action_spec.text, self)
                    action.setObjectName(action_spec.action_id)
                    action.setEnabled(router.is_enabled(action_spec.action_id))
                    if action_spec.shortcut:
                        action.setShortcut(action_spec.shortcut)
                    action.triggered.connect(lambda _checked=False, action_id=action_spec.action_id: router.dispatch(action_id))
                    menu.addAction(action)
                    self._actions[action_spec.action_id] = action
            self._initialized = True
            return menu_bar
        except Exception:
            self.shutdown()
            raise

    def shutdown(self) -> None:
        if self._menu_bar is not None:
            self._menu_bar.clear()
            self._menu_bar.deleteLater()
        self._actions.clear()
        self._menus.clear()
        self._menu_bar = None
        self._context = None
        self._initialized = False

    def refresh_enabled_states(self) -> None:
        if self._context is None:
            return
        router = self._context.action_router
        for action_id, action in tuple(self._actions.items()):
            action.setEnabled(router.is_enabled(action_id))

    def action(self, action_id: str) -> QAction | None:
        return self._actions.get(action_id)

    def _require_menu_bar(self) -> QMenuBar:
        if self._menu_bar is None:
            raise RuntimeError("MenuPlugin is initialized without a menu bar.")
        return self._menu_bar


def default_menus() -> tuple[MenuSpec, ...]:
    """Return the canonical, non-duplicated application menu taxonomy."""
    def a(action_id: str, text: str, shortcut: str | None = None, separator_before: bool = False) -> MenuActionSpec:
        return MenuActionSpec(action_id, text, shortcut, separator_before)

    return (
        MenuSpec("file", "File", (
            a("project.new", "New Project", "Ctrl+N"),
            a("project.open", "Open Project…", "Ctrl+O"),
            a("project.save", "Save Project", "Ctrl+S"),
            a("project.save_as", "Save Project As…", "Ctrl+Shift+S"),
            a("project.close", "Close Project", "Ctrl+W", True),
            a("application.exit", "Exit", "Alt+F4", True),
        )),
        MenuSpec("edit", "Edit", (
            a("edit.undo", "Undo", "Ctrl+Z"),
            a("edit.redo", "Redo", "Ctrl+Y"),
            a("edit.delete_selection", "Delete Selection", "Delete", True),
            a("edit.select_all", "Select All", "Ctrl+A"),
            a("edit.copy", "Copy", "Ctrl+C"),
            a("edit.paste", "Paste", "Ctrl+V"),
            a("edit.cut", "Cut", "Ctrl+X"),
        )),
        MenuSpec("view", "View", (
            a("view.fit", "Fit SLD View"),
            a("view.zoom_in", "Zoom In"),
            a("view.zoom_out", "Zoom Out"),
            a("view.pan", "Pan"),
        )),
        MenuSpec("project", "Project", (
            a("network.commit_draft", "Commit Network", "Ctrl+Shift+Enter"),
        )),
        MenuSpec("engineering", "Engineering", (
            a("view.sld_workspace", "SLD"),
            a("view.control_workspace", "Control"),
            a("view.protection_workspace", "Protection"),
            a("view.topology", "Topology"),
            a("view.map", "Map"),
            a("view.reports", "Reports"),
            a("view.equipment_browser", "Equipment Browser", None, True),
        )),
        MenuSpec("study", "Study", (
            a("study.cases", "Study Cases"),
        )),
        MenuSpec("tools", "Tools", (
            a("tool.select", "Select"),
            a("tool.bus", "Bus"),
            a("tool.wire", "Simple Wired Connection"),
        )),
        MenuSpec("window", "Window", ()),
        MenuSpec("help", "Help", (
            a("help.about", "About GridForge"),
        )),
    )


def create_menu_plugin(parent: Optional[QObject] = None) -> MenuPlugin:
    return MenuPlugin(parent=parent)


__all__ = ["MenuActionSpec", "MenuPlugin", "MenuSpec", "create_menu_plugin", "default_menus"]
