"""
GridForge V2
============

File:
    ui/plugins/shell_plugin.py

Purpose
-------
Final UI composition plugin responsible for assembling the already-created
GridForge composition plugins into the application's root widget.

Architectural role
------------------
ShellPlugin is the final UI composition boundary.

It:
    - receives the shared PluginContext;
    - obtains already-initialized composition plugins;
    - creates the root layout;
    - attaches their existing widgets;
    - establishes the visible Qt widget hierarchy.

It does NOT:
    - discover plugins;
    - load plugins;
    - construct plugins;
    - initialize plugins;
    - shut down plugins;
    - construct GraphicsView;
    - construct panels, toolbar, or status widgets;
    - own Core/domain state;
    - perform electrical calculations;
    - implement canvas interaction;
    - create tools;
    - create renderers;
    - own PluginStateStore;
    - modify plugin lifecycle state;
    - resolve dependencies.

Lifecycle ownership
-------------------
PluginManager decides:

    WHAT should happen
    WHEN it should happen
    IN WHICH dependency order it should happen

PluginRegistry performs:

    register
    initialize
    shutdown
    unregister
    enable
    disable

PluginStateStore records:

    registered
    enabled
    initialized
    generation
    last_error
    metadata

ShellPlugin performs only UI assembly.

Dependency contract
-------------------
ShellPlugin depends on:

    canvas
    panels
    toolbar
    status

Those plugins must already be loaded and initialized before ShellPlugin
is initialized.

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

    ShellPlugin assembles existing widgets. It does not construct or
    initialize the plugins that own those widgets.
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

        No Qt widgets are created here.
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
        """Return the root application composition widget."""

        return self._root_widget

    @property
    def layout(self) -> Optional[QLayout]:
        """Return the shell layout."""

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
        Assemble the existing GridForge UI widgets.

        Initialization is idempotent.

        PluginManager is responsible for ensuring that all declared
        dependencies have already been initialized.
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

        if self._root_widget is None:
            raise RuntimeError(
                "ShellPlugin initialization produced no root widget."
            )

        self._initialized = True

        return self._root_widget

    def shutdown(self) -> None:
        """
        Release shell-owned composition references.

        Child widgets are not explicitly destroyed. Qt ownership and the
        respective plugin remain responsible for widget lifetime.
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
        """Validate the supplied PluginContext."""

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
        """Resolve the root widget from PluginContext."""

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
        Create or reuse the root layout.

        ShellPlugin owns the composition relationship, but does not
        replace an existing layout supplied by the application boundary.
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
        Assemble the already-created plugin widgets.

        No plugin is constructed or initialized here.

        The expected composition is:

            toolbar
            ─────────────────
            canvas
            ─────────────────
            status

        The PanelsPlugin remains responsible for its own panel/workspace
        composition where applicable.
        """

        manager = self._require_plugin_manager()

        self._require_dependencies_initialized(
            manager
        )

        toolbar_widget = self._resolve_required_widget(
            manager,
            "toolbar",
        )

        canvas_widget = self._resolve_required_widget(
            manager,
            "canvas",
        )

        status_widget = self._resolve_required_widget(
            manager,
            "status",
        )

        # Panels are mandatory as a lifecycle dependency, but their
        # widget may be integrated into the canvas/workspace by the
        # PanelsPlugin itself.
        self._resolve_optional_widget(
            manager,
            "panels",
        )

        # ----------------------------------------------------
        # Root composition
        # ----------------------------------------------------

        self._add_widget_once(
            toolbar_widget
        )

        self._add_widget_once(
            canvas_widget,
            stretch=1,
        )

        self._add_widget_once(
            status_widget
        )

    # ========================================================
    # PLUGIN RESOLUTION
    # ========================================================

    def _require_plugin_manager(self) -> Any:
        """Return the PluginManager supplied through the context."""

        if self._context is None:
            raise RuntimeError(
                "ShellPlugin context is unavailable."
            )

        manager = self._context.plugin_manager

        if manager is None:
            raise RuntimeError(
                "ShellPlugin requires a plugin_manager."
            )

        return manager

    def _require_dependencies_initialized(
        self,
        manager: Any,
    ) -> None:
        """
        Verify that all declared shell dependencies are initialized.

        ShellPlugin does not initialize missing dependencies itself.
        """

        for plugin_id in self.plugin_dependencies:
            try:
                registered = manager.is_registered(
                    plugin_id
                )
            except AttributeError as exc:
                raise TypeError(
                    (
                        "ShellPlugin requires a PluginManager "
                        "with is_registered()."
                    )
                ) from exc

            if not registered:
                raise RuntimeError(
                    (
                        f"ShellPlugin dependency "
                        f"{plugin_id!r} is not registered."
                    )
                )

            if not manager.is_initialized(
                plugin_id
            ):
                raise RuntimeError(
                    (
                        f"ShellPlugin dependency "
                        f"{plugin_id!r} is not initialized."
                    )
                )

    @staticmethod
    def _resolve_required_widget(
        manager: Any,
        plugin_id: str,
    ) -> QWidget:
        """
        Resolve a mandatory widget exposed by a composition plugin.
        """

        plugin = manager.get(
            plugin_id
        )

        if plugin is None:
            raise RuntimeError(
                (
                    f"Required plugin "
                    f"{plugin_id!r} is unavailable."
                )
            )

        widget = getattr(
            plugin,
            "widget",
            None,
        )

        if not isinstance(
            widget,
            QWidget,
        ):
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} does not expose "
                    "a valid QWidget."
                )
            )

        return widget

    @staticmethod
    def _resolve_optional_widget(
        manager: Any,
        plugin_id: str,
    ) -> QWidget | None:
        """
        Resolve an optional widget exposed by a mandatory plugin.

        The plugin itself remains mandatory. Its widget is optional because
        the plugin may compose its UI into another workspace boundary.
        """

        plugin = manager.get(
            plugin_id
        )

        if plugin is None:
            raise RuntimeError(
                (
                    f"Required plugin "
                    f"{plugin_id!r} is unavailable."
                )
            )

        widget = getattr(
            plugin,
            "widget",
            None,
        )

        if widget is None:
            return None

        if not isinstance(
            widget,
            QWidget,
        ):
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} exposes "
                    "an invalid widget."
                )
            )

        return widget

    # ========================================================
    # LAYOUT HELPERS
    # ========================================================

    def _add_widget_once(
        self,
        widget: QWidget,
        *,
        stretch: int = 0,
    ) -> None:
        """
        Add an existing widget to the shell layout exactly once.
        """

        if self._layout is None:
            raise RuntimeError(
                "ShellPlugin layout is unavailable."
            )

        if not isinstance(
            widget,
            QWidget,
        ):
            raise TypeError(
                "widget must be QWidget."
            )

        if self._layout.indexOf(
            widget
        ) >= 0:
            return

        self._layout.addWidget(
            widget,
            stretch,
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
