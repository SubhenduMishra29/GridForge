from __future__ import annotations

from typing import Any

from core.application.events import ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged, ProjectClosed, ProjectLoaded, TopologyChanged


class ElementListProjection:
    event_types = (ElementCreated, ElementUpdated, ElementRemoved, NetworkChanged, TopologyChanged, ProjectLoaded, ProjectClosed)

    def __init__(self, *, application: Any, panel: Any) -> None:
        self._application = application
        self._panel = panel
        self._disposed = False
        self._rows = ()

    @property
    def rows(self):
        return self._rows

    def refresh(self, event: Any) -> None:
        if self._disposed:
            return
        if isinstance(event, ProjectClosed):
            self._rows = ()
        else:
            network = self._application.read_network()
            self._rows = tuple({
                "id": str(element.object_id),
                "type": str(element.element_type),
                "name": str(next(iter(getattr(element, "labels", {}).values()), element.element_type)),
            } for element in getattr(network, "elements", ()))
        self._panel.set_rows(self._rows)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._panel.set_rows(())
        self._rows = ()
        self._disposed = True


__all__ = ["ElementListProjection"]
