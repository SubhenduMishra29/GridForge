# ============================================================

# GridForge V2

# ============================================================

# File:

# ui/plugins/panels_plugin.py

#

# Purpose

# -------

# Panel composition plugin for the GridForge UI.

#

# Architectural boundary

# ----------------------

#

# PanelsPlugin owns:

# - panel specification;

# - panel presentation widget creation;

# - QDockWidget creation;

# - panel capability configuration;

# - panel registration;

# - panel lifecycle;

# - exposure of dock widgets to the composition layer.

#

# PanelsPlugin does NOT own:

# - Workspace layout;

# - logical panel placement;

# - dock-area policy;

# - tab groups;

# - split arrangement;

# - MainWindow layout policy;

# - visibility policy;

# - authoritative application state;

# - Core/domain state.

#

# Workspace/Layout is the sole authority for:

# - PanelArea;

# - placement;

# - ordering;

# - grouping/tabbing;

# - visibility;

# - floating placement.

#

# WorkspaceRealizer translates WorkspaceLayout into MainWindow

# operations.

#

# MainWindow remains the Qt dock/layout host.

#

# No direct PySide6/PyQt imports are permitted here.

# ============================================================

"""
GridForge V2 — Panels Plugin.
"""

from **future** import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ui.core.qt import (
QDockWidget,
QMainWindow,
QObject,
QWidget,
)

from ui.plugins.plugin_context import PluginContext

# ============================================================

# PANEL SPECIFICATION

# ============================================================

@dataclass(frozen=True, slots=True)
class PanelSpec:
"""
Declarative description of a panel.

```
PanelSpec describes panel identity, presentation, capabilities,
and metadata.

It deliberately contains NO Workspace placement or visibility
information.

Placement and visibility belong to WorkspacePlacement /
WorkspaceLayout.
"""

panel_id: str

title: str

widget: Optional[QWidget] = None

closable: bool = True

movable: bool = True

floatable: bool = True

metadata: Mapping[str, Any] = field(
    default_factory=dict
)

def __post_init__(self) -> None:
    if (
        not isinstance(self.panel_id, str)
        or not self.panel_id.strip()
    ):
        raise ValueError(
            "panel_id must be a non-empty string."
        )

    if not isinstance(self.title, str):
        raise TypeError(
            "title must be a string."
        )

    if not self.title.strip():
        raise ValueError(
            "title must not be empty."
        )

    if self.widget is not None and not isinstance(
        self.widget,
        QWidget,
    ):
        raise TypeError(
            "widget must be QWidget or None."
        )

    if not isinstance(self.closable, bool):
        raise TypeError(
            "closable must be bool."
        )

    if not isinstance(self.movable, bool):
        raise TypeError(
            "movable must be bool."
        )

    if not isinstance(self.floatable, bool):
        raise TypeError(
            "floatable must be bool."
        )
```

# ============================================================

# PANELS PLUGIN

# ============================================================

class PanelsPlugin(QObject):
"""
GridForge panel composition plugin.

```
This plugin creates and owns panel presentation objects.

It does not decide where or whether those panels are displayed.

