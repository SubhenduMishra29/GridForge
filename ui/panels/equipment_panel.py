# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/equipment_panel.py
#
# Purpose:
#     Electrical equipment browser / insertion panel.
#
# Architectural boundary:
#     Logical panel only. Equipment creation remains delegated
#     to the application's command/tool/model workflow.
# ============================================================

from __future__ import annotations

from .panel_base import PanelBase


class EquipmentPanel(PanelBase):
    """
    Electrical equipment browser panel.

    This panel provides the logical presentation boundary for
    selecting equipment types. It does not create electrical
    model objects and does not manipulate the SLD canvas directly.
    """

    _PANEL_ID = "equipment"
    _TITLE = "Equipment Browser"

    def __init__(self) -> None:
        self._created = False
        self._visible = False
        self._active = False
        self._selected_equipment_type: str | None = None

    @property
    def panel_id(self) -> str:
        """Return the stable panel identifier."""
        return self._PANEL_ID

    @property
    def title(self) -> str:
        """Return the human-readable panel title."""
        return self._TITLE

    @property
    def is_created(self) -> bool:
        """Return whether the panel lifecycle has started."""
        return self._created

    @property
    def is_visible(self) -> bool:
        """Return the current logical visibility state."""
        return self._visible

    @property
    def is_active(self) -> bool:
        """Return the current logical activation state."""
        return self._active

    @property
    def selected_equipment_type(self) -> str | None:
        """Return the currently selected equipment type."""
        return self._selected_equipment_type

    def select_equipment_type(
        self,
        equipment_type: str | None,
    ) -> None:
        """
        Select an equipment type for the surrounding UI workflow.

        This does not instantiate or modify a Core model object.
        """

        if equipment_type is not None:
            if not isinstance(equipment_type, str):
                raise TypeError(
                    "equipment_type must be str or None."
                )

            if not equipment_type.strip():
                raise ValueError(
                    "equipment_type must not be empty."
                )

        self._selected_equipment_type = equipment_type

    def on_create(self) -> None:
        """Initialize panel-local transient state."""
        self._created = True

    def on_show(self) -> None:
        """Mark the panel logically visible."""
        self._visible = True

    def on_hide(self) -> None:
        """Mark the panel logically hidden."""
        self._visible = False

    def on_activate(self) -> None:
        """Mark the panel logically active."""
        self._active = True

    def on_deactivate(self) -> None:
        """Mark the panel logically inactive."""
        self._active = False

    def on_destroy(self) -> None:
        """Release panel-local lifecycle state."""
        self._selected_equipment_type = None
        self._active = False
        self._visible = False
        self._created = False

    def reset(self) -> None:
        """Reset transient equipment selection."""
        self._selected_equipment_type = None
        self._active = False
