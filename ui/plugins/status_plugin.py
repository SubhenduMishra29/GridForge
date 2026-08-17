"""
GridForge V2
============

File:
    ui/plugins/status_plugin.py

Purpose
-------
Composition plugin responsible for creating and exposing the
application status bar.

Architectural role
------------------
StatusPlugin is a UI composition plugin.

It:

    - obtains the application's QStatusBar;
    - composes presentation fields;
    - owns only its presentation bookkeeping;
    - exposes the resulting QStatusBar;
    - provides presentation-only update operations.

It does NOT:

    - own application state;
    - own project state;
    - own network state;
    - access Core directly;
    - perform electrical calculations;
    - construct controllers or services;
    - maintain a second application-state model;
    - expose controllers as a service locator;
    - mutate application/domain state.

Architecture
------------
main.py
    |
    v
MainWindow
    |
    v
PluginManager / UI Registry
    |
    v
PluginContext
    |
    +--> main_window
    |
    v
StatusPlugin
    |
    v
QStatusBar

Qt boundary
-----------
All Qt imports are obtained from:

    ui.core.qt

PySide6 remains the sole Qt backend, but individual UI modules
must not import PySide6 directly.
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

from ui.plugins.plugin_context import PluginContext


# ============================================================
# STATUS SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class StatusSpec:
    """
    Declarative description of one status-bar presentation field.

    StatusSpec contains presentation metadata only.

    It does not contain application state and does not reference
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
        if (
            not isinstance(self.status_id, str)
            or not self.status_id.strip()
        ):
            raise ValueError(
                "status_id must be a non-empty string."
            )

        if not isinstance(self.text, str):
            raise TypeError(
                "text must be a string."
            )

        if self.tooltip is not None and not isinstance(
            self.tooltip,
            str,
        ):
            raise TypeError(
                "tooltip must be a string or None."
            )

        if not isinstance(self.stretch, int):
            raise TypeError(
                "stretch must be an integer."
            )

        if isinstance(self.stretch, bool):
            raise TypeError(
                "stretch must be an integer, not bool."
            )

        if self.stretch < 0:
            raise ValueError(
                "stretch cannot be negative."
            )

        if not isinstance(self.permanent, bool):
            raise TypeError(
                "permanent must be bool."
            )

        if not isinstance(self.visible, bool):
            raise TypeError(
                "visible must be bool."
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping."
            )


# ============================================================
# STATUS PLUGIN
# ============================================================


