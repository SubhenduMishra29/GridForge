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
    - creates the status-bar presentation
    - registers presentation fields
    - exposes the resulting QStatusBar
    - delegates application/UI coordination through PluginContext
      and its controller

It does NOT:
    - own application state
    - own project state
    - own network state
    - access Core directly
    - perform electrical calculations
    - construct controllers or services
    - maintain a second application-state model
    - communicate directly with MainWindow beyond the injected
      PluginContext boundary

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
    +--> controller
    +--> main_window
    |
    v
StatusPlugin
    |
    v
QStatusBar

PySide6 is the only Qt binding used by GridForge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar

from ui.plugins.plugin_context import PluginContext


# ============================================================
# STATUS SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class StatusSpec:
    """
    Declarative description of one status-bar field.

    StatusSpec contains presentation metadata only.

    It does not contain application state and does not reference
    controllers or Core objects.
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

        if not isinstance(self.stretch, int):
            raise TypeError(
                "stretch must be an integer."
            )

        if self.stretch < 0:
            raise ValueError(
                "stretch cannot be negative."
            )


# ============================================================
# STATUS PLUGIN
# ============================================================


class StatusPlugin(QObject):
    """
    GridForge status-bar composition plugin.

    Ownership
    ---------
    The plugin owns the composition and presentation bookkeeping of
    the status bar.

    Application state remains outside the plugin.

    Dependency boundary
    -------------------
    PluginContext is the only application dependency gateway.

    The plugin therefore does not receive independent references to:

        - project controller
        - selection controller
        - tool manager
        - status manager
        - Core objects
        - domain models

    Such dependencies must be coordinated through the application's
    controller exposed by PluginContext.
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
        """Return the composed status bar."""

        return self._status_bar

    @property
    def widget(self) -> Optional[QStatusBar]:
        """
        Return the plugin's composed UI component.

        UI registry/plugin manager can use this as the component
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

        return tuple(self._labels.keys())

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(self) -> QStatusBar:
        """
        Initialize the status plugin.

        PluginContext is supplied during construction and is not
        replaced during initialization.

        Initialization is idempotent.
        """

        if self._initialized:
            assert self._status_bar is not None
            return self._status_bar

        self._create_status_bar()

        self._initialized = True

        assert self._status_bar is not None

        return self._status_bar

    def shutdown(self) -> None:
        """
        Release plugin-owned presentation bookkeeping.

        The plugin does not destroy MainWindow or application services.

        The status bar itself remains under Qt/MainWindow ownership.
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
        Create or obtain the application's QStatusBar.

        MainWindow is supplied through PluginContext and remains the
        owner of the application status bar.
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

    # ========================================================
    # STATUS REGISTRATION
    # ========================================================

    def add_status(
        self,
        spec: StatusSpec,
    ) -> QLabel:
        """
        Add a presentation field to the status bar.

        The plugin owns the presentation widget but not the state
        represented by that widget.
        """

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

        if self._status_bar is None:
            raise RuntimeError(
                "StatusPlugin has not been initialized."
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
        Remove a presentation status field.

        No application state is modified.
        """

        if not isinstance(
            status_id,
            str,
        ):
            raise TypeError(
                "status_id must be a string."
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
        """Return a status presentation widget."""

        return self._labels.get(
            status_id
        )

    def has_status(
        self,
        status_id: str,
    ) -> bool:
        """Return whether a status field is registered."""

        return status_id in self._labels

    def set_status(
        self,
        status_id: str,
        text: str,
    ) -> None:
        """
        Update status presentation.

        This method changes only the UI representation. It does not
        write state to Core or to the controller.
        """

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
        """Change presentation visibility."""

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

    # ========================================================
    # TRANSIENT MESSAGE
    # ========================================================

    def set_message(
        self,
        text: str,
    ) -> None:
        """
        Display a transient status-bar message.

        This is presentation only.
        """

        if not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        if self._status_bar is None:
            return

        self._status_bar.showMessage(
            text
        )

    def clear_message(self) -> None:
        """Clear the transient status-bar message."""

        if self._status_bar is None:
            return

        self._status_bar.clearMessage()

    # ========================================================
    # CONTROLLER BRIDGE
    # ========================================================

    def controller(self) -> Any:
        """
        Return the approved UI controller.

        This method exists only as a narrow convenience accessor.

        StatusPlugin must not use the controller as a replacement for
        Core ownership or as a local application-state store.
        """

        return self._context.controller

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def status_count(self) -> int:
        """Return the number of registered status fields."""

        return len(
            self._labels
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

    These definitions establish presentation only.

    Their runtime values must be supplied by the controller/UI
    coordination layer rather than being calculated by this plugin.
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
    context: PluginContext,
    parent: Optional[QObject] = None,
) -> StatusPlugin:
    """
    Create an uninitialized StatusPlugin.

    Plugin construction does not perform UI composition.
    Initialization remains explicit.
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
