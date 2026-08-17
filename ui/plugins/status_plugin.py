"""
GridForge V2
============

File:
    ui/plugins/status_plugin.py

Purpose
-------
Composition plugin responsible for creating and managing the
application status-bar presentation.

Architectural rules
-------------------
- The plugin owns status-bar presentation composition only.
- The plugin does not own authoritative application state.
- The plugin does not perform electrical calculations.
- The plugin does not mutate Core directly.
- The plugin does not construct application services/controllers.
- PluginContext is an initialization dependency, not a constructor
  dependency.
- Construction and initialization are separate lifecycle phases.
- Qt access occurs exclusively through ui.core.qt.
- MainWindow remains thin and plugin-driven.
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
    QWidget,
)

from .plugin_contract import PluginContextProtocol


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
        if not isinstance(
            self.status_id,
            str,
        ) or not self.status_id.strip():
            raise ValueError(
                "status_id must be a non-empty string."
            )

        if not isinstance(
            self.text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

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

        if not isinstance(
            self.visible,
            bool,
        ):
            raise TypeError(
                "visible must be bool."
            )

        if not isinstance(
            self.permanent,
            bool,
        ):
            raise TypeError(
                "permanent must be bool."
            )


# ============================================================
# STATUS PLUGIN
# ============================================================


class StatusPlugin(QObject):
    """
    GridForge status-bar composition plugin.

    Lifecycle
    ---------
    Construction:
        Creates only plugin-owned bookkeeping.

    initialize(context):
        Receives the application/UI context and composes the
        application's status-bar presentation.

    shutdown():
        Removes only presentation fields created by this plugin.

    Ownership
    ---------
    The plugin owns:

        - status-field specifications;
        - status-field QLabel instances;
        - presentation operations;
        - the reference to the application's QStatusBar.

    The plugin does NOT own:

        - MainWindow;
        - QStatusBar lifetime;
        - project state;
        - network state;
        - Core state;
        - controller state;
        - command history;
        - simulation state.
    """

    plugin_id = "status"
    plugin_name = "Status"
    plugin_version = "1.0"

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

        Application context is deliberately not accepted here.

        PluginContext is supplied through initialize(context).
        """

        super().__init__(
            parent
        )

        self._context: Optional[
            PluginContextProtocol
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
    ) -> Optional[PluginContextProtocol]:
        """
        Return the current initialization context.

        Returns None before initialization.
        """

        return self._context

    @property
    def status_bar(
        self,
    ) -> Optional[QStatusBar]:
        """
        Return the application's composed status bar.

        The QStatusBar itself remains owned by QMainWindow.
        """

        return self._status_bar

    @property
    def widget(
        self,
    ) -> Optional[QStatusBar]:
        """
        Return the plugin's composed UI component.
        """

        return self._status_bar

    @property
    def initialized(
        self,
    ) -> bool:
        """
        Return whether the plugin has been initialized.
        """

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

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: PluginContextProtocol,
    ) -> QStatusBar:
        """
        Initialize the status plugin with an application context.

        Construction and initialization are deliberately separate.

        Initialization is idempotent. Reinitialization with a
        different context is rejected while the plugin is active.
        """

        if not isinstance(
            context,
            PluginContextProtocol,
        ):
            raise TypeError(
                "context must satisfy PluginContextProtocol."
            )

        if self._initialized:
            if context is not self._context:
                raise RuntimeError(
                    "StatusPlugin is already initialized "
                    "with a different context."
                )

            assert self._status_bar is not None

            return self._status_bar

        self._context = context

        try:
            self._create_status_bar()

            self._register_default_statuses()

            self._initialized = True

            assert self._status_bar is not None

            return self._status_bar

        except Exception:
            self._remove_plugin_statuses()

            self._status_bar = None
            self._context = None

            raise

    def shutdown(
        self,
    ) -> None:
        """
        Shut down the plugin's presentation composition.

        The application's QStatusBar is not destroyed because it is
        owned by QMainWindow.

        Only fields created by this plugin are removed.
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

        MainWindow remains the owner of the status bar.
        """

        context = self._context

        if context is None:
            raise RuntimeError(
                "StatusPlugin context is not initialized."
            )

        main_window = context.main_window

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                "PluginContext.main_window must be QMainWindow."
            )

        self._status_bar = (
            main_window.statusBar()
        )

    # ========================================================
    # STATUS REGISTRATION
    # ========================================================

    def _register_default_statuses(
        self,
    ) -> None:
        """
        Register the canonical baseline status fields.

        Status values are presentation defaults only. Runtime values
        may subsequently be supplied by application/UI coordination.
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
        Add one presentation field to the status bar.

        The plugin owns the QLabel but not the state represented by it.
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

        if self._status_bar is not None:
            self._status_bar.removeWidget(
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

    # ========================================================
    # STATUS ACCESS
    # ========================================================

    def status(
        self,
        status_id: str,
    ) -> Optional[QLabel]:
        """
        Return a registered status widget.
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

    # ========================================================
    # TRANSIENT MESSAGE
    # ========================================================

    def set_message(
        self,
        text: str,
    ) -> None:
        """
        Display a transient status-bar message.

        This modifies presentation only.
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

    def clear_message(
        self,
    ) -> None:
        """
        Clear the transient status-bar message.
        """

        if self._status_bar is None:
            return

        self._status_bar.clearMessage()

    # ========================================================
    # CONTEXT ACCESS
    # ========================================================

    def controller(
        self,
    ) -> Any:
        """
        Return the application's controller from the context.

        This is a narrow dependency accessor. It does not make the
        controller plugin-owned state.
        """

        context = self._context

        if context is None:
            return None

        return context.service(
            "controller",
            getattr(
                context,
                "controller",
                None,
            ),
        )

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def status_count(
        self,
    ) -> int:
        """
        Return the number of registered status fields.
        """

        return len(
            self._labels
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_status_id(
        status_id: str,
    ) -> None:
        """
        Validate a status identifier.
        """

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

    These values are presentation defaults only. Runtime state must
    be supplied by the application/UI coordination layer.
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

    No PluginContext is accepted here.

    Context assignment occurs exclusively through:

        plugin.initialize(context)
    """

    return StatusPlugin(
        parent=parent,
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
