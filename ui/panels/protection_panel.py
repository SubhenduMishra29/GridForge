# ============================================================
# File: ui/panels/protection_panel.py
# GridForge V2 — Protection Panel
# ============================================================

"""
GridForge V2 — Protection Panel
================================

Displays protection-system information supplied by the
application layer.

Responsibilities
----------------
ProtectionPanel:

    - display protection elements and relay information;
    - display protection status or diagnostic records;
    - replace the displayed protection collection;
    - clear displayed protection information;
    - expose the currently displayed records;
    - provide basic diagnostic state.

ProtectionPanel does NOT:

    - execute protection functions;
    - perform relay calculations;
    - perform relay coordination;
    - calculate fault currents;
    - operate circuit breakers directly;
    - modify Core protection objects;
    - create commands;
    - own protection state;
    - perform simulation;
    - access the filesystem.

Architecture
------------

    Protection / Controller / Application Layer
                       │
                       ▼
                ProtectionPanel
                       │
                       ▼
                  Presentation

The Core protection subsystem remains authoritative.

Any future protection-setting modification or control action
must pass through the appropriate Controller/Command boundary.

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


class ProtectionPanel(QWidget):
    """
    Presentation-only protection-system browser.

    Protection information is supplied by the application layer.
    The panel does not execute or mutate protection logic.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the ProtectionPanel.

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
        # This is not authoritative protection state.
        # ----------------------------------------------------

        self._protection_items: list[Any] = []

        # ----------------------------------------------------
        # Header.
        # ----------------------------------------------------

        self._title = QLabel(
            "Protection",
            self,
        )

        # ----------------------------------------------------
        # Protection information list.
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
    # PROTECTION DATA
    # ========================================================

    def set_protection(
        self,
        items: Iterable[Any],
    ) -> None:
        """
        Replace the displayed protection information.

        Parameters
        ----------
        items:
            Iterable containing protection records supplied by
            the application layer.

        Notes
        -----
        The supplied records are displayed only. No protection
        calculation or state mutation is performed.
        """

        if items is None:
            raise ValueError(
                "items must not be None."
            )

        protection_items = list(
            items
        )

        self._protection_items = protection_items

        self.list.clear()

        for item in protection_items:
            self.list.addItem(
                self._format_item(
                    item
                )
            )

    # ========================================================
    # PROTECTION FORMATTING
    # ========================================================

    @staticmethod
    def _format_item(
        item: Any,
    ) -> str:
        """
        Convert one protection record to display text.

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
        Clear all displayed protection information.
        """

        self._protection_items.clear()

        self.list.clear()

    # ========================================================
    # PROTECTION ACCESS
    # ========================================================

    def get_protection(
        self,
    ) -> list[Any]:
        """
        Return a detached copy of the currently supplied
        protection records.
        """

        return list(
            self._protection_items
        )

    # ========================================================
    # ITEM COUNT
    # ========================================================

    def get_item_count(
        self,
    ) -> int:
        """
        Return the number of supplied protection records.
        """

        return len(
            self._protection_items
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
                self._protection_items
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
            "ProtectionPanel("
            f"items={len(self._protection_items)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ProtectionPanel",
]
