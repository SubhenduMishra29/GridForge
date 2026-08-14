# ============================================================
# File: ui/panels/equipment_panel.py
# GridForge V2 — Equipment Panel
# ============================================================

"""
GridForge V2 — Equipment Panel
==============================

Displays electrical equipment supplied by the application layer.

Responsibilities
----------------
EquipmentPanel:

    - display equipment records;
    - replace the displayed equipment collection;
    - clear displayed equipment;
    - expose the currently displayed equipment;
    - provide basic diagnostic state.

EquipmentPanel does NOT:

    - create Core equipment objects;
    - modify Core equipment;
    - perform electrical calculations;
    - create commands;
    - perform equipment control;
    - perform simulation;
    - perform rendering;
    - access the filesystem;
    - become the authoritative equipment store.

Architecture
------------

    Core / Controller / Application Layer
                    │
                    ▼
             EquipmentPanel
                    │
                    ▼
              Presentation

The Core model remains authoritative.

The panel stores only a presentation snapshot of the
equipment supplied to it.

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


class EquipmentPanel(QWidget):
    """
    Presentation-only equipment browser.

    Equipment records are supplied by the application/controller
    layer. The panel does not interpret or mutate the underlying
    Core objects.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the EquipmentPanel.

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
        # These references are not authoritative application
        # state.
        # ----------------------------------------------------

        self._equipment: list[Any] = []

        # ----------------------------------------------------
        # Header.
        # ----------------------------------------------------

        self._title = QLabel(
            "Equipment",
            self,
        )

        # ----------------------------------------------------
        # Equipment list.
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
    # EQUIPMENT DATA
    # ========================================================

    def set_equipment(
        self,
        equipment: Iterable[Any],
    ) -> None:
        """
        Replace the displayed equipment collection.

        Parameters
        ----------
        equipment:
            Iterable containing equipment records or Core model
            objects supplied by the application layer.

        Notes
        -----
        The panel does not create or modify the supplied objects.
        """

        if equipment is None:
            raise ValueError(
                "equipment must not be None."
            )

        equipment_list = list(
            equipment
        )

        self._equipment = equipment_list

        self.list.clear()

        for item in equipment_list:
            self.list.addItem(
                self._format_equipment(
                    item
                )
            )

    # ========================================================
    # EQUIPMENT FORMATTING
    # ========================================================

    @staticmethod
    def _format_equipment(
        equipment: Any,
    ) -> str:
        """
        Convert one equipment record to display text.

        Formatting is intentionally generic.

        Mapping records are displayed as key/value pairs.

        Objects may optionally expose a public ``name`` or
        ``id`` attribute. No arbitrary attribute dumping is
        performed.
        """

        if equipment is None:
            return "—"

        if isinstance(
            equipment,
            Mapping,
        ):
            return ", ".join(
                f"{key}: {value}"
                for key, value
                in equipment.items()
            )

        name = getattr(
            equipment,
            "name",
            None,
        )

        if name is not None:
            return str(
                name
            )

        equipment_id = getattr(
            equipment,
            "id",
            None,
        )

        if equipment_id is not None:
            return str(
                equipment_id
            )

        return str(
            equipment
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear all displayed equipment.
        """

        self._equipment.clear()

        self.list.clear()

    # ========================================================
    # EQUIPMENT ACCESS
    # ========================================================

    def get_equipment(
        self,
    ) -> list[Any]:
        """
        Return a detached copy of the currently supplied
        equipment collection.
        """

        return list(
            self._equipment
        )

    # ========================================================
    # EQUIPMENT COUNT
    # ========================================================

    def get_equipment_count(
        self,
    ) -> int:
        """
        Return the number of supplied equipment records.
        """

        return len(
            self._equipment
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
            "equipment_count": len(
                self._equipment
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
            "EquipmentPanel("
            f"equipment={len(self._equipment)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "EquipmentPanel",
]
