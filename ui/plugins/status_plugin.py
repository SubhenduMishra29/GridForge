"""
GridForge V2
============

File:
    ui/plugins/status_plugin.py

Purpose
-------
Composition plugin responsible for the application's status area.

Architectural rules
-------------------
- StatusPlugin owns presentation composition only.
- It does not own authoritative application state.
- It does not perform electrical calculations.
- It does not mutate Core directly.
- Status information is supplied by application/UI services.
- MainWindow remains thin and plugin-driven.
- PySide6 is the only Qt binding used by GridForge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from ui.core.qt import QtWidgets


# ============================================================
# STATUS SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class StatusSpec:
    """
    Declarative description of one status field.
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

        if self.stretch < 0:
            raise ValueError(
                "stretch cannot be negative."
            )


# ============================================================
# STATUS CONTEXT
# ============================================================


@dataclass(slots=True)
class StatusPluginContext:
    """
    Runtime dependencies supplied to StatusPlugin.
    """

    parent: Optional[QWidget] = None

    main_window: Optional[QWidget] = None

    status_manager: Any = None

    project_controller: Any = None

    selection_controller: Any = None

    tool_manager: Any = None

    statuses: tuple[StatusSpec, ...] = ()


# ============================================================
# STATUS PLUGIN
# ============================================================


