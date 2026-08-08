# ============================================================
# File: ui/items/base_item.py
# Base graphics item with selection + styling behavior
# ============================================================

from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QPen, QColor


class BaseItem(QGraphicsItem):
    """
    Base class for all scene items.
    """

    def __init__(self, model_obj):
        super().__init__()

        self.model = model_obj

        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable
        )

    # --------------------------------------------------
    def paint_selection(self, painter):
        if self.isSelected():
            pen = QPen(QColor(0, 150, 255), 2)
            painter.setPen(pen)
            painter.drawRect(self.boundingRect())
