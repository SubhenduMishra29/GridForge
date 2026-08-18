"""
GridForge V2
============

File:
    ui/plugins/shell_plugin.py

Purpose
-------
Composition plugin responsible for assembling the already-created GridForge
UI plugins into the application's root widget.

Architectural role
------------------
ShellPlugin is the final UI composition boundary.

It:
    - receives the shared PluginContext;
    - obtains already-initialized composition plugins;
    - creates the root layout;
    - attaches their existing widgets to that layout;
    - establishes the visible Qt widget hierarchy.

It does NOT:
    - construct concrete plugins;
    - construct GraphicsView;
    - construct panels, toolbar, or status widgets;
    - own Core/domain state;
    - perform electrical calculations;
    - implement canvas interaction;
    - create tools;
    - create renderers;
    - own plugin lifecycle state;
    - modify plugin lifecycle state;
    - duplicate plugin state.

Lifecycle ownership
-------------------
PluginManager decides:
    WHAT should happen
    WHEN it should happen
    IN WHICH dependency order it should happen

ShellPlugin performs:
    UI assembly only.

The shell must initialize after the concrete composition plugins because
their widgets must already exist before they can be inserted into the root
layout.

Qt boundary
-----------
All Qt imports pass through:

    ui.core.qt
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QLayout,
    QVBoxLayout,
    QWidget,
)

from ui.plugins.plugin_context import PluginContext


# ============================================================
# SHELL PLUGIN
# ============================================================


class ShellPlugin:
    """
    Final UI composition plugin for the GridForge application shell.

    ShellPlugin does not create concrete UI components. It only assembles
    components produced by the other composition plugins.

    Expected plugin context
    -----------------------
    The shared PluginContext must provide:

        root_widget
            The neutral QWidget owned by MainWindow.

        plugin_manager
            The PluginManager used to retrieve initialized composition
            plugins.

    The plugin manager is accessed only as composition infrastructure.
    ShellPlugin does not perform lifecycle orchestration.
    """

    plugin_id = "shell"
    plugin_name = "Shell"
    plugin_version = "1.0"
    plugin_description = (
        "Final GridForge UI composition shell."
    )

    plugin_dependencies: tuple[str, ...] = (
        "canvas",
        "panels",
        "toolbar",
        "status",
    )

    plugin_optional = False

    def __init__(self) -> None:
        """
        Construct an uninitialized ShellPlugin.

        No application services or widgets are constructed here.
        """

        self._context: Optional[PluginContext] = None
        self._root_widget: Optional[QWidget] = None
        self._layout: Optional[QLayout] = None
        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> Optional[PluginContext]:
        """Return the current shell context."""

        return self._context

    @property
    def root_widget(self) -> Optional[QWidget]:
        """Return the application root composition widget."""

        return self._root_widget

    @property
    def layout(self) -> Optional[QLayout]:
        """Return the layout created by ShellPlugin."""

        return self._layout

    @property
    def initialized(self) -> bool:
        """Return whether the shell has been initialized."""

        return self._initialized

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Any,
    ) -> QWidget:
        """
        Assemble the existing UI plugin widgets.

        Initialization is idempotent.

        The concrete plugins must already have been initialized by
        PluginManager before ShellPlugin is initialized.
        """

        if self._initialized:
            if self._root_widget is None:
                raise RuntimeError(
                    "ShellPlugin is initialized without a root widget."
                )

            return self._root_widget

        self._validate_context(context)

        self._context = context
        self._root_widget = self._resolve_root_widget()

        self._create_layout()
        self._compose_widgets()

        self._initialized = True

        if self._root_widget is None:
            raise RuntimeError(
                "ShellPlugin initialization produced no root widget."
            )

        return self._root_widget

    def shutdown(self) -> None:
        """
        Release the shell's composition references.

        ShellPlugin does not destroy the child widgets. Their lifetime
        remains governed by Qt ownership and their respective plugins.
        """

        if not self._initialized:
            return

        self._layout = None
        self._root_widget = None
        self._context = None
        self._initialized = False

    # ========================================================
    # CONTEXT
    # ========================================================

    @staticmethod
    def _validate_context(
        context: Any,
    ) -> None:
        """Validate the shared PluginContext."""

        if not isinstance(
            context,
            PluginContext,
        ):
            raise TypeError(
                (
                    "ShellPlugin.initialize() requires "
                    "PluginContext."
                )
            )

        if context.root_widget is None:
            raise RuntimeError(
                "ShellPlugin requires a root_widget."
            )

        if context.plugin_manager is None:
            raise RuntimeError(
                "ShellPlugin requires a plugin_manager."
            )

    def _resolve_root_widget(self) -> QWidget:
        """Resolve the neutral root widget from PluginContext."""

        if self._context is None:
            raise RuntimeError(
                "ShellPlugin context is unavailable."
            )

        root_widget = self._context.root_widget

        if not isinstance(
            root_widget,
            QWidget,
        ):
            raise TypeError(
                "PluginContext.root_widget must be QWidget."
            )

        return root_widget

    # ========================================================
    # LAYOUT
    # ========================================================

    def _create_layout(self) -> None:
        """
        Create the root application layout.

        ShellPlugin owns this layout because it owns the composition
        relationship between the root widget and plugin widgets.
        """

        if self._root_widget is None:
            raise RuntimeError(
                "ShellPlugin root widget is unavailable."
            )

        existing_layout = self._root_widget.layout()

        if existing_layout is not None:
            self._layout = existing_layout
            return

        layout = QVBoxLayout(
            self._root_widget
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self._layout = layout

    # ========================================================
    # COMPOSITION
    # ========================================================

    def _compose_widgets(self) -> None:
        """
        Attach existing plugin widgets to the root layout.

        No concrete plugin is constructed here.

        The PluginManager has already loaded and initialized the
        dependencies before ShellPlugin is reached.
        """

        if self._context is None:
            raise RuntimeError(
                "ShellPlugin context is unavailable."
            )

        if self._layout is None:
            raise RuntimeError(
                "ShellPlugin layout has not been created."
            )

        manager = self._context.plugin_manager

        if manager is None:
            raise RuntimeError(
                "ShellPlugin requires a plugin_manager."
            )

        # ----------------------------------------------------
        # Canvas
        # ----------------------------------------------------

        canvas_plugin = manager.get(
            "canvas"
        )

        if canvas_plugin is None:
            raise RuntimeError(
                "Canvas plugin is unavailable."
            )

        canvas_widget = getattr(
            canvas_plugin,
            "widget",
            None,
        )

        if not isinstance(
            canvas_widget,
            QWidget,
        ):
            raise RuntimeError(
                "Canvas plugin does not expose a valid widget."
            )

        # ----------------------------------------------------
        # Panels
        # ----------------------------------------------------

        panels_plugin = manager.get(
            "panels"
        )

        if panels_plugin is None:
            raise RuntimeError(
                "Panels plugin is unavailable."
            )

        panels_widget = getattr(
            panels_plugin,
            "widget",
            None,
        )

        if panels_widget is not None and not isinstance(
            panels_widget,
            QWidget,
        ):
            raise RuntimeError(
                "Panels plugin exposes an invalid widget."
            )

        # ----------------------------------------------------
        # Toolbar
        # ----------------------------------------------------

        toolbar_plugin = manager.get(
            "toolbar"
        )

        if toolbar_plugin is None:
            raise RuntimeError(
                "Toolbar plugin is unavailable."
            )

        toolbar_widget = getattr(
            toolbar_plugin,
            "widget",
            None,
        )

        if toolbar_widget is not None and not isinstance(
            toolbar_widget,
            QWidget,
        ):
            raise RuntimeError(
                "Toolbar plugin exposes an invalid widget."
            )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status_plugin = manager.get(
            "status"
        )

        if status_plugin is None:
            raise RuntimeError(
                "Status plugin is unavailable."
            )

        status_widget = getattr(
            status_plugin,
            "widget",
            None,
        )

        if status_widget is not None and not isinstance(
            status_widget,
            QWidget,
        ):
            raise RuntimeError(
                "Status plugin exposes an invalid widget."
            )

        # ----------------------------------------------------
        # Current composition contract
        # ----------------------------------------------------
        #
        # The canvas is the central content widget.
        #
        # Panels / toolbar / status plugins may expose widgets
        # that are composed by their own integration boundary.
        #
        # The immediate mandatory composition invariant is that
        # the authoritative CanvasPlugin widget is inserted into
        # the root layout.
        # ----------------------------------------------------

        self._add_widget_once(
            canvas_widget
        )

    # ========================================================
    # LAYOUT HELPERS
    # ========================================================

    def _add_widget_once(
        self,
        widget: QWidget,
    ) -> None:
        """Add a widget to the shell layout exactly once."""

        if self._layout is None:
            raise RuntimeError(
                "ShellPlugin layout is unavailable."
            )

        if widget is None:
            raise ValueError(
                "Cannot add a None widget to the shell."
            )

        if self._layout.indexOf(
            widget
        ) >= 0:
            return

        self._layout.addWidget(
            widget
        )

    # ========================================================
    # ACCESS
    # ========================================================

    def require_root_widget(self) -> QWidget:
        """Return the initialized root widget."""

        if self._root_widget is None:
            raise RuntimeError(
                "ShellPlugin has not been initialized."
            )

        return self._root_widget

    def require_layout(self) -> QLayout:
        """Return the initialized shell layout."""

        if self._layout is None:
            raise RuntimeError(
                "ShellPlugin has not been initialized."
            )

        return self._layout

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def shell_available(self) -> bool:
        """Return whether the shell has a root widget."""

        return self._root_widget is not None

    def layout_available(self) -> bool:
        """Return whether the shell has a layout."""

        return self._layout is not None


# ============================================================
# FACTORY
# ============================================================


def create_shell_plugin() -> ShellPlugin:
    """
    Create an uninitialized ShellPlugin.

    No widgets or application services are constructed here.
    """

    return ShellPlugin()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ShellPlugin",
    "create_shell_plugin",
]