class StatusPlugin(QObject):
    """
    Composition plugin for the GridForge status bar.

    The plugin presents state supplied by application services but does
    not become the source of that state.
    """

    plugin_id = "status"
    plugin_name = "Status"
    plugin_version = "1.0"

    status_changed = Signal(str, str)

    def __init__(
        self,
        context: Optional[
            StatusPluginContext
        ] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._context = (
            context
            or StatusPluginContext()
        )

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

        self._connections: list[
            tuple[Any, Any]
        ] = []

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> StatusPluginContext:
        """Return the plugin context."""

        return self._context

    @property
    def status_bar(
        self,
    ) -> Optional[QStatusBar]:
        """Return the status bar."""

        return self._status_bar

    @property
    def widget(
        self,
    ) -> Optional[QStatusBar]:
        """Return the status bar as the plugin widget."""

        return self._status_bar

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    @property
    def status_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered status identifiers."""

        return tuple(
            self._labels.keys()
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Optional[
            StatusPluginContext
        ] = None,
    ) -> QStatusBar:
        """
        Initialize the status plugin.

        Initialization is idempotent.
        """

        if self._initialized:
            assert self._status_bar is not None
            return self._status_bar

        if context is not None:
            self._context = context

        self._create_status_bar()

        self._register_context_statuses()

        self._wire_services()

        self._initialized = True

        assert self._status_bar is not None

        return self._status_bar

    def shutdown(self) -> None:
        """
        Disconnect external signals and release plugin bookkeeping.

        The Qt parent hierarchy owns the status bar widget.
        """

        self._disconnect_services()

        self._labels.clear()
        self._specs.clear()

        self._status_bar = None

        self._initialized = False

    # ========================================================
    # STATUS BAR CREATION
    # ========================================================

    def _create_status_bar(self) -> None:
        """Create or obtain the application's QStatusBar."""

        main_window = self._context.main_window

        if (
            main_window is not None
            and hasattr(
                main_window,
                "statusBar",
            )
        ):
            status_bar = main_window.statusBar()

            if status_bar is None:
                status_bar = QStatusBar(
                    main_window
                )

                if hasattr(
                    main_window,
                    "setStatusBar",
                ):
                    main_window.setStatusBar(
                        status_bar
                    )

            self._status_bar = status_bar
            return

        self._status_bar = QStatusBar(
            self._context.parent
        )

    # ========================================================
    # STATUS REGISTRATION
    # ========================================================

    def _register_context_statuses(self) -> None:
        """Register status fields supplied by the context."""

        for spec in self._context.statuses:
            self.add_status(
                spec
            )

    def add_status(
        self,
        spec: StatusSpec,
    ) -> QLabel:
        """
        Add a status field.

        Status identifiers must be unique.
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
                "Status bar has not been initialized."
            )

        label = QLabel(
            spec.text,
            self._status_bar,
        )

        label.setObjectName(
            f"status_{spec.status_id}"
        )

        if spec.tooltip:
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
        """Remove a registered status field."""

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

    # ========================================================
    # STATUS ACCESS
    # ========================================================

    def status(
        self,
        status_id: str,
    ) -> Optional[QLabel]:
        """Return a status label."""

        return self._labels.get(
            status_id
        )

    def has_status(
        self,
        status_id: str,
    ) -> bool:
        """Return whether a status field exists."""

        return status_id in self._labels

    def set_status(
        self,
        status_id: str,
        text: str,
    ) -> None:
        """
        Update a status field.

        This changes presentation only. It does not modify the source
        application state.
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
        """Change status field visibility."""

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
    # CONVENIENCE STATUS
    # ========================================================

    def set_message(
        self,
        text: str,
    ) -> None:
        """Set the transient status-bar message."""

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
    # SERVICE WIRING
    # ========================================================

    def _wire_services(self) -> None:
        """
        Connect compatible application services.

        Services remain authoritative for the state they expose.
        """

        self._attach_status_manager()

        self._connect_service(
            self._context.project_controller
        )

        self._connect_service(
            self._context.selection_controller
        )

        self._connect_service(
            self._context.tool_manager
        )

    def _attach_status_manager(self) -> None:
        """Attach the status bar to the status manager."""

        manager = self._context.status_manager

        if manager is None:
            return

        self._invoke_optional(
            manager,
            (
                "set_status_bar",
                "set_status_widget",
                "attach_status_bar",
            ),
            self._status_bar,
        )

        self._connect_service(
            manager
        )

    def _connect_service(
        self,
        service: Any,
    ) -> None:
        """
        Connect common status-producing signals where available.

        The plugin deliberately supports only established, conventional
        signal names and does not require every service to implement
        them.
        """

        if service is None:
            return

        candidates = (
            (
                "status_message",
                self.set_message,
            ),
            (
                "status_changed",
                self._on_status_changed,
            ),
            (
                "selection_changed",
                self._on_selection_changed,
            ),
            (
                "tool_changed",
                self._on_tool_changed,
            ),
            (
                "active_tool_changed",
                self._on_tool_changed,
            ),
        )

        for signal_name, callback in candidates:
            signal = getattr(
                service,
                signal_name,
                None,
            )

            connect = getattr(
                signal,
                "connect",
                None,
            )

            if not callable(connect):
                continue

            try:
                connect(
                    callback
                )
            except (TypeError, RuntimeError):
                continue

            self._connections.append(
                (
                    signal,
                    callback,
                )
            )

    def _disconnect_services(self) -> None:
        """Disconnect signals previously connected by the plugin."""

        for signal, callback in tuple(
            self._connections
        ):
            disconnect = getattr(
                signal,
                "disconnect",
                None,
            )

            if not callable(
                disconnect
            ):
                continue

            try:
                disconnect(
                    callback
                )
            except (TypeError, RuntimeError):
                pass

        self._connections.clear()

        manager = self._context.status_manager

        if manager is not None:
            self._invoke_optional(
                manager,
                (
                    "detach_status_bar",
                    "clear_status_bar",
                ),
                self._status_bar,
            )

    # ========================================================
    # EXTERNAL STATE HANDLERS
    # ========================================================

    def _on_status_changed(
        self,
        status_id: Any,
        text: Any = "",
    ) -> None:
        """Reflect an externally supplied status update."""

        status_id = str(
            status_id
        )

        if status_id not in self._labels:
            return

        self.set_status(
            status_id,
            str(text),
        )

    def _on_selection_changed(
        self,
        selection: Any = None,
        *args: Any,
    ) -> None:
        """Reflect selection state when a suitable status exists."""

        if "selection" not in self._labels:
            return

        if selection is None:
            text = "Selection: None"
        else:
            try:
                count = len(selection)
            except TypeError:
                count = 1

            text = (
                f"Selection: {count}"
            )

        self.set_status(
            "selection",
            text,
        )

    def _on_tool_changed(
        self,
        tool_id: Any = None,
        *args: Any,
    ) -> None:
        """Reflect active-tool state when a suitable status exists."""

        if "tool" not in self._labels:
            return

        text = (
            "Tool: "
            + (
                str(tool_id)
                if tool_id is not None
                else "None"
            )
        )

        self.set_status(
            "tool",
            text,
        )

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def status_count(self) -> int:
        """Return the number of registered status fields."""

        return len(
            self._labels
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

        Exceptions raised by an existing method are intentionally not
        swallowed because they represent genuine integration errors.
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
# DEFAULT STATUS SPECIFICATIONS
# ============================================================


def default_statuses() -> tuple[
    StatusSpec,
    ...
]:
    """
    Return the canonical baseline status fields.

    These are presentation fields only; their values are supplied by
    the corresponding application services.
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
    context: Optional[
        StatusPluginContext
    ] = None,
    parent: Optional[QObject] = None,
) -> StatusPlugin:
    """Create an uninitialized StatusPlugin."""

    return StatusPlugin(
        context=context,
        parent=parent,
    )


__all__ = [
    "StatusSpec",
    "StatusPluginContext",
    "StatusPlugin",
    "default_statuses",
    "create_status_plugin",
]
