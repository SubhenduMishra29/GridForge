"""SLD projection item; imports Qt only through GridForge's single Qt boundary."""
from __future__ import annotations
from typing import Any
from ui.core.qt import QGraphicsItem, QRectF, QPainter, QPen, QBrush, QColor, QFont, Qt

class SLDMotorGraphicsItem(QGraphicsItem):
    RADIUS = 22.0
    def __init__(self, motor_id: str, read_models: Any, parent: QGraphicsItem | None = None):
        super().__init__(parent); self.motor_id, self.read_models = motor_id, read_models
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    def boundingRect(self) -> QRectF: return QRectF(-self.RADIUS-3, -self.RADIUS-3, 2*self.RADIUS+6, 2*self.RADIUS+6)
    def paint(self, painter: QPainter, option: Any, widget: Any = None) -> None:
        summary = self.read_models.get_simulation_summary(self.motor_id)
        fault = (summary.fault or "").lower() if summary else ""
        color = QColor("#d97706") if "bearing" in fault else (QColor("#dc2626") if any(x in fault for x in ("short", "fault", "trip")) else QColor("#2563eb"))
        painter.save(); painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(color, 2.4); painter.setPen(pen); painter.setBrush(QBrush(QColor("#ffffff"))); painter.drawEllipse(QRectF(-self.RADIUS, -self.RADIUS, 2*self.RADIUS, 2*self.RADIUS))
        font = QFont(); font.setBold(True); font.setPointSize(9); painter.setFont(font); painter.setPen(QPen(color)); painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, "M / 3~")
        painter.restore()
