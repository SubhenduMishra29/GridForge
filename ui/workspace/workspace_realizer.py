```python
# ============================================================
# File: ui/workspace/workspace_realizer.py
# GridForge V2 — Workspace Qt Realizer
# ============================================================

"""
GridForge V2 — Workspace Realizer.

Logical WorkspaceLayout -> Qt realization boundary.

Architectural ownership
-----------------------

WorkspaceManager
    Owns workspace definitions and logical workspace state.

WorkspaceLayout
    Describes the logical arrangement of panels/editors.

WorkspaceRealizer
    Translates WorkspaceLayout into operations on the existing
    MainWindow host.

MainWindow
    Owns the Qt workspace infrastructure and performs the actual
    Qt docking operations.

PanelsPlugin
    Owns panel composition and panel/dock creation.

This module MUST NOT:

    - create MainWindow;
    - create application services;
    - create panels;
    - register panels;
    - decide workspace policy;
    - modify Core state;
    - contain electrical semantics;
    - directly call QMainWindow.addDockWidget();
    - directly call QMainWindow.tabifyDockWidget();
    - directly manipulate dock placement outside MainWindow.

Qt imports are permitted only through ui.core.qt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ui.core.qt import QDockWidget, Qt

from .panel_area import PanelArea
from .workspace_layout import WorkspaceLayout


# ============================================================
# Exceptions
# ============================================================


class WorkspaceRealizationError(RuntimeError):
    """Raised when a logical workspace cannot be realized."""


# ============================================================
# Runtime Dock Binding
# ============================================================


@dataclass(frozen=True, slots=True)
class DockBinding:
    """
    Associate a GridForge panel ID with an existing QDockWidget.

    The dock widget is created and owned by the panel composition
    layer. WorkspaceRealizer only retains the runtime association
    required for layout realization.
    """

    panel_id: str
    dock_widget: QDockWidget

    def __post_init__(self) -> None:
        if not isinstance(
            self.panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        if not self.panel_id.strip():
            raise ValueError(
                "panel_id must not be empty."
            )

        if not isinstance(
            self.dock_widget,
            QDockWidget,
        ):
            raise TypeError(
                "dock_widget must be a QDockWidget."
            )


# ============================================================
# WorkspaceRealizer
# ============================================================


class WorkspaceRealizer:
    """
    Realize a logical WorkspaceLayout through MainWindow.

    The realizer contains no workspace policy. It only translates
    already-decided logical placement into host operations.
    """

    def __init__(
        self,
        *,
        main_window,
    ) -> None:
        """
        Construct a WorkspaceRealizer.

        Parameters
        ----------
        main_window:
            Existing GridForge MainWindow host.
        """

        if main_window is None:
            raise ValueError(
                "WorkspaceRealizer requires an explicit MainWindow."
            )

        self._main_window = main_window

        self._bindings: dict[
            str,
            DockBinding,
        ] = {}

        self._realized_layout: WorkspaceLayout | None = None

    # ========================================================
    # Properties
    # ========================================================

    @property
    def main_window(self):
        """Return the explicitly supplied MainWindow host."""

        return self._main_window

    @property
    def bindings(
        self,
    ) -> Mapping[str, DockBinding]:
        """
        Return a snapshot of current runtime bindings.

        The returned mapping cannot mutate the internal registry.
        """

        return dict(
            self._bindings
        )

    @property
    def realized_layout(
        self,
    ) -> WorkspaceLayout | None:
        """
        Return the last successfully realized layout.
        """

        return self._realized_layout

    # ========================================================
    # Dock Registration
    # ========================================================

    def register_dock(
        self,
        *,
        panel_id: str,
        dock_widget: QDockWidget,
        replace: bool = False,
    ) -> None:
        """
        Register an already-created dock widget.

        WorkspaceRealizer does not create or own the dock.
        """

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        if not panel_id.strip():
            raise ValueError(
                "panel_id must not be empty."
            )

        if not isinstance(
            dock_widget,
            QDockWidget,
        ):
            raise TypeError(
                "dock_widget must be a QDockWidget."
            )

        if (
            panel_id in self._bindings
            and not replace
        ):
            raise ValueError(
                f"Dock already registered for panel: "
                f"{panel_id!r}"
            )

        self._bindings[
            panel_id
        ] = DockBinding(
            panel_id=panel_id,
            dock_widget=dock_widget,
        )

    def unregister_dock(
        self,
        panel_id: str,
    ) -> DockBinding | None:
        """
        Remove a runtime binding.

        The dock widget itself is not destroyed.
        """

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        return self._bindings.pop(
            panel_id,
            None,
        )

    def get_dock(
        self,
        panel_id: str,
    ) -> QDockWidget | None:
        """
        Return the dock registered for a panel.
        """

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        binding = self._bindings.get(
            panel_id
        )

        if binding is None:
            return None

        return binding.dock_widget

    # ========================================================
    # Logical Area -> Qt Area
    # ========================================================

    @staticmethod
    def _qt_area(
        area: PanelArea,
    ) -> Qt.DockWidgetArea:
        """
        Translate a GridForge logical dock area into Qt.

        CENTER and FLOATING do not map to a standard Qt
        DockWidgetArea.
        """

        if not isinstance(
            area,
            PanelArea,
        ):
            raise TypeError(
                "area must be a PanelArea."
            )

        mapping = {
            PanelArea.LEFT: Qt.LeftDockWidgetArea,
            PanelArea.RIGHT: Qt.RightDockWidgetArea,
            PanelArea.TOP: Qt.TopDockWidgetArea,
            PanelArea.BOTTOM: Qt.BottomDockWidgetArea,
        }

        try:
            return mapping[area]
        except KeyError as exc:
            raise WorkspaceRealizationError(
                f"PanelArea {area.value!r} is not a standard "
                "Qt dock area."
            ) from exc

    # ========================================================
    # Validation
    # ========================================================

    def _validate_layout(
        self,
        layout: WorkspaceLayout,
    ) -> None:
        """
        Validate runtime resources required by the layout.

        CENTER placements do not require a dock binding because
        CENTER represents the central editor/SLD host.

        All other placements require a registered dock.
        """

        if not isinstance(
            layout,
            WorkspaceLayout,
        ):
            raise TypeError(
                "layout must be a WorkspaceLayout."
            )

        missing: list[str] = []

        for placement in layout.placements:
            if placement.area == PanelArea.CENTER:
                continue

            if placement.panel_id not in self._bindings:
                missing.append(
                    placement.panel_id
                )

        if missing:
            raise WorkspaceRealizationError(
                "Workspace layout references panels without "
                f"registered docks: {missing!r}"
            )

    # ========================================================
    # Realization
    # ========================================================

    def realize(
        self,
        layout: WorkspaceLayout,
    ) -> None:
        """
        Realize the supplied logical workspace layout.

        WorkspaceLayout owns the decision.
        WorkspaceRealizer translates it.
        MainWindow performs the Qt operations.

        _realized_layout is updated only after every realization
        operation succeeds.
        """

        self._validate_layout(
            layout
        )

        active_ids = {
            placement.panel_id
            for placement in layout.placements
        }

        # ----------------------------------------------------
        # Remove docks no longer present in the logical layout.
        #
        # The runtime binding is retained because the dock
        # remains owned by the panel composition layer.
        # ----------------------------------------------------

        for panel_id, binding in tuple(
            self._bindings.items()
        ):
            if panel_id not in active_ids:
                self._main_window.remove_dock_widget(
                    binding.dock_widget
                )

        # ----------------------------------------------------
        # Realize placements.
        # ----------------------------------------------------

        for placement in layout.placements:
            binding = self._bindings.get(
                placement.panel_id
            )

            # ------------------------------------------------
            # CENTER
            # ------------------------------------------------

            if placement.area == PanelArea.CENTER:
                if binding is not None:
                    self._main_window.set_dock_visible(
                        binding.dock_widget,
                        placement.visible,
                    )

                continue

            # ------------------------------------------------
            # Non-CENTER placements require a dock.
            # ------------------------------------------------

            if binding is None:
                raise WorkspaceRealizationError(
                    "No registered dock for panel "
                    f"{placement.panel_id!r}."
                )

            dock = binding.dock_widget

            # ------------------------------------------------
            # Visibility is always explicitly realized.
            # ------------------------------------------------

            self._main_window.set_dock_visible(
                dock,
                placement.visible,
            )

            # ------------------------------------------------
            # Hidden docks require no placement operation.
            # ------------------------------------------------

            if not placement.visible:
                continue

            # ------------------------------------------------
            # FLOATING
            # ------------------------------------------------

            if placement.area == PanelArea.FLOATING:
                self._main_window.set_dock_floating(
                    dock,
                    True,
                )
                continue

            # ------------------------------------------------
            # Normal dock placement.
            # ------------------------------------------------

            qt_area = self._qt_area(
                placement.area
            )

            self._main_window.add_dock_widget(
                qt_area,
                dock,
            )

            self._main_window.set_dock_floating(
                dock,
                False,
            )

        # ----------------------------------------------------
        # Realize logical tab groups.
        # ----------------------------------------------------

        self._realize_tab_groups(
            layout
        )

        # ----------------------------------------------------
        # Commit the realized-layout marker only after every
        # host operation has succeeded.
        # ----------------------------------------------------

        self._realized_layout = layout

    # ========================================================
    # Tab Groups
    # ========================================================

    def _realize_tab_groups(
        self,
        layout: WorkspaceLayout,
    ) -> None:
        """
        Realize logical workspace tab groups.

        WorkspaceLayout decides group membership.

        MainWindow performs the actual tabification operation.
        """

        groups: dict[
            str,
            list[str],
        ] = {}

        for placement in layout.visible_panels():
            if placement.group is None:
                continue

            if placement.area in (
                PanelArea.CENTER,
                PanelArea.FLOATING,
            ):
                continue

            groups.setdefault(
                placement.group,
                [],
            ).append(
                placement.panel_id
            )

        for panel_ids in groups.values():
            if len(panel_ids) < 2:
                continue

            first_dock = self.get_dock(
                panel_ids[0]
            )

            if first_dock is None:
                raise WorkspaceRealizationError(
                    "Missing dock for tab group panel "
                    f"{panel_ids[0]!r}."
                )

            for panel_id in panel_ids[1:]:
                second_dock = self.get_dock(
                    panel_id
                )

                if second_dock is None:
                    raise WorkspaceRealizationError(
                        "Missing dock for tab group panel "
                        f"{panel_id!r}."
                    )

                self._main_window.tabify_dock_widgets(
                    first_dock,
                    second_dock,
                )

    # ========================================================
    # Clear
    # ========================================================

    def clear_realization(
        self,
    ) -> None:
        """
        Remove currently realized docks from MainWindow.

        Runtime dock objects remain owned by their creator.

        Dock bindings are deliberately retained because they
        represent panel-to-dock associations, not ownership.
        """

        for binding in tuple(
            self._bindings.values()
        ):
            self._main_window.remove_dock_widget(
                binding.dock_widget
            )

        self._realized_layout = None


# ============================================================
# Public API
# ============================================================

__all__ = [
    "DockBinding",
    "WorkspaceRealizationError",
    "WorkspaceRealizer",
]
```
