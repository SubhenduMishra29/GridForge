# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_area.py
#
# Purpose:
#     Defines canonical logical docking areas.
#
# Architectural Role:
#     Keeps docking semantics independent of Qt constants.
#
# Responsibilities:
#     - define standard panel areas;
#     - validate area names;
#     - provide canonical area values.
#
# Does NOT:
#     - call QMainWindow.addDockWidget();
#     - manipulate QDockWidget.
#
# ============================================================

"""
GridForge V2 — Panel Areas.
"""


class PanelArea:
    """
    Canonical logical docking areas.
    """

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"

    ALL = (
        LEFT,
        RIGHT,
        TOP,
        BOTTOM,
        CENTER,
    )

    @classmethod
    def is_valid(
        cls,
        area: str,
    ) -> bool:
        return area in cls.ALL

    @classmethod
    def require(
        cls,
        area: str,
    ) -> str:
        if not cls.is_valid(area):
            raise ValueError(
                f"Unknown panel area: {area}"
            )

        return area
