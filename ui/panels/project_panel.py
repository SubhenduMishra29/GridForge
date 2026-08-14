# ============================================================
# File: ui/panels/project_panel.py
# GridForge V2 — Project Panel
# ============================================================
"""
Project structure panel for the GridForge UI.

Responsibilities
----------------
ProjectPanel is a presentation-only widget for displaying the
currently available project files/items.

It is responsible for:

    - displaying project file names;
    - replacing the displayed file list;
    - clearing the displayed list;
    - exposing the current displayed items.

ProjectPanel does NOT:

    - load project files;
    - save project files;
    - modify the Core model;
    - perform project parsing;
    - manage project persistence;
    - create commands;
    - perform filesystem operations;
    - own project/application state.

Data Ownership
--------------
The project/application layer remains authoritative for project
structure.

ProjectPanel contains only the visual representation of that
structure.

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


class ProjectPanel(QWidget):
    """
    Displays the current project file structure.

    The panel is deliberately passive. It receives project data
    from the application layer and presents it to the user.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the project panel.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # Project file list.
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
    # FILE DATA
    # ========================================================

    def set_files(
        self,
        files: Iterable[str],
    ) -> None:
        """
        Replace the displayed project file list.

        Parameters
        ----------
        files:
            Iterable of project file names.

        Notes
        -----
        This method changes only the visual representation.
        It does not perform filesystem or project operations.
        """

        if files is None:
            raise ValueError(
                "files must not be None."
            )

        self.list.clear()

        self.list.addItems(
            [
                str(file_name)
                for file_name in files
            ]
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all displayed project files.
        """

        self.list.clear()

    # ========================================================
    # FILE ACCESS
    # ========================================================

    def get_files(
        self,
    ) -> list[str]:
        """
        Return the currently displayed project file names.
        """

        return [
            self.list.item(index).text()
            for index in range(
                self.list.count()
            )
        ]

    # ========================================================
    # FILE COUNT
    # ========================================================

    def get_file_count(
        self,
    ) -> int:
        """
        Return the number of displayed project files.
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
            "file_count": self.list.count(),
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
            "ProjectPanel("
            f"files={self.list.count()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ProjectPanel",
]
