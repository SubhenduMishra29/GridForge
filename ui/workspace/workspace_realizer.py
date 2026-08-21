# ============================================================
# File: ui/workspace/workspace_realizer.py
# GridForge V2 — Workspace Qt Realizer
# ============================================================

"""
GridForge V2
============

Workspace/Layout → Qt realization boundary.

Architectural Role
------------------
WorkspaceRealizer translates the logical GridForge Workspace/Layout
model into Qt presentation operations exposed by MainWindow.

It is intentionally NOT a workspace-policy component.

WorkspaceManager owns:
    - workspace definitions
    - active workspace state
    - logical panel placement
    - workspace composition policy

WorkspaceRealizer owns:
    - translating PanelArea to Qt dock areas
    - realizing logical dock placement
    - realizing logical tab groups
    - realizing logical visibility
    - removing/replacing obsolete dock widgets

MainWindow owns:
    - QMainWindow
    - Qt docking infrastructure
    - the actual Qt operations

WorkspaceRealizer does NOT:
    - create application-owned services
    - create panels
    - register panels
    - modify Core state
    - decide workspace policy
    - define electrical semantics
    - instantiate QMainWindow
    - directly call QMainWindow.addDockWidget()
    - directly call QMainWindow.tabifyDockWidget()

All Qt workspace operations are routed through the explicit
MainWindow host boundary.

Dependency Direction
--------------------

    WorkspaceManager
          │
          ▼
    WorkspaceLayout
          │
          ▼
    WorkspaceRealizer
          │
          ▼
    MainWindow
          │
          ▼
         Qt
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
    """
    Raised when a logical workspace cannot be realized.
    """


# ============================================================
# Runtime Dock Binding
# ============================================================


@dataclass(frozen=True, slots=True)
class DockBinding:
    """
    Runtime association between a GridForge panel ID and its
    Qt dock widget.

    This is realization state.

    It is deliberately separate from WorkspaceLayout because
    WorkspaceLayout must remain Qt-independent.
    """

    panel_id: str
    dock_widget: QDockWidget

    def __post_init__(self) -> None:
        if not isinstance(self.panel_id, str):
            raise TypeError(
                "panel_id must be a string."
            )

        if not self.panel_id.strip():
            raise ValueError(
                "panel_id must not be empty."
            )

        if self.dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )


# ============================================================
# WorkspaceRealizer
# ============================================================


class WorkspaceRealizer:
    """
    Realizes a logical WorkspaceLayout through MainWindow's
    explicit Qt workspace-host interface.

    MainWindow is supplied explicitly.

    No MainWindow is created internally.
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
            Existing GridForge MainWindow.

        Raises
        ------
        ValueError
            If main_window is not supplied.
        """

        if main_window is None:
            raise ValueError(
                "WorkspaceRealizer requires an explicit "
                "MainWindow."
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
        """
        Return the explicitly supplied MainWindow host.
        """

        return self._main_window

    # --------------------------------------------------------

    @property
    def bindings(
        self,
    ) -> Mapping[str, DockBinding]:
        """
        Return the current immutable view of dock bindings.
        """

        return dict(self._bindings)

    # --------------------------------------------------------

    @property
    def realized_layout(
        self,
    ) -> WorkspaceLayout | None:
        """
        Return the last successfully realized layout.
        """

        return self._realized_layout

    # ========================================================
    # Registration of Runtime Dock Objects
    # ========================================================

    def register_dock(
        self,
        *,
        panel_id: str,
        dock_widget: QDockWidget,
        replace: bool = False,
    ) -> None:
        """
        Register an already-created QDockWidget.

        WorkspaceRealizer does NOT create the dock widget.

        Panel creation remains the responsibility of the panel
        composition layer.
        """

        if not isinstance(panel_id, str):
            raise TypeError(
                "panel_id must be a string."
            )

        if not panel_id.strip():
            raise ValueError(
                "panel_id must not be empty."
            )

        if dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )

        if (
            panel_id in self._bindings
            and not replace
        ):
            raise ValueError(
                f"Dock already registered for panel: "
                f"{panel_id!r}"
            )

        self._bindings[panel_id] = DockBinding(
            panel_id=panel_id,
            dock_widget=dock_widget,
        )

    # --------------------------------------------------------

    def unregister_dock(
        self,
        panel_id: str,
    ) -> DockBinding | None:
        """
        Remove a runtime dock binding.

        This does not destroy the QWidget.
        """

        return self._bindings.pop(
            panel_id,
            None,
        )

    # --------------------------------------------------------

    def get_dock(
        self,
        panel_id: str,
    ) -> QDockWidget | None:
        """
        Return the registered dock widget for a panel.
        """

        binding = self._bindings.get(
            panel_id
        )

        if binding is None:
            return None

        return binding.dock_widget

    # ========================================================
    # Logical Area → Qt Area
    # ========================================================

    @staticmethod
    def _qt_area(
        area: PanelArea,
    ) -> Qt.DockWidgetArea:
        """
        Translate a GridForge logical PanelArea into Qt's
        DockWidgetArea.

        This is the ONLY place where the logical area is
        translated into a Qt docking area.
        """

        if area == PanelArea.LEFT:
            return Qt.LeftDockWidgetArea

        if area == PanelArea.RIGHT:
            return Qt.RightDockWidgetArea

        if area == PanelArea.TOP:
            return Qt.TopDockWidgetArea

        if area == PanelArea.BOTTOM:
            return Qt.BottomDockWidgetArea

        if area == PanelArea.CENTER:
            raise WorkspaceRealizationError(
                "CENTER is not a Qt dock area. "
                "The center workspace is the primary editor "
                "region and must be hosted separately."
            )

        if area == PanelArea.FLOATING:
            raise WorkspaceRealizationError(
                "FLOATING is not a dock area. "
                "Floating realization requires explicit "
                "workspace presentation handling."
            )

        raise WorkspaceRealizationError(
            f"Unsupported PanelArea: {area!r}"
        )

    # ========================================================
    # Validation
    # ========================================================

    def _validate_layout(
        self,
        layout: WorkspaceLayout,
    ) -> None:
        """
        Validate that all visible logical placements have
        registered runtime docks.
        """

        if layout is None:
            raise ValueError(
                "layout must not be None."
            )

        missing: list[str] = []

        for placement in layout.visible_panels():
            if placement.area in (
                PanelArea.CENTER,
                PanelArea.FLOATING,
            ):
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
        Realize a logical WorkspaceLayout.

        The method applies only the presentation decisions already
        contained in the WorkspaceLayout.

        It does not modify the layout itself.
        """

        self._validate_layout(
            layout
        )

        # ----------------------------------------------------
        # 1. Remove docks no longer present in the layout.
        # ----------------------------------------------------

        active_ids = {
            placement.panel_id
            for placement in layout.placements
        }

        for panel_id, binding in tuple(
            self._bindings.items()
        ):
            if panel_id not in active_ids:
                self._main_window.remove_dock_widget(
                    binding.dock_widget
                )

        # ----------------------------------------------------
        # 2. Realize logical dock placement.
        # ----------------------------------------------------

        for placement in layout.placements:
            binding = self._bindings.get(
                placement.panel_id
            )

            if binding is None:
                # CENTER/FLOATING may be realized by another
                # editor/presentation subsystem later.
                if placement.area in (
                    PanelArea.CENTER,
                    PanelArea.FLOATING,
                ):
                    continue

                raise WorkspaceRealizationError(
                    "No dock registered for panel "
                    f"{placement.panel_id!r}."
                )

            dock = binding.dock_widget

            # ----------------------------------------------
            # Visibility belongs to WorkspaceLayout.
            # ----------------------------------------------

            dock.setVisible(
                placement.visible
            )

            # ----------------------------------------------
            # Floating is a presentation state.
            # ----------------------------------------------

            if placement.area == PanelArea.FLOATING:
                dock.setFloating(True)
                continue

            # ----------------------------------------------
            # Center is not a dock area.
            # ----------------------------------------------

            if placement.area == PanelArea.CENTER:
                continue

            # ----------------------------------------------
            # Normal dock placement.
            # ----------------------------------------------

            qt_area = self._qt_area(
                placement.area
            )

            self._main_window.add_dock_widget(
                qt_area,
                dock,
            )

        # ----------------------------------------------------
        # 3. Realize logical tab groups.
        # ----------------------------------------------------

        self._realize_tab_groups(
            layout
        )

        # ----------------------------------------------------
        # 4. Record successful realization.
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
        Realize WorkspacePlacement.group relationships.

        Group membership is workspace policy.

        This method merely translates that policy into the
        MainWindow Qt operation.
        """

        groups: dict[
            str,
            list[str],
        ] = {}

        for placement in layout.visible_panels():
            if placement.group is None:
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
    # Reset
    # ========================================================

    def clear_realization(
        self,
    ) -> None:
        """
        Remove all currently realized docks from MainWindow.

        Runtime dock objects remain owned by their creator.
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
