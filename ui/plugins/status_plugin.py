"""
GridForge V2
============

File:
    ui/plugins/status_plugin.py

Purpose
-------
Composition plugin responsible for creating and managing the
application status-bar presentation.

Architectural role
------------------
StatusPlugin is a UI composition plugin.

It:
    - obtains the application's QStatusBar;
    - creates and manages plugin-owned status fields;
    - exposes status presentation components;
    - provides transient status messages;
    - owns only its presentation composition.

It does NOT:
    - own application state;
    - own project/network state;
    - perform electrical calculations;
    - mutate Core directly;
    - construct application services/controllers;
    - access ToolManager directly;
    - create tools;
    - create another status-bar state model;
    - own QMainWindow;
    - own the application's QStatusBar lifetime;
    - perform service discovery.

Lifecycle
--------
    StatusPlugin()
        |
        +--> initialize(context)
        |       obtain QStatusBar
        |       compose status fields
        |
        +--> shutdown()
                remove plugin-owned fields

PluginContext
-------------
PluginContext is supplied exclusively through initialize().

It is never a constructor dependency.

Dependency graph
----------------
Status composition depends on the other primary UI composition
plugins being available:

    canvas
      |
      +--> panels
      |
      +--> toolbar
      |
      +--> status

StatusPlugin does not directly manipulate those plugins. The
dependencies are declared for PluginManager lifecycle ordering.

Ownership
---------
StatusPlugin owns:
    - StatusSpec definitions;
    - plugin-created QLabel instances;
    - status-field presentation;
    - transient status messages;
    - references to the application's QStatusBar.

MainWindow owns:
    - QMainWindow;
    - QStatusBar lifetime;
    - overall application composition.

Core/domain layers remain authoritative for application state.

Qt boundary
-----------
All Qt imports pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ui.core.qt import (
    QLabel,
    QMainWindow,
    QObject,
    QStatusBar,
    Signal,
)

from .plugin_context import PluginContext


# ============================================================
# STATUS SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class StatusSpec:
    """
    Declarative description of one status-bar presentation field.

    StatusSpec contains presentation metadata only.

    It does not own application state and does not reference
    controllers, services, Core objects, or domain models.
    """

    status_id: str

    text: str = ""

    tooltip: Optional[str] = None

    stretch: int = 0

    permanent: bool = False

    visible: bool = True

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        # ----------------------------------------------------
        # status_id
        # ----------------------------------------------------

        if (
            not isinstance(
                self.status_id,
                str,
            )
            or not self.status_id.strip()
        ):
            raise ValueError(
                "status_id must be a non-empty string."
            )

        # ----------------------------------------------------
        # text
        # ----------------------------------------------------

        if not isinstance(
            self.text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        # ----------------------------------------------------
        # stretch
        # ----------------------------------------------------

        if not isinstance(
            self.stretch,
            int,
        ):
            raise TypeError(
                "stretch must be an integer."
            )

        if self.stretch < 0:
            raise ValueError(
                "stretch cannot be negative."
            )

        # ----------------------------------------------------
        # tooltip
        # ----------------------------------------------------

        if (
            self.tooltip is not None
            and not isinstance(
                self.tooltip,
                str,
            )
        ):
            raise TypeError(
                "tooltip must be a string or None."
            )

        # ----------------------------------------------------
        # permanent
        # ----------------------------------------------------

        if not isinstance(
            self.permanent,
            bool,
        ):
            raise TypeError(
                "permanent must be bool."
            )

        # ----------------------------------------------------
        # visible
        # ----------------------------------------------------

        if not isinstance(
            self.visible,
            bool,
        ):
            raise TypeError(
                "visible must be bool."
            )

        # ----------------------------------------------------
        # metadata
        # ----------------------------------------------------

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a Mapping."
            )


# ============================================================
# STATUS PLUGIN
# ============================================================


class StatusPlugin(QObject):
    """
    GridForge status-bar composition plugin.

    The plugin owns status-field composition only.

    The application's QStatusBar remains owned by QMainWindow.
    """

    plugin_id = "status"
    plugin_name = "Status"
    plugin_version = "1.0"
    plugin_description = (
        "GridForge application status-bar composition."
    )

    plugin_dependencies: tuple[str, ...] = (
        "canvas",
        "panels",
        "toolbar",
    )

    plugin_optional = False

    status_changed = Signal(
        str,
        str,
    )

    def __init__(
        self,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Construct an uninitialized StatusPlugin.

        No application context is accepted during construction.

        PluginContext is supplied exclusively through initialize().
        """

        super().__init__(
            parent
        )

        self._context: Optional[
            PluginContext
        ] = None

        self._status_bar: Optional[
            QStatusBar
        ] = None

        self._labels: dict[
            str,
            QLabel,
        ] = {}

        self._specs: dict[
            str,
            StatusSpec,
        ] = {}

        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(
        self,
    ) -> Optional[PluginContext]:
        """
        Return the active PluginContext.

        Returns None before initialization or after shutdown.
        """

        return self._context

    @property
    def status_bar(
        self,
    ) -> Optional[QStatusBar]:
        """
        Return the application's QStatusBar.

        The status bar itself remains owned by QMainWindow.
        """

        return self._status_bar

    @property
    def widget(
        self,
    ) -> Optional[QStatusBar]:
        """
        Return the composed status bar presentation component.
        """

        return self._status_bar

    @property
    def initialized(
        self,
    ) -> bool:
        """Return whether the plugin is initialized."""

        return self._initialized

    @property
    def status_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered status identifiers in registration order.
        """

        return tuple(
            self._labels.keys()
        )

    @property
    def statuses(
        self,
    ) -> tuple[QLabel, ...]:
        """
        Return registered status widgets in registration order.
        """

        return tuple(
            self._labels.values()
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: PluginContext,
    ) -> QStatusBar:
        """
        Initialize status-bar composition.

        PluginContext is the sole application dependency boundary.

        Initialization is idempotent for the same context.
        Reinitialization with a different context is rejected.
        """

        if not isinstance(
            context,
            PluginContext,
        ):
            raise TypeError(
                "StatusPlugin requires PluginContext."
            )

        # ----------------------------------------------------
        # Existing lifecycle
        # ----------------------------------------------------

        if self._initialized:
            if self._context is not context:
                raise RuntimeError(
                    (
                        "StatusPlugin is already initialized "
                        "with a different PluginContext."
                    )
                )

            if self._status_bar is None:
                raise RuntimeError(
                    (
                        "StatusPlugin is initialized without "
                        "a QStatusBar."
                    )
                )

            return self._status_bar

        # ----------------------------------------------------
        # New lifecycle
        # ----------------------------------------------------

        self._context = context

        try:
            self._create_status_bar()

            self._register_default_statuses()

            self._initialized = True

            if self._status_bar is None:
                raise RuntimeError(
                    (
                        "StatusPlugin initialization produced "
                        "no QStatusBar."
                    )
                )

            return self._status_bar

        except Exception:
            self._remove_plugin_statuses()

            self._status_bar = None
            self._context = None
            self._initialized = False

            raise

    def shutdown(
        self,
    ) -> None:
        """
        Shut down status-bar composition.

        The application's QStatusBar is not destroyed.

        Only status fields created by this plugin are removed.
        """

        if not self._initialized:
            return

        self._remove_plugin_statuses()

        self._status_bar = None
        self._context = None
        self._initialized = False

    # ========================================================
    # STATUS BAR COMPOSITION
    # ========================================================

    def _create_status_bar(
        self,
    ) -> None:
        """
        Obtain the application's QStatusBar.

        QMainWindow remains responsible for its lifetime.
        """

        context = self._context

        if context is None:
            raise RuntimeError(
                "StatusPlugin context is unavailable."
            )

        main_window = context.main_window

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                (
                    "PluginContext.main_window must be "
                    "QMainWindow."
                )
            )

        status_bar = main_window.statusBar()

        if not isinstance(
            status_bar,
            QStatusBar,
        ):
            raise TypeError(
                (
                    "QMainWindow.statusBar() did not return "
                    "a QStatusBar."
                )
            )

        self._status_bar = status_bar

    # ========================================================
    # STATUS REGISTRATION
    # ========================================================

    def _register_default_statuses(
        self,
    ) -> None:
        """
        Register the canonical GridForge baseline status fields.
        """

        for spec in default_statuses():
            self.add_status(
                spec
            )

    def add_status(
        self,
        spec: StatusSpec,
    ) -> QLabel:
        """
        Add one plugin-owned presentation field.

        The plugin must already be initialized.
        """

        self._require_initialized()

        if not isinstance(
            spec,
            StatusSpec,
        ):
            raise TypeError(
                "spec must be StatusSpec."
            )

        if spec.status_id in self._labels:
            raise ValueError(
                (
                    f"Status {spec.status_id!r} "
                    "is already registered."
                )
            )

        status_bar = self._status_bar

        if status_bar is None:
            raise RuntimeError(
                "StatusPlugin has no QStatusBar."
            )

        label = QLabel(
            spec.text,
            status_bar,
        )

        label.setObjectName(
            f"gridforge_status_{spec.status_id}"
        )

        if spec.tooltip is not None:
            label.setToolTip(
                spec.tooltip
            )

        label.setVisible(
            spec.visible
        )

        if spec.permanent:
            status_bar.addPermanentWidget(
                label,
                spec.stretch,
            )
        else:
            status_bar.addWidget(
                label,
                spec.stretch,
            )

        self._labels[
            spec.status_id
        ] = label

        self._specs[
            spec.status_id
        ] = spec

        return label

    def remove_status(
        self,
        status_id: str,
    ) -> Optional[QLabel]:
        """
        Remove one plugin-owned presentation field.
        """

        self._validate_status_id(
            status_id
        )

        label = self._labels.pop(
            status_id,
            None,
        )

        self._specs.pop(
            status_id,
            None,
        )

        if label is None:
            return None

        status_bar = self._status_bar

        if status_bar is not None:
            status_bar.removeWidget(
                label
            )

        label.deleteLater()

        return label

    def _remove_plugin_statuses(
        self,
    ) -> None:
        """
        Remove every status field composed by this plugin.
        """

        for status_id in tuple(
            self._labels.keys()
        ):
            self.remove_status(
                status_id
            )

        self._labels.clear()
        self._specs.clear()

    # ========================================================
    # STATUS ACCESS
    # ========================================================

    def status(
        self,
        status_id: str,
    ) -> Optional[QLabel]:
        """
        Return a registered status widget, if present.
        """

        self._validate_status_id(
            status_id
        )

        return self._labels.get(
            status_id
        )

    def has_status(
        self,
        status_id: str,
    ) -> bool:
        """
        Return whether a status field is registered.
        """

        self._validate_status_id(
            status_id
        )

        return status_id in self._labels

    def status_count(
        self,
    ) -> int:
        """Return the number of registered status fields."""

        return len(
            self._labels
        )

    # ========================================================
    # STATUS PRESENTATION
    # ========================================================

    def set_status(
        self,
        status_id: str,
        text: str,
    ) -> None:
        """
        Update only the presentation value of a status field.
        """

        self._validate_status_id(
            status_id
        )

        if not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        label = self._labels.get(
            status_id
        )

        if label is None:
            raise KeyError(
                f"Unknown status: {status_id!r}"
            )

        if label.text() == text:
            return

        label.setText(
            text
        )

        self.status_changed.emit(
            status_id,
            text,
        )

    def set_status_visible(
        self,
        status_id: str,
        visible: bool,
    ) -> None:
        """
        Change only the presentation visibility of a status field.
        """

        self._validate_status_id(
            status_id
        )

        if not isinstance(
            visible,
            bool,
        ):
            raise TypeError(
                "visible must be bool."
            )

        label = self._labels.get(
            status_id
        )

        if label is None:
            raise KeyError(
                f"Unknown status: {status_id!r}"
            )

        label.setVisible(
            visible
        )

    def is_status_visible(
        self,
        status_id: str,
    ) -> bool:
        """
        Return the current presentation visibility of a status field.
        """

        self._validate_status_id(
            status_id
        )

        label = self._labels.get(
            status_id
        )

        if label is None:
            raise KeyError(
                f"Unknown status: {status_id!r}"
            )

        return label.isVisible()

    # ========================================================
    # TRANSIENT MESSAGE
    # ========================================================

    def set_message(
        self,
        text: str,
    ) -> None:
        """
        Display a transient status-bar message.

        This changes presentation only.
        """

        if not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        status_bar = self._status_bar

        if status_bar is None:
            return

        status_bar.showMessage(
            text
        )

    def clear_message(
        self,
    ) -> None:
        """Clear the transient status-bar message."""

        status_bar = self._status_bar

        if status_bar is None:
            return

        status_bar.clearMessage()

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def status_available(
        self,
    ) -> bool:
        """Return whether the application's status bar is available."""

        return self._status_bar is not None

    # ========================================================
    # VALIDATION
    # ========================================================

    def _require_initialized(
        self,
    ) -> None:
        """Require an active plugin lifecycle."""

        if not self._initialized:
            raise RuntimeError(
                "StatusPlugin has not been initialized."
            )

        if self._context is None:
            raise RuntimeError(
                (
                    "StatusPlugin is initialized without "
                    "PluginContext."
                )
            )

        if self._status_bar is None:
            raise RuntimeError(
                (
                    "StatusPlugin is initialized without "
                    "QStatusBar."
                )
            )

    @staticmethod
    def _validate_status_id(
        status_id: str,
    ) -> None:
        """Validate a status identifier."""

        if not isinstance(
            status_id,
            str,
        ):
            raise TypeError(
                "status_id must be a string."
            )

        if not status_id.strip():
            raise ValueError(
                "status_id cannot be empty."
            )


