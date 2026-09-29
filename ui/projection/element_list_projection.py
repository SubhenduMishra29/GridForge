# ============================================================
# GridForge V2 — Element List Projection
# ============================================================
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Any

from core.application.events import (
    ElementCreated,
    ElementRemoved,
    ElementUpdated,
    NetworkChanged,
    ProjectClosed,
    ProjectLoaded,
    TopologyChanged,
)


class ElementListProjection:
    """Project the Application network read model into the Element List panel."""

    event_types = (
        ElementCreated,
        ElementUpdated,
        ElementRemoved,
        NetworkChanged,
        TopologyChanged,
        ProjectLoaded,
        ProjectClosed,
    )

    def __init__(self, *, application: Any, panel: Any) -> None:
        if application is None or not callable(getattr(application, "read_network", None)):
            raise TypeError("application must provide read_network().")
        if panel is None or not callable(getattr(panel, "set_rows", None)):
            raise TypeError("panel must provide set_rows().")
        self._application = application
        self._panel = panel
        self._disposed = False
        self._rows: tuple[dict[str, str], ...] = ()

    @property
    def rows(self) -> tuple[dict[str, str], ...]:
        return self._rows

    def refresh(self, event: Any) -> None:
        if self._disposed:
            return
        if isinstance(event, ProjectClosed):
            self._rows = ()
        else:
            network = self._application.read_network()
            self._rows = tuple(self._row(element) for element in getattr(network, "elements", ()))
        self._panel.set_rows(self._rows)

    @staticmethod
    def _row(element: Any) -> dict[str, str]:
        labels = getattr(element, "labels", {})
        name = labels.get("name") if hasattr(labels, "get") else None
        if name is None or not str(name).strip():
            name = labels.get("type") if hasattr(labels, "get") else None
        if name is None or not str(name).strip():
            name = getattr(element, "element_type", "element")
        attributes = getattr(element, "attributes", {})
        nominal_voltage = None
        status = None
        in_service = None
        if hasattr(attributes, "get"):
            nominal_voltage = attributes.get("nominal_voltage", attributes.get("nominalVoltage"))
            status = attributes.get("status")
            in_service = attributes.get("in_service")
        if nominal_voltage is None and hasattr(labels, "get"):
            nominal_voltage = labels.get("nominal_voltage", labels.get("nominalVoltage"))
        if status is None and hasattr(labels, "get"):
            status = labels.get("status")
        if status is None and in_service is not None:
            status = "In Service" if bool(in_service) else "Out of Service"
        return {
            "id": str(element.object_id),
            "type": str(element.element_type),
            "name": str(name),
            "nominal_voltage": "" if nominal_voltage is None else str(nominal_voltage),
            "status": "Unknown" if status is None else str(status),
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        self._panel.set_rows(())
        self._rows = ()
        self._disposed = True


__all__ = ["ElementListProjection"]