class StatusPlugin(QObject):
    """
    GridForge status-bar composition plugin.

    Ownership
    ---------
    The plugin owns:

        - status presentation composition;
        - status specification bookkeeping;
        - status QLabel instances created by the plugin.

    The MainWindow owns the QStatusBar through Qt's parent-child
    ownership model.

    Application state remains outside this plugin.

    Dependency boundary
    -------------------
    PluginContext is the application's dependency boundary.

    StatusPlugin does not expose the controller or any other
    application service as a convenience accessor. Presentation
    coordination belongs to the appropriate application/UI
    coordination layer.
    """

    plugin_id = "status"
    plugin_name = "Status"
    plugin_version = "1.0"

    status_changed = Signal(str, str)

    def __init__(
        self,
        context: PluginContext,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        if not isinstance(
            context,
            PluginContext,
        ):
            raise TypeError(
                "StatusPlugin requires PluginContext."
            )

        self._context = context

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
    def context(self) -> PluginContext:
        """Return the plugin dependency context."""

        return self._context

    @property
    def status_bar(self) -> Optional[QStatusBar]:
        """Return the composed application status bar."""

        return self._status_bar

    @property
    def widget(self) -> Optional[QStatusBar]:
        """
        Return the plugin's composed UI component.

        Plugin infrastructure may use this as the component
        produced by the plugin.
        """

        return self._status_bar

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    @property
    def status_ids(self) -> tuple[str, ...]:
        """Return registered status identifiers."""

        return tuple(
            self._labels.keys()
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(self) -> QStatusBar:
        """
        Initialize the status plugin.

        Initialization is idempotent.

        The MainWindow supplies the authoritative QStatusBar.
        The plugin does not create or replace the MainWindow's
        status-bar ownership.

        Canonical presentation fields are composed during the
        first initialization.
        """

        if self._initialized:
            if self._status_bar is None:
                raise RuntimeError(
                    "StatusPlugin is initialized without a status bar."
                )

            return self._status_bar

        self._create_status_bar()

        self._register_default_statuses()

        self._initialized = True

        if self._status_bar is None:
            raise RuntimeError(
                "Status bar creation failed."
            )

        return self._status_bar

    def shutdown(self) -> None:
        """
        Release plugin-owned presentation objects.

        The MainWindow-owned QStatusBar is not destroyed.

        Application services and application state are not modified.
        """

        if not self._initialized:
            return

        self._remove_plugin_statuses()

        self._status_bar = None
        self._initialized = False

    # ========================================================
    # STATUS BAR COMPOSITION
    # ========================================================

    def _create_status_bar(self) -> None:
        """
        Obtain the application's QStatusBar.

        The status bar belongs to the MainWindow. This plugin does
        not construct an independent status bar.
        """

        main_window = self._context.main_window

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                "PluginContext.main_window must be QMainWindow."
            )

        self._status_bar = main_window.statusBar()

    def _register_default_statuses(self) -> None:
        """Register the canonical GridForge status presentation."""

        for spec in default_statuses():
            self.add_status(
                spec
            )

    # ========================================================
    # STATUS REGISTRATION
    # ========================================================

    def add_status(
        self,
        spec: StatusSpec,
    ) -> QLabel:
        """
        Add one presentation field to the status bar.

        The plugin owns the created QLabel.

        The value represented by the label remains presentation
        state only; authoritative application state is external.
        """

        if not isinstance(
            spec,
            StatusSpec,
        ):
            raise TypeError(
                "spec must be StatusSpec."
            )

        if self._status_bar is None:
            raise RuntimeError(
                "StatusPlugin has not been initialized."
            )

        if spec.status_id in self._labels:
            raise ValueError(
                (
                    f"Status {spec.status_id!r} "
                    "is already registered."
                )
            )

        label = QLabel(
            spec.text,
            self._status_bar,
        )

        label.setObjectName(
            f"status_{spec.status_id}"
        )

        if spec.tooltip is not None:
            label.setToolTip(
                spec.tooltip
            )

        label.setVisible(
            spec.visible
        )

        if spec.permanent:
            self._status_bar.addPermanentWidget(
                label,
                spec.stretch,
            )
        else:
            self._status_bar.addWidget(
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
        Remove a plugin-owned presentation field.

        No application or domain state is modified.
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

        if self._status_bar is not None:
            self._status_bar.removeWidget(
                label
            )

        label.deleteLater()

        return label

    def _remove_plugin_statuses(self) -> None:
        """Remove all status fields composed by this plugin."""

        for status_id in tuple(
            self._labels.keys()
        ):
            self.remove_status(
                status_id
            )

    # ========================================================
    # STATUS ACCESS
    # ========================================================

    def status(
        self,
        status_id: str,
    ) -> Optional[QLabel]:
        """Return a registered status presentation widget."""

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
        """Return whether a status field is registered."""

        self._validate_status_id(
            status_id
        )

        return status_id in self._labels

    def status_spec(
        self,
        status_id: str,
    ) -> Optional[StatusSpec]:
        """Return the immutable specification for a status field."""

        self._validate_status_id(
            status_id
        )

        return self._specs.get(
            status_id
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
        Update status presentation.

        This changes only the QLabel representation.

        It does not write state to Core, the project, or an
        application controller.
        """

        if not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

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
        """Change presentation visibility."""

        if not isinstance(
            visible,
            bool,
        ):
            raise TypeError(
                "visible must be bool."
            )

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

        label.setVisible(
            visible
        )

    # ========================================================
    # TRANSIENT MESSAGE
    # ========================================================

    def set_message(
        self,
        text: str,
    ) -> None:
        """
        Display a transient status-bar message.

        This is presentation only and does not represent persistent
        application state.
        """

        if not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        if self._status_bar is None:
            raise RuntimeError(
                "StatusPlugin has not been initialized."
            )

        self._status_bar.showMessage(
            text
        )

    def clear_message(self) -> None:
        """Clear the transient status-bar message."""

        if self._status_bar is None:
            raise RuntimeError(
                "StatusPlugin has not been initialized."
            )

        self._status_bar.clearMessage()

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def status_count(self) -> int:
        """Return the number of registered status fields."""

        return len(
            self._labels
        )

    # ========================================================
    # VALIDATION HELPERS
    # ========================================================

    @staticmethod
    def _validate_status_id(
        status_id: str,
    ) -> None:
        """Validate a status identifier."""

        if (
            not isinstance(status_id, str)
            or not status_id.strip()
        ):
            raise ValueError(
                "status_id must be a non-empty string."
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

    These definitions describe presentation defaults only.

    Runtime values are supplied by the appropriate application/UI
    coordination layer.
    """

    return (
        StatusSpec(
            status_id="tool",
            text="Tool: Select",
            tooltip="Currently active tool.",
        ),
        StatusSpec(
            status_id="selection",
            text="Selection: None",
            tooltip="Current canvas selection.",
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
            permanent=True,
        ),
    )


# ============================================================
# FACTORY
# ============================================================


def create_status_plugin(
    context: PluginContext,
    parent: Optional[QObject] = None,
) -> StatusPlugin:
    """
    Create an uninitialized StatusPlugin.

    Construction performs dependency validation only.

    UI composition remains explicit through initialize().
    """

    return StatusPlugin(
        context=context,
        parent=parent,
    )


__all__ = [
    "StatusSpec",
    "StatusPlugin",
    "default_statuses",
    "create_status_plugin",
]
