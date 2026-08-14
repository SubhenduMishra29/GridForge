# ============================================================
# File: ui/panels/network_panel.py
# GridForge V2 — Network Panel
# ============================================================

"""
GridForge V2 — Network Panel
============================

Displays network/topology information supplied by the
application layer.

Responsibilities
----------------
NetworkPanel:

    - display network elements or topology records;
    - replace the displayed network collection;
    - clear displayed network information;
    - expose the currently displayed records;
    - provide basic diagnostic state.

NetworkPanel does NOT:

    - own the authoritative Network;
    - modify Core topology;
    - create or delete network elements;
    - perform electrical calculations;
    - execute power-flow or short-circuit analysis;
    - create commands;
    - perform rendering;
    - manage canvas interaction;
    - access the filesystem.

Architecture
------------

    Core Network / Controller / Application Layer
                         │
                         ▼
                   NetworkPanel
                         │
                         ▼
                    Presentation

The Core network remains authoritative.

The panel stores only a presentation snapshot of the
network information supplied to it.

Qt Rule
-------
All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Optional

from ui.core.qt import (
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)


class NetworkPanel(QWidget):
    """
    Presentation-only network/topology browser.

    Network information is supplied by the application or
    controller layer. The panel does not mutate the underlying
    Core network.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the NetworkPanel.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # Presentation snapshot.
        #
        # This is not authoritative network state.
        # ----------------------------------------------------

        self._network_items: list[Any] = []

        # ----------------------------------------------------
        # Header.
        # ----------------------------------------------------

        self._title = QLabel(
            "Network",
            self,
        )

        # ----------------------------------------------------
        # Network list.
        # ----------------------------------------------------

        self.list = QListWidget(
            self
        )

        # ----------------------------------------------------
        # Layout.
        # ----------------------------------------------------

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            self._title
        )

        layout.addWidget(
            self.list
        )

    # ========================================================
    # NETWORK DATA
    # ========================================================

    def set_network(
        self,
        items: Iterable[Any],
    ) -> None:
        """
        Replace the displayed network information.

        Parameters
        ----------
        items:
            Iterable containing network/topology records supplied
            by the application layer.

        Notes
        -----
        No topology mutation or electrical calculation occurs.
        """

        if items is None:
            raise ValueError(
                "items must not be None."
            )

        network_items = list(
            items
        )

        self._network_items = network_items

        self.list.clear()

        for item in network_items:
            self.list.addItem(
                self._format_item(
                    item
                )
            )

    # ========================================================
    # NETWORK FORMATTING
    # ========================================================

    @staticmethod
    def _format_item(
        item: Any,
    ) -> str:
        """
        Convert one network record to display text.

        Mapping records are rendered as key/value pairs.

        Objects may optionally expose a public ``name`` or ``id``
        attribute.

        No arbitrary object attribute dumping is performed.
        """

        if item is None:
            return "—"

        if isinstance(
            item,
            Mapping,
        ):
            return ", ".join(
                f"{key}: {value}"
                for key, value
                in item.items()
            )

        name = getattr(
            item,
            "name",
            None,
        )

        if name is not None:
            return str(
                name
            )

        item_id = getattr(
            item,
            "id",
            None,
        )

        if item_id is not None:
            return str(
                item_id
            )

        return str(
            item
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear all displayed network information.
        """

        self._network_items.clear()

        self.list.clear()

    # ========================================================
    # NETWORK ACCESS
    # ========================================================

    def get_network(
        self,
    ) -> list[Any]:
        """
        Return a detached copy of the currently supplied network
        records.
        """

        return list(
            self._network_items
        )

    # ========================================================
    # ITEM COUNT
    # ========================================================

    def get_item_count(
        self,
    ) -> int:
        """
        Return the number of supplied network records.
        """

        return len(
            self._network_items
        )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic panel state.
        """

        return {
            "item_count": len(
                self._network_items
            ),
            "display_count": self.list.count(),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "NetworkPanel("
            f"items={len(self._network_items)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "NetworkPanel",
]
