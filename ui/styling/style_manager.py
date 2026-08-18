# ============================================================
# File: ui/styling/style_manager.py
# GridForge V2 — UI Style Manager
# ============================================================
"""
GridForge V2 UI Style Manager.

The StyleManager is the application-facing styling service for
the GridForge graphical interface.

Architectural Role
------------------
StyleManager bridges the presentation-only Theme definition
and the Qt application.

    Theme
      │
      ▼
    StyleManager
      │
      ▼
    QApplication
      │
      ▼
    GridForge UI

Responsibilities
----------------
StyleManager:

    - owns the currently active Theme reference;
    - loads the GridForge QSS stylesheet;
    - applies the stylesheet to QApplication;
    - provides controlled theme access;
    - provides styling diagnostics;
    - supports explicit stylesheet application.

StyleManager does NOT:

    - own application state;
    - own engineering state;
    - modify Controller state;
    - modify GridForge Core;
    - perform engineering calculations;
    - manage widgets;
    - manage canvas state;
    - manage tools;
    - manage selection;
    - manage plugins;
    - manage renderers;
    - create a QApplication;
    - become a global styling singleton.

Qt Boundary
-----------
Qt types are imported exclusively through:

    ui.core.qt

No direct PySide6 or PyQt imports are permitted.

Stylesheet Ownership
--------------------
The default stylesheet is stored in:

    ui/styling/stylesheet.qss

The stylesheet is a presentation resource.

It must not contain:

    - application logic;
    - engineering state;
    - controller behavior;
    - electrical semantics;
    - dynamic application decisions.

Theme Independence
------------------
Theme is deliberately Qt-independent.

StyleManager is responsible for translating the selected
presentation configuration into application-level styling.

The initial implementation supports the GridForge QSS resource
directly. The architecture remains open for future token
substitution and theme-specific stylesheet generation.

Future Vision
-------------
Future versions may support:

    - runtime theme switching;
    - light/dark themes;
    - high-contrast accessibility themes;
    - custom user themes;
    - stylesheet token substitution;
    - UI density profiles;
    - typography profiles;
    - canvas presentation profiles;
    - persisted UI appearance preferences;
    - theme validation;
    - stylesheet caching.

These capabilities must remain presentation concerns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ui.core.qt import QApplication

from .theme import DEFAULT_THEME, Theme


# ============================================================
# EXCEPTIONS
# ============================================================


class StyleManagerError(RuntimeError):
    """
    Base exception for UI styling failures.
    """


class StylesheetLoadError(StyleManagerError):
    """
    Raised when the QSS stylesheet cannot be loaded.
    """


class StylesheetApplyError(StyleManagerError):
    """
    Raised when a stylesheet cannot be applied to QApplication.
    """


# ============================================================
# STYLE MANAGER
# ============================================================


class StyleManager:
    """
    Central application-level styling service.

    StyleManager does not create QApplication.

    The application/composition layer is responsible for
    creating QApplication before calling apply().
    """

    # ========================================================
    # RESOURCE LOCATION
    # ========================================================

    _STYLESHEET_FILENAME = "stylesheet.qss"

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        theme: Optional[Theme] = None,
        stylesheet_path: Optional[str | Path] = None,
    ) -> None:
        """
        Initialize the StyleManager.

        Parameters
        ----------
        theme:
            Presentation theme to use.

            Defaults to DEFAULT_THEME.

        stylesheet_path:
            Optional path to a QSS stylesheet.

            When omitted, the GridForge default stylesheet
            located beside this module is used.
        """

        if theme is None:
            theme = DEFAULT_THEME

        if not isinstance(theme, Theme):
            raise TypeError(
                "theme must be a Theme instance."
            )

        self._theme = theme

        if stylesheet_path is None:
            stylesheet_path = (
                Path(__file__).resolve().parent
                / self._STYLESHEET_FILENAME
            )

        self._stylesheet_path = Path(
            stylesheet_path
        ).resolve()

        self._stylesheet: Optional[str] = None

        self._applied = False

    # ========================================================
    # THEME
    # ========================================================

    @property
    def theme(self) -> Theme:
        """
        Return the currently configured Theme.
        """

        return self._theme

    # --------------------------------------------------------

    def get_theme(self) -> Theme:
        """
        Return the currently configured Theme.
        """

        return self._theme

    # --------------------------------------------------------

    def set_theme(
        self,
        theme: Theme,
    ) -> None:
        """
        Replace the configured presentation theme.

        Changing the configured theme does not automatically
        modify QApplication.

        Call apply() explicitly to apply the new styling.
        """

        if not isinstance(theme, Theme):
            raise TypeError(
                "theme must be a Theme instance."
            )

        self._theme = theme
        self._applied = False

    # --------------------------------------------------------

    def reset_theme(self) -> None:
        """
        Restore DEFAULT_THEME.

        The new theme is not applied automatically.
        """

        self.set_theme(
            DEFAULT_THEME
        )

    # ========================================================
    # STYLESHEET PATH
    # ========================================================

    @property
    def stylesheet_path(self) -> Path:
        """
        Return the configured stylesheet path.
        """

        return self._stylesheet_path

    # --------------------------------------------------------

    def get_stylesheet_path(self) -> Path:
        """
        Return the configured stylesheet path.
        """

        return self._stylesheet_path

    # --------------------------------------------------------

    def set_stylesheet_path(
        self,
        path: str | Path,
    ) -> None:
        """
        Set the stylesheet resource path.

        The stylesheet is not loaded or applied automatically.
        """

        if path is None:
            raise ValueError(
                "path must not be None."
            )

        self._stylesheet_path = Path(
            path
        ).resolve()

        self._stylesheet = None
        self._applied = False

    # ========================================================
    # STYLESHEET LOADING
    # ========================================================

    def load_stylesheet(self) -> str:
        """
        Load and cache the configured QSS stylesheet.

        Returns
        -------
        str
            Complete stylesheet contents.

        Raises
        ------
        StylesheetLoadError
            If the stylesheet cannot be read.
        """

        path = self._stylesheet_path

        if not path.exists():
            raise StylesheetLoadError(
                "Stylesheet does not exist: "
                f"{path}"
            )

        if not path.is_file():
            raise StylesheetLoadError(
                "Stylesheet path is not a file: "
                f"{path}"
            )

        try:
            stylesheet = path.read_text(
                encoding="utf-8"
            )
        except OSError as exc:
            raise StylesheetLoadError(
                "Failed to read stylesheet: "
                f"{path}"
            ) from exc

        self._stylesheet = stylesheet

        return stylesheet

    # --------------------------------------------------------

    def get_stylesheet(self) -> str:
        """
        Return the currently loaded stylesheet.

        The stylesheet is loaded lazily if necessary.
        """

        if self._stylesheet is None:
            return self.load_stylesheet()

        return self._stylesheet

    # --------------------------------------------------------

    def reload_stylesheet(self) -> str:
        """
        Force a fresh stylesheet load from disk.
        """

        self._stylesheet = None

        return self.load_stylesheet()

    # ========================================================
    # APPLICATION
    # ========================================================

    def apply(
        self,
        application: Optional[QApplication] = None,
    ) -> None:
        """
        Apply the configured stylesheet to QApplication.

        Parameters
        ----------
        application:
            QApplication instance.

            If omitted, QApplication.instance() is used.

        Raises
        ------
        RuntimeError
            If no QApplication exists.

        StylesheetApplyError
            If QApplication cannot accept the stylesheet.
        """

        target = application

        if target is None:
            target = QApplication.instance()

        if target is None:
            raise RuntimeError(
                "A QApplication instance is required "
                "before applying UI styling."
            )

        stylesheet = self.get_stylesheet()

        try:
            target.setStyleSheet(
                stylesheet
            )
        except Exception as exc:
            raise StylesheetApplyError(
                "Failed to apply GridForge stylesheet."
            ) from exc

        self._applied = True

    # ========================================================
    # RESET
    # ========================================================

    def clear(
        self,
        application: Optional[QApplication] = None,
    ) -> None:
        """
        Remove the GridForge application stylesheet.

        This affects Qt presentation only.

        No application or engineering state is modified.
        """

        target = application

        if target is None:
            target = QApplication.instance()

        if target is None:
            raise RuntimeError(
                "A QApplication instance is required "
                "before clearing UI styling."
            )

        try:
            target.setStyleSheet("")
        except Exception as exc:
            raise StylesheetApplyError(
                "Failed to clear GridForge stylesheet."
            ) from exc

        self._applied = False

    # ========================================================
    # STATE
    # ========================================================

    @property
    def applied(self) -> bool:
        """
        Return whether StyleManager successfully applied the
        stylesheet through apply().
        """

        return self._applied

    # --------------------------------------------------------

    def is_applied(self) -> bool:
        """
        Return whether the stylesheet has been applied.
        """

        return self._applied

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_stylesheet(self) -> bool:
        """
        Verify that the configured stylesheet can be loaded.

        This performs resource validation only.

        It does not create QApplication and does not apply
        styling.
        """

        stylesheet = self.load_stylesheet()

        return bool(
            stylesheet.strip()
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of the styling service.
        """

        return {
            "theme": self._theme.name,
            "stylesheet_path": str(
                self._stylesheet_path
            ),
            "stylesheet_loaded": (
                self._stylesheet is not None
            ),
            "stylesheet_length": (
                len(self._stylesheet)
                if self._stylesheet is not None
                else 0
            ),
            "applied": self._applied,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "StyleManager("
            f"theme={self._theme.name!r}, "
            f"applied={self._applied}, "
            f"stylesheet="
            f"{str(self._stylesheet_path)!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "StyleManager",
    "StyleManagerError",
    "StylesheetApplyError",
    "StylesheetLoadError",
]
