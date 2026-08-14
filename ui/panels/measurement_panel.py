# ============================================================
# File: ui/panels/measurement_panel.py
# GridForge V2 — Measurement Panel
# ============================================================
"""
Measurement infrastructure panel for the GridForge UI.

Responsibilities
----------------
MeasurementPanel is a presentation-only widget for displaying
measurement infrastructure associated with the GridForge model.

It is responsible for:

    - displaying measurement points/channels supplied by the
      application layer;
    - replacing the displayed measurement list;
    - clearing the displayed list;
    - exposing the currently displayed measurements;
    - providing basic diagnostic state.

MeasurementPanel does NOT:

    - create MeasurementPoint objects;
    - create MeasurementChannel objects;
    - perform electrical measurements;
    - calculate measurement values;
    - modify the Core model;
    - own measurement infrastructure;
    - manage relays or protection logic;
    - perform simulation;
    - perform persistence;
    - perform filesystem operations.

Architecture
------------

    Core Measurement Domain
            │
            ▼
      Controller / UI Layer
            │
            ▼
      MeasurementPanel
            │
            ▼
       Presentation only

The authoritative measurement infrastructure remains in:

    core/measurement/

MeasurementPanel only presents information supplied by the
application/controller layer.

Qt Architecture
---------------

All Qt classes must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ui.core.qt import (
    QListWidget,
    QVBoxLayout,
    QWidget,
)


class MeasurementPanel(QWidget):
    """
    Presentation-only panel for measurement infrastructure.

    The panel deliberately does not depend on concrete Core
    measurement classes. The Controller/application layer may
    provide whatever presentation representation is appropriate.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the measurement panel.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # Measurement list.
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
            self.list
        )

    # ========================================================
    # MEASUREMENT DATA
    # ========================================================

    def set_measurements(
        self,
        measurements: Iterable[Any],
    ) -> None:
        """
        Replace the displayed measurement entries.

        Parameters
        ----------
        measurements:
            Iterable containing presentation values for
            measurement points/channels.

        Notes
        -----
        The supplied objects are converted to display strings.
        This method does not modify the supplied objects or the
        Core measurement domain.
        """

        if measurements is None:
            raise ValueError(
                "measurements must not be None."
            )

        self.list.clear()

        self.list.addItems(
            [
                str(measurement)
                for measurement in measurements
            ]
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all displayed measurement entries.
        """

        self.list.clear()

    # ========================================================
    # ACCESS
    # ========================================================

    def get_measurements(
        self,
    ) -> list[str]:
        """
        Return the currently displayed measurement entries.
        """

        return [
            self.list.item(index).text()
            for index in range(
                self.list.count()
            )
        ]

    # ========================================================
    # COUNT
    # ========================================================

    def get_measurement_count(
        self,
    ) -> int:
        """
        Return the number of displayed measurement entries.
        """

        return self.list.count()

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
            "measurement_count": (
                self.list.count()
            ),
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
            "MeasurementPanel("
            f"measurements={self.list.count()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "MeasurementPanel",
]