The Workspace subsystem owns arrangement and visibility policy.
WorkspaceRealizer realizes those decisions through MainWindow.
"""

plugin_id = "panels"
plugin_name = "Panels"
plugin_version = "1.0"
plugin_description = (
    "GridForge application panel and dock composition."
)

plugin_dependencies: tuple[str, ...] = ()
plugin_optional = False

def __init__(
    self,
    parent: Optional[QObject] = None,
) -> None:
    """
    Construct the plugin.

    Construction performs no UI composition and accepts no
    application services.
    """

    super().__init__(parent)

    self._context: Optional[PluginContext] = None

    self._panels: dict[
        str,
        QWidget,
    ] = {}

    self._dock_widgets: dict[
        str,
        QDockWidget,
    ] = {}

    self._panel_specs: dict[
        str,
        PanelSpec,
    ] = {}

    self._initialized = False

# ========================================================
# PROPERTIES
# ========================================================

@property
def context(self) -> Optional[PluginContext]:
    """Return the active shared plugin context."""

    return self._context

@property
def widget(self) -> Optional[QWidget]:
    """
    Return the plugin presentation root.

    Panels are independently dockable, therefore this plugin has
    no central presentation widget.
    """

    return None

@property
def initialized(self) -> bool:
    """Return whether the plugin has been initialized."""

    return self._initialized

@property
def dock_widgets(self) -> tuple[QDockWidget, ...]:
    """
    Return all managed dock widgets.

    The returned docks are presentation objects.

    Their placement and visibility are NOT defined here.
    """

    return tuple(
        self._dock_widgets.values()
    )

@property
def panel_ids(self) -> tuple[str, ...]:
    """Return registered panel identifiers."""

    return tuple(
        self._panels.keys()
    )

# ========================================================
# LIFECYCLE
# ========================================================

def initialize(
    self,
    context: PluginContext,
) -> None:
    """
    Initialize panel composition.

    PluginContext is the application dependency boundary.

    No docks are created until a panel is explicitly registered.
    """

    if not isinstance(
        context,
        PluginContext,
    ):
        raise TypeError(
            "PanelsPlugin requires PluginContext."
        )

    if self._initialized:
        if self._context is not context:
            raise RuntimeError(
                "PanelsPlugin is already initialized "
                "with a different PluginContext."
            )

        return

    main_window = context.main_window

    if not isinstance(
        main_window,
        QMainWindow,
    ):
        raise TypeError(
            "PluginContext.main_window must be QMainWindow."
        )

    self._context = context
    self._initialized = True

def shutdown(self) -> None:
    """
    Shut down panel composition.

    MainWindow itself is never destroyed here.

    Docks are detached from the window through the MainWindow
    host abstraction and then scheduled for Qt deletion.
    """

    if not self._initialized:
        return

    for dock in tuple(
        self._dock_widgets.values()
    ):
        self._remove_dock(
            dock
        )

    self._dock_widgets.clear()
    self._panels.clear()
    self._panel_specs.clear()

    self._context = None
    self._initialized = False

# ========================================================
# PANEL REGISTRATION
# ========================================================

def add_panel(
    self,
    spec: PanelSpec,
) -> QWidget:
    """
    Register and compose one panel.

    This creates the presentation dock but does NOT place it
    and does NOT determine its visibility.

    WorkspaceRealizer is responsible for realizing placement
    and visibility.
    """

    self._require_initialized()

    if not isinstance(
        spec,
        PanelSpec,
    ):
        raise TypeError(
            "spec must be PanelSpec."
        )

    if spec.panel_id in self._panel_specs:
        raise ValueError(
            (
                f"Panel {spec.panel_id!r} "
                "is already registered."
            )
        )

    widget = spec.widget

    if widget is None:
        widget = QWidget()

    self._panel_specs[
        spec.panel_id
    ] = spec

    self._panels[
        spec.panel_id
    ] = widget

    try:
        self._create_panel_dock(
            spec,
            widget,
        )
    except Exception:
        self._panels.pop(
            spec.panel_id,
            None,
        )

        self._panel_specs.pop(
            spec.panel_id,
            None,
        )

        raise

    return widget

def remove_panel(
    self,
    panel_id: str,
) -> Optional[QWidget]:
    """
    Remove a registered panel.

    Returns the panel widget if it existed.
    """

    self._require_initialized()

    self._validate_panel_id(
        panel_id
    )

    widget = self._panels.pop(
        panel_id,
        None,
    )

    self._panel_specs.pop(
        panel_id,
        None,
    )

    dock = self._dock_widgets.pop(
        panel_id,
        None,
    )

    if dock is not None:
        self._remove_dock(
            dock
        )

    return widget

def panel(
    self,
    panel_id: str,
) -> Optional[QWidget]:
    """Return a registered panel widget."""

    self._validate_panel_id(
        panel_id
    )

    return self._panels.get(
        panel_id
    )

def dock(
    self,
    panel_id: str,
) -> Optional[QDockWidget]:
    """
    Return the presentation dock for a panel.

    This does not imply any placement or visibility policy.
    """

    self._validate_panel_id(
        panel_id
    )

    return self._dock_widgets.get(
        panel_id
    )

def spec(
    self,
    panel_id: str,
) -> Optional[PanelSpec]:
    """Return the registered panel specification."""

    self._validate_panel_id(
        panel_id
    )

    return self._panel_specs.get(
        panel_id
    )

def panels(self) -> tuple[QWidget, ...]:
    """Return all registered panel widgets."""

    return tuple(
        self._panels.values()
    )

# ========================================================
# DOCK CREATION
# ========================================================

def _create_panel_dock(
    self,
    spec: PanelSpec,
    widget: QWidget,
) -> QDockWidget:
    """
    Create the presentation dock for a panel.

    IMPORTANT:
        This method does NOT call addDockWidget().
        It does NOT call setVisible().
        It only creates/configures the dock.

    WorkspaceRealizer/MainWindow owns placement and visibility.
    """

    context = self._context

    if context is None:
        raise RuntimeError(
            "PanelsPlugin has no PluginContext."
        )

    main_window = context.main_window

    if not isinstance(
        main_window,
        QMainWindow,
    ):
        raise TypeError(
            "PluginContext.main_window must be QMainWindow."
        )

    dock = QDockWidget(
        spec.title,
        main_window,
    )

    dock.setObjectName(
        f"gridforge_panel_{spec.panel_id}"
    )

    dock.setFeatures(
        self._dock_features(
            spec
        )
    )

    dock.setWidget(
        widget
    )

    self._dock_widgets[
        spec.panel_id
    ] = dock

    return dock

# ========================================================
# DOCK CAPABILITIES
# ========================================================

@staticmethod
def _dock_features(
    spec: PanelSpec,
) -> QDockWidget.DockWidgetFeatures:
    """
    Convert panel capabilities into Qt dock features.

    This describes capability only.

    It does NOT describe placement or visibility.
    """

    features = (
        QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
        | QDockWidget.DockWidgetFeature.DockWidgetFloatable
    )

    if not spec.closable:
        features &= ~(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

    if not spec.movable:
        features &= ~(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
        )

    if not spec.floatable:
        features &= ~(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

    return features

# ========================================================
# INTERNAL CLEANUP
# ========================================================

def _remove_dock(
    self,
    dock: QDockWidget,
) -> None:
    """
    Remove a dock from MainWindow through the host abstraction.

    PanelsPlugin does not directly manipulate the QMainWindow
    docking/layout API.
    """

    context = self._context

    if context is None:
        dock.deleteLater()
        return

    main_window = context.main_window

    remove_dock = getattr(
        main_window,
        "remove_dock_widget",
        None,
    )

    if callable(remove_dock):
        remove_dock(
            dock
        )
    else:
        dock.deleteLater()

# --------------------------------------------------------

def _remove_all_docks(self) -> None:
    """Remove all managed docks."""

    for dock in tuple(
        self._dock_widgets.values()
    ):
        self._remove_dock(
            dock
        )

    self._dock_widgets.clear()

# ========================================================
# VALIDATION
# ========================================================

def _require_initialized(self) -> None:
    """Require an initialized plugin."""

    if not self._initialized:
        raise RuntimeError(
            "PanelsPlugin is not initialized."
        )

@staticmethod
def _validate_panel_id(
    panel_id: str,
) -> None:
    """Validate a panel identifier."""

    if (
        not isinstance(panel_id, str)
        or not panel_id.strip()
    ):
        raise ValueError(
            "panel_id must be a non-empty string."
        )
```
