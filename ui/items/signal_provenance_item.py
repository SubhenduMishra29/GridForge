"""Interactive read-only signal provenance label used by engineering canvases."""

from __future__ import annotations

from collections.abc import Callable

from ui.core.qt import QGraphicsTextItem


class SignalProvenanceItem(QGraphicsTextItem):
    """Hoverable provenance label; double-click navigates to one unambiguous peer."""

    def __init__(
        self,
        text: str,
        detail: str,
        *,
        target_editor: str | None = None,
        target_object_id: str | None = None,
        navigate: Callable[[str, str], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(str(text), parent)
        self._target_editor = target_editor
        self._target_object_id = target_object_id
        self._navigate = navigate
        self.setToolTip(str(detail))

    def mouseDoubleClickEvent(self, event) -> None:
        if (
            self._target_editor
            and self._target_object_id
            and callable(self._navigate)
        ):
            self._navigate(self._target_editor, self._target_object_id)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


__all__ = ["SignalProvenanceItem"]
