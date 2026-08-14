# ============================================================
# File: ui/panels/results_panel.py
# GridForge V2 — Results Panel
# ============================================================

"""
GridForge V2 — Results Panel
============================

Displays analysis and simulation results supplied by the
application layer.

Responsibilities
----------------
ResultsPanel:

    - display result records supplied by the application;
    - replace the current result set;
    - clear displayed results;
    - expose the currently displayed results;
    - provide basic diagnostic state.

ResultsPanel does NOT:

    - execute simulations;
    - execute power-flow or short-circuit analysis;
    - own solver state;
    - calculate electrical quantities;
    - modify the Core model;
    - create commands;
    - access the filesystem;
    - become the authoritative source of analysis results.

Architecture
------------

    Analysis / Simulation / Controller
                │
                ▼
          ResultsPanel
                │
                ▼
         Presentation only

The authoritative result data remains owned by the
application/analysis layer.

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


class ResultsPanel(QWidget):
    """
    Presentation-only panel for displaying analysis or
    simulation results.

    The panel intentionally accepts already-produced result
    information. It does not interpret or calculate results.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the ResultsPanel.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # Current result records.
        #
        # This is only a presentation snapshot. The authoritative
        # result remains outside the panel.
        # ----------------------------------------------------

        self._results: list[Any] = []

        # ----------------------------------------------------
        # Header.
        # ----------------------------------------------------

        self._title = QLabel(
            "Results",
            self,
        )

        # ----------------------------------------------------
        # Result list.
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
    # RESULT DATA
    # ========================================================

    def set_results(
        self,
        results: Iterable[Any],
    ) -> None:
        """
        Replace the displayed result set.

        Parameters
        ----------
        results:
            Iterable containing already-produced result records.

        Notes
        -----
        Results are converted to display strings only for the
        visual list. No analysis or interpretation is performed.
        """

        if results is None:
            raise ValueError(
                "results must not be None."
            )

        result_list = list(
            results
        )

        self._results = result_list

        self.list.clear()

        for result in result_list:
            self.list.addItem(
                self._format_result(
                    result
                )
            )

    # ========================================================
    # RESULT FORMATTING
    # ========================================================

    @staticmethod
    def _format_result(
        result: Any,
    ) -> str:
        """
        Convert one supplied result record to display text.

        Mapping results are rendered as a compact key/value
        representation. Other result objects use their string
        representation.

        No domain-specific interpretation is performed.
        """

        if result is None:
            return "—"

        if isinstance(
            result,
            Mapping,
        ):
            return ", ".join(
                f"{key}: {value}"
                for key, value
                in result.items()
            )

        return str(
            result
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear all displayed results.
        """

        self._results.clear()

        self.list.clear()

    # ========================================================
    # RESULT ACCESS
    # ========================================================

    def get_results(
        self,
    ) -> list[Any]:
        """
        Return a detached copy of the currently supplied results.

        The returned list can be modified without changing the
        panel's internal result collection.
        """

        return list(
            self._results
        )

    # ========================================================
    # RESULT COUNT
    # ========================================================

    def get_result_count(
        self,
    ) -> int:
        """
        Return the number of supplied result records.
        """

        return len(
            self._results
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
            "result_count": len(
                self._results
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
            "ResultsPanel("
            f"results={len(self._results)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ResultsPanel",
]
