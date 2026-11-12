"""Interactive read-only signal provenance label used by engineering canvases."""

from __future__ import annotations

from collections.abc import Callable

from ui.core.qt import QGraphicsTextItem, QMenu


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
        alternate_targets: tuple[tuple[str, str, str], ...] = (),
        parent=None,
    ) -> None:
        super().__init__(str(text), parent)
        self._target_editor = target_editor
        self._target_object_id = target_object_id
        self._navigate = navigate
        normalized_targets = tuple(
            (str(label).strip(), str(editor).strip().lower(), str(object_id).strip())
            for label, editor, object_id in alternate_targets
        )
        if any(not label or not editor or not object_id for label, editor, object_id in normalized_targets):
            raise ValueError("alternate provenance targets require label, editor and object ID.")
        self._alternate_targets = normalized_targets
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

    def contextMenuEvent(self, event) -> None:
        if self._alternate_targets and callable(self._navigate):
            menu = QMenu()
            for label, editor, object_id in self._alternate_targets:
                action = menu.addAction(label)
                action.triggered.connect(
                    lambda _checked=False, target_editor=editor, target_id=object_id:
                    self._navigate(target_editor, target_id)
                )
            menu.exec(event.screenPos())
            event.accept()
            return
        super().contextMenuEvent(event)


__all__ = ["SignalProvenanceItem"]
