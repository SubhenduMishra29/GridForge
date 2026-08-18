# ============================================================
# File: ui/styling/theme.py
# GridForge V2 — UI Theme Infrastructure
# ============================================================
"""
GridForge V2 UI Theme Infrastructure.

This module defines the presentation-level theme contract used
by the GridForge UI styling subsystem.

Architectural Role
------------------
Theme definitions belong to the presentation layer.

A Theme describes visual properties such as:

    - application colors
    - panel colors
    - canvas appearance
    - foreground colors
    - accent colors
    - borders
    - selection appearance
    - typography

Theme does NOT:

    - own application state;
    - own engineering state;
    - access Controller;
    - access GridForge Core;
    - create Qt objects;
    - load stylesheets;
    - modify QApplication;
    - modify widgets;
    - perform rendering;
    - perform engineering calculations.

QSS/application of a theme belongs to a higher-level styling
service.

Design Principles
-----------------
1. Theme is immutable.
2. Theme contains presentation configuration only.
3. Theme is independent of Qt.
4. Theme is independent of Controller.
5. Theme is independent of GridForge Core.
6. Theme instances are safe to share.
7. Theme definitions are deterministic.
8. Default theme configuration is explicit.
9. Future themes must implement the same data contract.
10. Styling behavior must not be hidden inside Theme.

Future Vision
-------------
The theme contract is intentionally extensible.

Future versions may support:

    - light theme;
    - dark theme;
    - high-contrast theme;
    - custom user themes;
    - accessibility profiles;
    - compact/comfortable UI density;
    - typography scales;
    - canvas palettes;
    - semantic equipment colors;
    - state-aware visual tokens;
    - theme serialization.

Those extensions must remain presentation concerns and must
not introduce engineering-domain semantics.
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================
# THEME
# ============================================================


@dataclass(frozen=True, slots=True)
class Theme:
    """
    Immutable GridForge UI theme definition.

    Theme contains presentation tokens only.

    The values are intentionally represented as simple Python
    data rather than Qt-specific objects. This keeps the theme
    contract independent of the Qt implementation.
    """

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    name: str

    # --------------------------------------------------------
    # General application surfaces
    # --------------------------------------------------------

    application_background: str
    panel_background: str
    canvas_background: str

    # --------------------------------------------------------
    # Foreground / text
    # --------------------------------------------------------

    foreground: str
    secondary_foreground: str
    disabled_foreground: str

    # --------------------------------------------------------
    # Interaction
    # --------------------------------------------------------

    accent: str
    border: str
    selection: str

    # --------------------------------------------------------
    # UI surfaces
    # --------------------------------------------------------

    toolbar_background: str
    statusbar_background: str

    # --------------------------------------------------------
    # Typography
    # --------------------------------------------------------

    font_family: str
    font_size: int

    # ========================================================
    # VALIDATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate the immutable theme definition.

        Validation is intentionally limited to structural
        correctness.

        Theme does not attempt to interpret engineering meaning
        from presentation values.
        """

        self._validate_non_empty_string(
            self.name,
            "name",
        )

        self._validate_non_empty_string(
            self.application_background,
            "application_background",
        )

        self._validate_non_empty_string(
            self.panel_background,
            "panel_background",
        )

        self._validate_non_empty_string(
            self.canvas_background,
            "canvas_background",
        )

        self._validate_non_empty_string(
            self.foreground,
            "foreground",
        )

        self._validate_non_empty_string(
            self.secondary_foreground,
            "secondary_foreground",
        )

        self._validate_non_empty_string(
            self.disabled_foreground,
            "disabled_foreground",
        )

        self._validate_non_empty_string(
            self.accent,
            "accent",
        )

        self._validate_non_empty_string(
            self.border,
            "border",
        )

        self._validate_non_empty_string(
            self.selection,
            "selection",
        )

        self._validate_non_empty_string(
            self.toolbar_background,
            "toolbar_background",
        )

        self._validate_non_empty_string(
            self.statusbar_background,
            "statusbar_background",
        )

        self._validate_non_empty_string(
            self.font_family,
            "font_family",
        )

        if (
            isinstance(self.font_size, bool)
            or not isinstance(self.font_size, int)
        ):
            raise TypeError(
                "font_size must be an integer."
            )

        if self.font_size <= 0:
            raise ValueError(
                "font_size must be greater than zero."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_non_empty_string(
        value: object,
        field_name: str,
    ) -> None:
        """
        Validate a required non-empty string field.
        """

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"{field_name} must not be empty."
            )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, object]:
        """
        Return a diagnostic representation of the theme.

        The returned dictionary contains presentation values
        only and does not expose mutable Theme state because
        Theme itself is immutable.
        """

        return {
            "name": self.name,
            "application_background": (
                self.application_background
            ),
            "panel_background": (
                self.panel_background
            ),
            "canvas_background": (
                self.canvas_background
            ),
            "foreground": self.foreground,
            "secondary_foreground": (
                self.secondary_foreground
            ),
            "disabled_foreground": (
                self.disabled_foreground
            ),
            "accent": self.accent,
            "border": self.border,
            "selection": self.selection,
            "toolbar_background": (
                self.toolbar_background
            ),
            "statusbar_background": (
                self.statusbar_background
            ),
            "font_family": self.font_family,
            "font_size": self.font_size,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "Theme("
            f"name={self.name!r}, "
            f"font_family={self.font_family!r}, "
            f"font_size={self.font_size!r}"
            ")"
        )


# ============================================================
# DEFAULT THEME
# ============================================================

DEFAULT_THEME = Theme(
    name="GridForge Dark",

    application_background="#202124",
    panel_background="#25272B",
    canvas_background="#181A1D",

    foreground="#E8EAED",
    secondary_foreground="#AEB4BD",
    disabled_foreground="#686D75",

    accent="#4DA3FF",
    border="#3A3D42",
    selection="#315F8F",

    toolbar_background="#25272B",
    statusbar_background="#202124",

    font_family="Segoe UI",
    font_size=10,
)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "DEFAULT_THEME",
    "Theme",
]
