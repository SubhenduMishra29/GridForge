# ============================================================
# File: ui/panels/console_panel.py
# GridForge V2 — Console Panel
# ============================================================
"""
System console panel for the GridForge UI.

Responsibilities
----------------
ConsolePanel is a presentation-only widget for displaying
system messages, diagnostics, validation output, and other
human-readable application messages.

ConsolePanel:

    - displays text messages;
    - provides a read-only console;
    - preserves message order;
    - exposes a small presentation API.

ConsolePanel does NOT:

    - own the application logging system;
    - perform validation;
    - modify the Core model;
    - execute commands;
    - perform electrical calculations;
    - subscribe directly to arbitrary Core events;
    - interpret message contents.

Message Ownership
-----------------
The panel owns only the visual representation of messages.

The source of messages belongs to the application/controller
or logging infrastructure.

Qt Architecture
---------------
All Qt classes must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QVBoxLayout,
    QTextEdit,
    QWidget,
)


class ConsolePanel(QWidget):
    """
    Read-only system console for the GridForge UI.

    The panel is deliberately thin. It provides presentation
    facilities only; message generation and application logging
    remain outside this widget.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the console panel.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # Console text area.
        # ----------------------------------------------------

        self.text = QTextEdit(
            self
        )

        self.text.setReadOnly(
            True
        )

        # ----------------------------------------------------
        # Layout.
        # ----------------------------------------------------

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            self.text
        )

    # ========================================================
    # LOGGING API
    # ========================================================

    def log(
        self,
        message: Any,
    ) -> None:
        """
        Append a message to the console.

        Parameters
        ----------
        message:
            Human-readable message to display.

        Notes
        -----
        Message generation and classification remain outside
        ConsolePanel. The panel only presents the supplied
        content.
        """

        if message is None:
            return

        self.text.append(
            str(message)
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear all console output.
        """

        self.text.clear()

    # ========================================================
    # CONTENT ACCESS
    # ========================================================

    def get_text(
        self,
    ) -> str:
        """
        Return the complete visible console contents.
        """

        return self.text.toPlainText()

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic console state.
        """

        return {
            "message_count": (
                len(
                    self.text
                    .toPlainText()
                    .splitlines()
                )
                if self.text.toPlainText()
                else 0
            ),
            "read_only": (
                self.text.isReadOnly()
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
            "ConsolePanel("
            f"messages="
            f"{self.get_state()['message_count']}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ConsolePanel",
]
