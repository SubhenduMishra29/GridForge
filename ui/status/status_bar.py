```python
# ============================================================
# File: ui/status/status_bar.py
# GridForge V2 — Status Bar
# ============================================================
"""
GridForge V2 Status Bar
=======================

Presentation-only status bar for the GridForge UI.

Responsibilities
----------------
StatusBar displays transient UI/application information such as:

    - active tool;
    - cursor coordinates;
    - general status messages.

StatusBar does NOT:

    - own application state;
    - access the Core model;
    - manage ToolManager;
    - perform coordinate conversion;
    - perform electrical calculations;
    - subscribe directly to Core events;
    - execute commands;
    - modify application state.

The Controller, InteractionManager, or another UI orchestration
component is responsible for supplying information to this widget.

Architecture
------------

    Application / Controller
              │
              │ presentation updates
              ▼
        ┌─────────────┐
        │ StatusBar   │
        ├─────────────┤
        │ message     │
        │ tool        │
        │ coordinates │
        └─────────────┘

Qt Architecture
---------------
All Qt classes must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QLabel,
    QStatusBar,
    QWidget,
)


class StatusBar(QStatusBar):
    """
    Passive GridForge application status bar.

    The widget provides explicit presentation methods rather than
    discovering application state on its own.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the status bar.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # Presentation state.
        #
        # These values are owned by the StatusBar only as
        # displayed state. They are not application state.
        # ----------------------------------------------------

        self._tool_name = "None"

        self._x = 0.0
        self._y = 0.0

        self._message = ""

        # ====================================================
        # GENERAL STATUS MESSAGE
        # ====================================================

        self.message_label = QLabel(
            self
        )

        self.addWidget(
            self.message_label
        )

        # ====================================================
        # TOOL STATE
        # ====================================================

        self.tool_label = QLabel(
            "Tool: None",
            self,
        )

        self.addPermanentWidget(
            self.tool_label
        )

        # ====================================================
        # COORDINATES
        # ====================================================

        self.coord_label = QLabel(
            "X: 0.0, Y: 0.0",
            self,
        )

        self.addPermanentWidget(
            self.coord_label
        )

    # ========================================================
    # MESSAGE
    # ========================================================

    def set_message(
        self,
        message: str,
    ) -> None:
        """
        Set the general status message.

        Parameters
        ----------
        message:
            Human-readable status text.
        """

        if message is None:
            message = ""

        if not isinstance(
            message,
            str,
        ):
            message = str(
                message
            )

        self._message = message

        self.message_label.setText(
            message
        )

    # --------------------------------------------------------

    def clear_message(
        self,
    ) -> None:
        """
        Clear the general status message.
        """

        self.set_message(
            ""
        )

    # ========================================================
    # TOOL
    # ========================================================

    def set_tool(
        self,
        tool_name: str,
    ) -> None:
        """
        Display the currently active tool.

        Parameters
        ----------
        tool_name:
            Display name of the active tool.
        """

        if tool_name is None:
            tool_name = "None"

        if not isinstance(
            tool_name,
            str,
        ):
            tool_name = str(
                tool_name
            )

        tool_name = tool_name.strip()

        if not tool_name:
            tool_name = "None"

        self._tool_name = tool_name

        self.tool_label.setText(
            f"Tool: {tool_name}"
        )

    # --------------------------------------------------------

    def clear_tool(
        self,
    ) -> None:
        """
        Reset the displayed tool to the neutral state.
        """

        self.set_tool(
            "None"
        )

    # ========================================================
    # COORDINATES
    # ========================================================

    def set_coordinates(
        self,
        x: float,
        y: float,
    ) -> None:
        """
        Display scene/canvas coordinates.

        Coordinate conversion is performed outside this widget.

        Parameters
        ----------
        x:
            Resolved display X coordinate.

        y:
            Resolved display Y coordinate.
        """

        self._x = float(
            x
        )

        self._y = float(
            y
        )

        self.coord_label.setText(
            f"X: {self._x:.1f}, "
            f"Y: {self._y:.1f}"
        )

    # --------------------------------------------------------

    def clear_coordinates(
        self,
    ) -> None:
        """
        Reset the displayed coordinates to zero.
        """

        self.set_coordinates(
            0.0,
            0.0,
        )

    # ========================================================
    # RESET
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Reset all presentation state to its neutral values.
        """

        self.clear_message()

        self.clear_tool()

        self.clear_coordinates()

    # ========================================================
    # STATE ACCESS
    # ========================================================

    def get_tool(
        self,
    ) -> str:
        """
        Return the currently displayed tool name.
        """

        return self._tool_name

    # --------------------------------------------------------

    def get_coordinates(
        self,
    ) -> tuple[float, float]:
        """
        Return the currently displayed coordinates.
        """

        return (
            self._x,
            self._y,
        )

    # --------------------------------------------------------

    def get_message(
        self,
    ) -> str:
        """
        Return the currently displayed general message.
        """

        return self._message

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of status-bar state.
        """

        return {
            "tool": self._tool_name,
            "coordinates": (
                self._x,
                self._y,
            ),
            "message": self._message,
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
            "StatusBar("
            f"tool={self._tool_name!r}, "
            f"coordinates=({self._x:.1f}, "
            f"{self._y:.1f}), "
            f"message={self._message!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "StatusBar",
]
```
