"""
GridForge V2
============

File:
    ui/plugins/shell_plugin.py

Purpose
-------
Final UI composition plugin responsible for assembling already-created
GridForge UI widgets into the MainWindow root composition widget.

Architectural role
------------------
ShellPlugin is the final presentation/composition boundary.

It:
    - receives PluginContext;
    - receives already-created widgets through an explicit composition API;
    - creates/reuses the root layout;
    - attaches existing widgets;
    - establishes the visible Qt widget hierarchy.

It does NOT:
    - discover plugins;
    - resolve plugin dependencies;
    - access PluginManager;
    - access PluginRegistry;
    - initialize other plugins;
    - shut down other plugins;
    - construct CanvasPlugin;
    - construct ToolbarPlugin;
    - construct StatusPlugin;
    - construct PanelsPlugin;
    - construct GraphicsView;
    - construct tools;
    - construct renderers;
    - own Core/domain state;
    - perform electrical calculations;
    - manage plugin lifecycle.

Dependency ownership
--------------------
PluginManager owns:

    plugin discovery
    dependency resolution
    loading
    initialization order
    shutdown order

ShellPlugin owns only:

    root layout
    widget composition
    visible UI hierarchy

Composition contract
--------------------
The composition layer supplies the already-created widgets:

    canvas_widget
    toolbar_widget
    status_widget

Panels remain independently owned by PanelsPlugin and are not blindly
inserted into the central vertical layout because their presentation
boundary may be dock/workspace based.

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
    Final GridForge UI composition plugin.

    ShellPlugin consumes already-created widgets. It never resolves
    those widgets through PluginManager or PluginRegistry.
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

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Construct an uninitialized ShellPlugin.

        No Qt widgets are created here.
        """

        self._context: Optional[PluginContext] = None

        self._root_widget: Optional[QWidget] = None
        self._layout: Optional[QLayout] = None

        self._canvas_widget: Optional[QWidget] = None
        self._toolbar_widget: Optional[QWidget] = None
        self._status_widget: Optional[QWidget] = None

        self._initialized = False

        self._composition_bound = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(
        self,
    ) -> Optional[PluginContext]:
        """Return the current shell context."""

        return self._context

    @property
    def root_widget(
        self,
    ) -> Optional[QWidget]:
        """Return the root application composition widget."""

        return self._root_widget

    @property
    def layout(
        self,
    ) -> Optional[QLayout]:
        """Return the shell layout."""

        return self._layout

    @property
    def canvas_widget(
        self,
    ) -> Optional[QWidget]:
        """Return the composed canvas widget."""

        return self._canvas_widget

    @property
    def toolbar_widget(
        self,
    ) -> Optional[QWidget]:
        """Return the composed toolbar widget."""

        return self._toolbar_widget

    @property
    def status_widget(
        self,
    ) -> Optional[QWidget]:
        """Return the composed status widget."""

        return self._status_widget

    @property
    def initialized(
        self,
    ) -> bool:
        """Return whether the shell has been initialized."""

        return self._initialized

    @property
    def composition_bound(
        self,
    ) -> bool:
        """Return whether all required composition widgets are bound."""

        return self._composition_bound

    # ========================================================
    # COMPOSITION BINDING
    # ========================================================

    def set_composition(
        self,
        *,
        canvas_widget: QWidget,
        toolbar_widget: QWidget,
        status_widget: QWidget,
    ) -> None:
        """
        Bind the already-created composition widgets.

        This method deliberately accepts widgets rather than plugins.

        That prevents ShellPlugin from depending on PluginManager,
        PluginRegistry, or plugin discovery.

        Parameters
        ----------
        canvas_widget:
            Existing canvas widget created by CanvasPlugin.

        toolbar_widget:
            Existing toolbar widget created by ToolbarPlugin.

        status_widget:
            Existing status widget created by StatusPlugin.
        """

        if self._initialized:
            raise RuntimeError(
                "Cannot change ShellPlugin composition after initialization."
            )

        self._validate_widget(
            canvas_widget,
            "canvas_widget",
        )

        self._validate_widget(
            toolbar_widget,
            "toolbar_widget",
        )

        self._validate_widget(
            status_widget,
            "status_widget",
        )

        self._canvas_widget = canvas_widget
        self._toolbar_widget = toolbar_widget
        self._status_widget = status_widget

        self._composition_bound = True

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Any,
    ) -> QWidget:
        """
        Initialize the shell and assemble the supplied widgets.

        PluginManager is responsible for ensuring that the dependency
        plugins have already been initialized.

        ShellPlugin does not query PluginManager to verify that state.
        """

        if self._initialized:
            if self._root_widget is None:
                raise RuntimeError(
                    "ShellPlugin is initialized without a root widget."
                )

            return self._root_widget

        self._validate_context(
            context
        )

        if not self._composition_bound:
            raise RuntimeError(
                (
                    "ShellPlugin requires composition widgets before "
                    "initialization. Call set_composition() first."
                )
            )

        self._context = context

        self._root_widget = self._resolve_root_widget()

        self._create_layout()

        self._compose_widgets()

        self._initialized = True

        return self._root_widget

    # ========================================================

    def shutdown(
        self,
    ) -> None:
        """
        Release shell-owned composition references.

        Child widgets remain owned by their respective plugins/Qt.
        """

        if not self._initialized:
            return

        self._layout = None
        self._root_widget = None

        self._context = None

        self._initialized = False

    # ========================================================
    # CONTEXT VALIDATION
    # ========================================================

    @staticmethod
    def _validate_context(
        context: Any,
    ) -> None:
        """
        Validate the supplied PluginContext.

        No PluginManager requirement is allowed here.
        """

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

    # ========================================================

    def _resolve_root_widget(
        self,
    ) -> QWidget:
        """Resolve the MainWindow-owned root widget."""

        if self._context is None:
            raise RuntimeError(
                "ShellPlugin context is unavailable."
            )

        root_widget = self._context.root_widget

        self._validate_widget(
            root_widget,
            "PluginContext.root_widget",
        )

        return root_widget

    # ========================================================
    # LAYOUT
    # ========================================================

    def _create_layout(
        self,
    ) -> None:
        """
        Create or reuse the root layout.

        An application-supplied layout is never replaced.
        """

        if self._root_widget is None:
            raise RuntimeError(
                "ShellPlugin root widget is unavailable."
            )

        existing_layout = (
            self._root_widget.layout()
        )

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

    def _compose_widgets(
        self,
    ) -> None:
        """
        Assemble the already-created UI widgets.

        Composition order:

            toolbar
            canvas
            status
        """

        if self._layout is None:
            raise RuntimeError(
                "ShellPlugin layout is unavailable."
            )

        if self._toolbar_widget is None:
            raise RuntimeError(
                "Toolbar widget is unavailable."
            )

        if self._canvas_widget is None:
            raise RuntimeError(
                "Canvas widget is unavailable."
            )

        if self._status_widget is None:
            raise RuntimeError(
                "Status widget is unavailable."
            )

        # ----------------------------------------------------
        # Toolbar
        # ----------------------------------------------------

        self._add_widget_once(
            self._toolbar_widget
        )

        # ----------------------------------------------------
        # Canvas
        #
        # Canvas receives the available vertical space.
        # ----------------------------------------------------

        self._add_widget_once(
            self._canvas_widget,
            stretch=1,
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self._add_widget_once(
            self._status_widget
        )

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
        Add an existing widget exactly once.
        """

        if self._layout is None:
            raise RuntimeError(
                "ShellPlugin layout is unavailable."
            )

        self._validate_widget(
            widget,
            "widget",
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
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_widget(
        widget: Any,
        name: str,
    ) -> None:
        """
        Validate a QWidget dependency.
        """

        if not isinstance(
            widget,
            QWidget,
        ):
            raise TypeError(
                f"{name} must be QWidget."
            )

    # ========================================================
    # ACCESSORS
    # ========================================================

    def require_root_widget(
        self,
    ) -> QWidget:
        """Return the initialized root widget."""

        if self._root_widget is None:
            raise RuntimeError(
                "ShellPlugin has not been initialized."
            )

        return self._root_widget

    # --------------------------------------------------------

    def require_layout(
        self,
    ) -> QLayout:
        """Return the initialized shell layout."""

        if self._layout is None:
            raise RuntimeError(
                "ShellPlugin has not been initialized."
            )

        return self._layout

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def shell_available(
        self,
    ) -> bool:
        """Return whether the shell has a root widget."""

        return self._root_widget is not None

    # --------------------------------------------------------

    def layout_available(
        self,
    ) -> bool:
        """Return whether the shell has a layout."""

        return self._layout is not None


# ============================================================
# FACTORY
# ============================================================


def create_shell_plugin() -> ShellPlugin:
    """
    Create an uninitialized ShellPlugin.

    No Qt widgets or application services are created here.
    """

    return ShellPlugin()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ShellPlugin",
    "create_shell_plugin",
]