# ============================================================
# DEFAULT STATUS SPECIFICATIONS
# ============================================================


def default_statuses() -> tuple[
    StatusSpec,
    ...
]:
    """
    Return the canonical GridForge baseline status fields.

    These are presentation defaults only.

    Runtime application state must be supplied by the appropriate
    application/UI coordination layer.
    """

    return (
        StatusSpec(
            status_id="tool",
            text="Tool: Select",
            tooltip="Currently active tool.",
            stretch=0,
        ),
        StatusSpec(
            status_id="selection",
            text="Selection: None",
            tooltip="Current canvas selection.",
            stretch=0,
        ),
        StatusSpec(
            status_id="coordinates",
            text="X: —  Y: —",
            tooltip="Current canvas coordinates.",
            stretch=1,
        ),
        StatusSpec(
            status_id="project",
            text="Project: Ready",
            tooltip="Current project state.",
            stretch=0,
            permanent=True,
        ),
    )


# ============================================================
# FACTORY
# ============================================================


def create_status_plugin(
    parent: Optional[QObject] = None,
) -> StatusPlugin:
    """
    Create an uninitialized StatusPlugin.

    PluginContext is supplied exclusively during initialize().
    """

    return StatusPlugin(
        parent=parent
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "StatusSpec",
    "StatusPlugin",
    "default_statuses",
    "create_status_plugin",
]
