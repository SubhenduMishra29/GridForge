# ============================================================
# GridForge V2 — SLD Document Tabs
# ============================================================
"""Presentation-only SLD document tab strip.

The tab strip never owns SLD documents. It displays the canonical
ProjectWorkspaceLifecycle/DocumentManager registry and emits user intent
through injected callbacks.
"""

from __future__ import annotations

from typing import Any, Callable

from ui.core.qt import QHBoxLayout, QTabBar, QToolButton, QWidget


class SLDDocumentTabs(QWidget):
    """Dedicated SLD document-tab presentation over the canonical registry."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._document_manager: Any | None = None
        self._activate_callback: Callable[[str], Any] | None = None
        self._new_callback: Callable[[], Any] | None = None
        self._close_callback: Callable[[str], Any] | None = None
        self._reordering = False

        self._tabs = QTabBar(self)
        self._tabs.setMovable(True)
        self._tabs.setTabsClosable(True)
        self._tabs.setDocumentMode(True)
        self._tabs.tabBarClicked.connect(self._on_tab_clicked)
        self._tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        self._tabs.tabMoved.connect(self._on_tab_moved)

        self._new_button = QToolButton(self)
        self._new_button.setText("+")
        self._new_button.setToolTip("New SLD Document")
        self._new_button.setAutoRaise(True)
        self._new_button.clicked.connect(self._on_new_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        layout.addWidget(self._tabs, 1)
        layout.addWidget(self._new_button, 0)

        self.setObjectName("SLDDocumentTabs")

    @property
    def tab_bar(self) -> QTabBar:
        return self._tabs

    def bind(
        self,
        document_manager: Any,
        *,
        activate: Callable[[str], Any],
        new_document: Callable[[], Any],
        close_document: Callable[[str], Any],
    ) -> None:
        if document_manager is None:
            raise TypeError("document_manager is required.")
        for callback in (activate, new_document, close_document):
            if not callable(callback):
                raise TypeError("SLD document tab callbacks must be callable.")
        self._document_manager = document_manager
        self._activate_callback = activate
        self._new_callback = new_document
        self._close_callback = close_document
        self.refresh()

    def refresh(self) -> None:
        manager = self._document_manager
        if manager is None:
            self._tabs.clear()
            return
        active_id = getattr(manager, "active_document_id", None)
        documents = tuple(manager.documents())
        self._reordering = True
        try:
            self._tabs.blockSignals(True)
            self._tabs.clear()
            for document in documents:
                label = str(getattr(document, "name", "Untitled SLD"))
                if bool(getattr(manager, "is_dirty", lambda *_: False)(document.document_id)):
                    label += " *"
                index = self._tabs.addTab(label)
                self._tabs.setTabData(index, str(document.document_id))
                self._tabs.setTabToolTip(index, str(document.document_id))
                if document.document_id == active_id:
                    self._tabs.setCurrentIndex(index)
        finally:
            self._tabs.blockSignals(False)
            self._reordering = False

    def _document_id_at(self, index: int) -> str | None:
        data = self._tabs.tabData(index)
        return str(data) if data is not None else None

    def _on_tab_clicked(self, index: int) -> None:
        if self._reordering:
            return
        document_id = self._document_id_at(index)
        if document_id is not None and self._activate_callback is not None:
            self._activate_callback(document_id)

    def _on_new_clicked(self) -> None:
        if self._new_callback is not None:
            self._new_callback()

    def _on_tab_close_requested(self, index: int) -> None:
        document_id = self._document_id_at(index)
        if document_id is not None and self._close_callback is not None:
            self._close_callback(document_id)

    def _on_tab_moved(self, from_index: int, to_index: int) -> None:
        if self._reordering or self._document_manager is None:
            return
        document_id = self._document_id_at(to_index)
        if document_id is None:
            return
        self._document_manager.move(document_id, to_index)
        self.refresh()


__all__ = ["SLDDocumentTabs"]
