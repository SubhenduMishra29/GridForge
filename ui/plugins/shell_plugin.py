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
    QHBoxLayout,
    QLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
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
        self._header_widget: Optional[QWidget] = None
        self._engineering_context_store: Any = None
        self._engineering_context_label: Optional[QLabel] = None

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
        header_widget: QWidget | None = None,
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

        if header_widget is not None:
            self._validate_widget(header_widget, "header_widget")

        self._canvas_widget = canvas_widget
        self._toolbar_widget = toolbar_widget
        self._status_widget = status_widget
        self._header_widget = header_widget

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

        previous_context = self._context
        previous_root = self._root_widget
        previous_layout = self._layout
        previous_header = self._header_widget
        previous_initialized = self._initialized
        root = context.root_widget
        existing_layout = root.layout()
        previous_items = (
            tuple(
                existing_layout.itemAt(index).widget()
                for index in range(existing_layout.count())
            )
            if existing_layout is not None
            else ()
        )

        try:
            self._context = context
            self._root_widget = self._resolve_root_widget()
            if self._header_widget is None:
                self.create_header_widget()
            self._create_layout()
            self._compose_widgets()
            self._initialized = True
            return self._root_widget
        except BaseException as exc:
            compensation_error = None
            try:
                self._compensate_initialization(
                    root=root,
                    existing_layout=existing_layout,
                    previous_items=previous_items,
                    created_layout=existing_layout is None,
                )
            except BaseException as cleanup_exc:
                compensation_error = cleanup_exc
            self._context = previous_context
            self._root_widget = previous_root
            self._layout = previous_layout
            self._header_widget = previous_header
            self._initialized = previous_initialized
            if compensation_error is not None:
                raise ExceptionGroup(
                    "ShellPlugin initialization and composition compensation failed.",
                    [exc, compensation_error],
                ) from exc
            raise

    def _compensate_initialization(
        self,
        *,
        root: QWidget,
        existing_layout: Optional[QLayout],
        previous_items: tuple[Optional[QWidget], ...],
        created_layout: bool,
    ) -> None:
        """Restore shell-owned layout composition after failed initialization."""
        layout = self._layout
        if layout is None:
            return
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget not in previous_items:
                widget.setParent(None)
        if created_layout and layout is not existing_layout:
            layout.deleteLater()

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
        self._header_widget = None

        if self._engineering_context_store is not None and callable(getattr(self._engineering_context_store, "unsubscribe", None)):
            self._engineering_context_store.unsubscribe(self._refresh_engineering_context_label)
        self._engineering_context_store = None
        self._engineering_context_label = None
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
        # Application header
        # ----------------------------------------------------

        if self._header_widget is not None:
            self._add_widget_once(self._header_widget)

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
    # HEADER
    # ========================================================

    def create_header_widget(self) -> QWidget:
        """Create the presentation-only application header from shared context."""
        if self._context is None:
            raise RuntimeError("ShellPlugin context is unavailable.")
        if self._header_widget is not None:
            return self._header_widget

        header = QWidget(self._root_widget)
        header.setObjectName("GridForgeApplicationHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 6, 10, 6)

        brand = QLabel("GridForge V2", header)
        brand.setObjectName("GridForgeBrand")
        layout.addWidget(brand)

        context_store = self._context.metadata.get("engineering_context_store") if self._context is not None else None
        self._engineering_context_store = context_store
        if context_store is not None and callable(getattr(context_store, "subscribe", None)):
            context_store.subscribe(self._refresh_engineering_context_label)

        project_context = getattr(self._context.application, "project_lifecycle", None)
        project_context = getattr(project_context, "context", None)
        project_name = getattr(project_context, "name", None) or "No Project"
        project_label = QLabel(f"Project: {project_name}", header)
        project_label.setObjectName("GridForgeProjectContext")
        layout.addWidget(project_label)

        context_label = QLabel(self._format_engineering_context(), header)
        context_label.setObjectName("GridForgeEngineeringContext")
        self._engineering_context_label = context_label
        layout.addWidget(context_label)
        layout.addStretch(1)

        search = QLineEdit(header)
        search.setPlaceholderText("Search project elements…")
        search.setObjectName("GridForgeProjectSearch")
        search.setClearButtonEnabled(True)
        layout.addWidget(search)

        notifications = QPushButton("Notifications", header)
        notifications.setObjectName("GridForgeNotifications")
        notifications.clicked.connect(
            lambda: QMessageBox.information(
                header,
                "Notifications",
                self._notification_text(),
            )
        )
        layout.addWidget(notifications)

        help_button = QPushButton("Help", header)
        help_button.setObjectName("GridForgeHelp")
        help_button.clicked.connect(
            lambda: QMessageBox.information(
                header,
                "GridForge Help",
                "Use the Equipment Library to select an engineering tool, "
                "place equipment on the SLD, then inspect and commit engineering data.",
            )
        )
        layout.addWidget(help_button)

        user_context = getattr(self._context.application, "user_context", None)
        role = getattr(user_context, "role", None) or "Engineer"
        user_label = QLabel(f"User / Role: {role}", header)
        user_label.setObjectName("GridForgeUserContext")
        layout.addWidget(user_label)

        search.returnPressed.connect(lambda: self._search_project(search.text(), header))
        self._header_widget = header
        return header

    def _format_engineering_context(self) -> str:
        context = getattr(self._engineering_context_store, "current", None)
        if context is None:
            return "Engineering: SLD"
        discipline = str(getattr(context, "discipline", "sld")).upper()
        study = getattr(context, "study_id", None) or "No Study"
        state = getattr(context, "system_state", None) or "Normal"
        return f"Engineering: {discipline} · Study: {study} · State: {state}"

    def _refresh_engineering_context_label(self, _context: Any) -> None:
        if self._engineering_context_label is not None:
            self._engineering_context_label.setText(self._format_engineering_context())

    def _search_project(self, query: str, parent: QWidget) -> None:
        """Search canonical Application read models without mutating state."""
        query = str(query).strip().lower()
        if not query:
            return
        application = self._context.application if self._context is not None else None
        if application is None or not callable(getattr(application, "read_network", None)):
            QMessageBox.information(parent, "Project Search", "Project read access is unavailable.")
            return
        matches = [
            element for element in application.read_network().elements
            if query in str(element.object_id).lower()
            or query in str(element.element_type).lower()
            or query in " ".join(str(value).lower() for value in element.labels.values())
        ]
        if not matches:
            QMessageBox.information(parent, "Project Search", f"No project element matches {query!r}.")
            return

        # Search is read-only, but selecting the first canonical match is a
        # real navigation action through the existing transient UI selection
        # authority. The Application/Core model is not mutated.
        router = getattr(self._context, "action_router", None) if self._context is not None else None
        if callable(getattr(router, "dispatch", None)):
            router.dispatch("view.sld_workspace")
        selection_manager = (
            self._context.metadata.get("selection_manager")
            if self._context is not None
            else None
        )
        if callable(getattr(selection_manager, "select_single", None)):
            selection_manager.select_single(matches[0].object_id)

        lines = [f"{item.object_id} — {item.element_type}" for item in matches[:50]]
        suffix = "" if len(matches) <= 50 else f"\\n…and {len(matches) - 50} more"
        QMessageBox.information(
            parent,
            "Project Search",
            "Selected: " + lines[0] + ("\\n\\n" + "\\n".join(lines[1:]) if len(lines) > 1 else ""),
        )

    def _notification_text(self) -> str:
        application = self._context.application if self._context is not None else None
        validation = getattr(application, "read_validation", lambda: None)()
        if validation is None:
            return "No validation notifications are currently published."
        errors = getattr(validation, "errors", ()) or ()
        warnings = getattr(validation, "warnings", ()) or ()
        return f"Validation notifications: {len(errors)} error(s), {len(warnings)} warning(s)."

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
