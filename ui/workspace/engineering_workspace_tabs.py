# ============================================================
# File: ui/workspace/engineering_workspace_tabs.py
# GridForge V2 — Engineering Workspace Tabs
# Author: Subhendu Mishra
# ============================================================

"""Read-only engineering workspace projections sharing Application state.

These views are presentation projections only. They do not own Core,
topology, study, or SLD authority.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QLabel,
    QListWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class TopologyWorkspaceView(QWidget):
    """Project the Application NetworkReadModel as a topology inventory."""

    def __init__(self, application: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application
        self._table = QTableWidget(self)
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(("ID", "Type", "Connections", "Status"))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        self.refresh()

    def refresh(self) -> None:
        network = self._application.read_network()
        elements = tuple(network.elements)
        self._table.setRowCount(len(elements))
        for row, element in enumerate(elements):
            self._table.setItem(row, 0, QTableWidgetItem(str(element.object_id)))
            self._table.setItem(row, 1, QTableWidgetItem(str(element.element_type)))
            self._table.setItem(row, 2, QTableWidgetItem(", ".join(map(str, element.connectivity_refs))))
            status = element.attributes.get("in_service")
            self._table.setItem(row, 3, QTableWidgetItem(
                "In Service" if status is True else "Out of Service" if status is False else "Unknown"
            ))
        self._table.resizeColumnsToContents()


class MapWorkspaceView(QWidget):
    """Project persisted SLD geometry as a lightweight engineering map inventory."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._document: Any | None = None
        self._list = QListWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("SLD Geometry Map", self))
        layout.addWidget(self._list)
        self.set_document(None)

    def set_document(self, document: Any | None) -> None:
        self._document = document
        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        document = self._document
        if document is None:
            self._list.addItem("No SLD document is currently loaded.")
            return
        for node in document.model.nodes:
            position = getattr(node, "position", None)
            if position is None:
                self._list.addItem(f"{node.node_id} — position unavailable")
            else:
                self._list.addItem(
                    f"{node.equipment_id or node.node_id} — "
                    f"({getattr(position, 'x', 0):.1f}, {getattr(position, 'y', 0):.1f})"
                )


class ReportsWorkspaceView(QWidget):
    """Project published Application study results without creating a result authority."""

    def __init__(self, application: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application
        self._list = QListWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Study Reports", self))
        layout.addWidget(self._list)
        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        results = tuple(self._application.read_study_results())
        if not results:
            self._list.addItem("No published study results.")
            return
        for result in results:
            self._list.addItem(
                f"{result.study_type} — {result.status} — "
                f"{result.message or 'No message'}"
            )


class EngineeringWorkspaceTabs(QWidget):
    """Canonical presentation host for shared project-state workspace views."""

    def __init__(
        self,
        *,
        application: Any,
        surfaces: dict[str, QWidget],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not surfaces:
            raise ValueError("At least one engineering surface is required.")
        self._application = application
        self._surfaces = dict(surfaces)
        self._tabs = QTabWidget(self)
        self._tabs.setObjectName("EngineeringWorkspaceTabs")
        self._topology = TopologyWorkspaceView(application, self)
        self._map = MapWorkspaceView(self)
        self._reports = ReportsWorkspaceView(application, self)
        self._surfaces.update({
            "topology": self._topology,
            "map": self._map,
            "reports": self._reports,
        })
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)
        self._tab_by_id: dict[str, int] = {}
        for surface_id, widget in self._surfaces.items():
            self._tab_by_id[surface_id] = self._tabs.addTab(widget, self._title_for(surface_id))

    @staticmethod
    def _title_for(surface_id: str) -> str:
        return {
            "sld": "SLD",
            "topology": "Topology",
            "map": "Map",
            "reports": "Reports",
            "control": "Control",
            "protection": "Protection",
        }.get(surface_id, surface_id.replace("_", " ").title())

    @property
    def surface_ids(self) -> tuple[str, ...]:
        return tuple(self._surfaces)

    def activate(self, surface_id: str) -> None:
        if surface_id not in self._tab_by_id:
            raise KeyError(f"Unknown workspace surface: {surface_id!r}")
        self._tabs.setCurrentIndex(self._tab_by_id[surface_id])
        if surface_id == "topology":
            self._topology.refresh()
        elif surface_id == "reports":
            self._reports.refresh()
        elif surface_id == "map":
            self._map.refresh()

    def set_sld_document(self, document: Any | None) -> None:
        """Present the active SLD document on the canonical SLD editor surface."""
        sld_surface = self._surfaces.get("sld")
        if sld_surface is None:
            raise RuntimeError("The canonical SLD surface is not registered.")
        if document is None:
            clear = getattr(sld_surface, "clear_document", None)
            if not callable(clear):
                raise RuntimeError("The canonical SLD surface cannot clear its document.")
            clear()
        else:
            present = getattr(sld_surface, "present_document", None)
            if not callable(present):
                raise RuntimeError("The canonical SLD surface cannot present an SLD document.")
            present(document)
        # Map remains a secondary persisted-geometry projection only.
        self._map.set_document(document)


__all__ = [
    "EngineeringWorkspaceTabs",
    "MapWorkspaceView",
    "ReportsWorkspaceView",
    "TopologyWorkspaceView",
]
