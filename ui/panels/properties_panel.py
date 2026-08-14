# ============================================================
# File: ui/panels/properties_panel.py
# GridForge V2 — Properties Panel
# ============================================================

"""
GridForge V2 — Properties Panel
================================

Displays properties of the currently selected GridForge object.

Responsibilities
----------------
PropertiesPanel:

    - provide the properties UI;
    - display a selected object's properties;
    - clear the displayed properties;
    - provide diagnostic state.

PropertiesPanel does NOT:

    - own the Core model;
    - modify Core model objects directly;
    - perform electrical calculations;
    - perform selection;
    - create tools;
    - manage ToolManager;
    - manage docking;
    - perform rendering;
    - become the authoritative source of object state.

Architecture
------------

    Selection / Controller
            │
            ▼
      PropertiesPanel
            │
            ▼
       Display only

The Core model remains authoritative.

Qt Rule
-------
All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from ui.core.qt import (
    QLabel,
    QFormLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PropertiesPanel(QWidget):
    """
    Read-only property inspection panel.

    The panel intentionally starts as a presentation-only
    component. Editing semantics can be introduced later through
    explicit Controller/Command integration rather than by
    allowing the widget to mutate Core objects directly.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the PropertiesPanel.
        """

        super().__init__(parent)

        self._selected_object: Optional[Any] = None

        # ----------------------------------------------------
        # Root layout
        # ----------------------------------------------------

        self._layout = QVBoxLayout(
            self
        )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        self._title = QLabel(
            "Properties"
        )

        self._layout.addWidget(
            self._title
        )

        # ----------------------------------------------------
        # Scroll container
        #
        # Property sets may grow as richer model objects are
        # introduced.
        # ----------------------------------------------------

        self._scroll = QScrollArea()

        self._scroll.setWidgetResizable(
            True
        )

        self._layout.addWidget(
            self._scroll
        )

        # ----------------------------------------------------
        # Property content widget
        # ----------------------------------------------------

        self._content = QWidget()

        self._form = QFormLayout(
            self._content
        )

        self._scroll.setWidget(
            self._content
        )

        self._show_empty_state()

    # ========================================================
    # OBJECT ACCESS
    # ========================================================

    def set_object(
        self,
        obj: Optional[Any],
    ) -> None:
        """
        Display properties for the supplied object.

        Parameters
        ----------
        obj:
            Object whose properties should be displayed.

        Notes
        -----
        The object is retained only as the current presentation
        target. The panel does not modify it.
        """

        self._selected_object = obj

        self._clear_properties()

        if obj is None:
            self._show_empty_state()
            return

        self._title.setText(
            "Properties"
        )

        properties = self._extract_properties(
            obj
        )

        if not properties:
            self._add_property(
                "Object",
                type(obj).__name__,
            )

            return

        for name, value in properties.items():
            self._add_property(
                name,
                value,
            )

    # --------------------------------------------------------

    def clear(
        self,
    ) -> None:
        """
        Clear the currently displayed object and properties.
        """

        self._selected_object = None

        self._clear_properties()

        self._show_empty_state()

    # ========================================================
    # PROPERTY EXTRACTION
    # ========================================================

    def _extract_properties(
        self,
        obj: Any,
    ) -> dict[str, Any]:
        """
        Extract a conservative read-only property snapshot.

        Priority
        --------
        1. Public ``get_properties()`` method when available.
        2. Public ``properties`` mapping when available.
        3. No implicit ``__dict__`` dumping.

        Notes
        -----
        We deliberately do not inspect arbitrary object
        attributes. Core models may contain internal state,
        services, references, or non-displayable objects.
        """

        getter = getattr(
            obj,
            "get_properties",
            None,
        )

        if callable(getter):
            result = getter()

            if result is None:
                return {}

            if not isinstance(
                result,
                Mapping,
            ):
                raise TypeError(
                    "get_properties() must return a mapping."
                )

            return {
                str(key): value
                for key, value
                in result.items()
            }

        properties = getattr(
            obj,
            "properties",
            None,
        )

        if isinstance(
            properties,
            Mapping,
        ):
            return {
                str(key): value
                for key, value
                in properties.items()
            }

        return {}

    # ========================================================
    # PROPERTY DISPLAY
    # ========================================================

    def _add_property(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Add one read-only property row.
        """

        name_label = QLabel(
            str(name)
        )

        value_label = QLabel(
            self._format_value(value)
        )

        value_label.setWordWrap(
            True
        )

        self._form.addRow(
            name_label,
            value_label,
        )

    # --------------------------------------------------------

    @staticmethod
    def _format_value(
        value: Any,
    ) -> str:
        """
        Convert a property value to a safe display string.
        """

        if value is None:
            return "—"

        if isinstance(
            value,
            bool,
        ):
            return "Yes" if value else "No"

        return str(value)

    # ========================================================
    # INTERNAL UI MANAGEMENT
    # ========================================================

    def _clear_properties(
        self,
    ) -> None:
        """
        Remove all currently displayed property rows.
        """

        while self._form.rowCount() > 0:

            self._form.removeRow(
                0
            )

    # --------------------------------------------------------

    def _show_empty_state(
        self,
    ) -> None:
        """
        Display the empty-selection state.
        """

        self._title.setText(
            "Properties"
        )

        self._add_property(
            "Selection",
            "No object selected",
        )

    # ========================================================
    # STATE ACCESS
    # ========================================================

    def get_object(
        self,
    ) -> Optional[Any]:
        """
        Return the currently displayed object.
        """

        return self._selected_object

    # --------------------------------------------------------

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic panel state.
        """

        return {
            "has_object": (
                self._selected_object is not None
            ),
            "object_type": (
                type(self._selected_object).__name__
                if self._selected_object is not None
                else None
            ),
            "property_count": (
                self._form.rowCount()
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

        object_type = (
            type(self._selected_object).__name__
            if self._selected_object is not None
            else "None"
        )

        return (
            "PropertiesPanel("
            f"object={object_type}, "
            f"properties={self._form.rowCount()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PropertiesPanel",
]
