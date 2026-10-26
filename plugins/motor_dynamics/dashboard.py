"""StudyCompleted-driven charts; Qt widgets are presentation-only and do not run solvers."""
from __future__ import annotations
from typing import Any
import numpy as np
from ui.core.qt import QWidget, QSplitter, QVBoxLayout, QChart, QChartView, QLineSeries, QValueAxis, Qt

class MotorTelemetryDashboardWidget(QWidget):
    def __init__(self, read_models: Any, event_bus: Any = None, parent: QWidget | None = None):
        super().__init__(parent); self.read_models, self.event_bus = read_models, event_bus
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self); layout = QVBoxLayout(self); layout.addWidget(self.splitter)
        self._charts = {}
        for key, title, ytitle in (("current", "Stator Inrush Current Profile", "Current (A)"), ("temperature", "Winding Temperature Dynamics", "Temperature (°C)")):
            series = QLineSeries(); chart = QChart(); chart.setTitle(title); chart.addSeries(series)
            xaxis, yaxis = QValueAxis(), QValueAxis(); xaxis.setTitleText("Time (s)"); yaxis.setTitleText(ytitle)
            chart.addAxis(xaxis, Qt.AlignmentFlag.AlignBottom); chart.addAxis(yaxis, Qt.AlignmentFlag.AlignLeft); series.attachAxis(xaxis); series.attachAxis(yaxis)
            self.splitter.addWidget(QChartView(chart)); self._charts[key] = (series, xaxis, yaxis)
        self._unsubscribe = self._subscribe(event_bus)
    def _subscribe(self, bus: Any):
        if bus is None: return None
        subscribe = getattr(bus, "subscribe", None)
        if not callable(subscribe): return None
        return subscribe("StudyCompleted", self._on_study_completed)
    def _on_study_completed(self, event: Any) -> None:
        payload = getattr(event, "payload", {}) or {}; motor_id = payload.get("motor_id")
        if not motor_id: return
        summary = self.read_models.get_simulation_summary(motor_id)
        if summary is None: return
        for key, channel in (("current", "stator_current_a"), ("temperature", "winding_temperature_c")):
            vector = self.read_models.get_raw_channel_vector(motor_id, channel)
            if vector is None or not vector.size: continue
            stride = max(1, int(np.ceil(vector.size / 1500))); indices = np.arange(0, vector.size, stride); t = indices * summary.sample_period_s
            points = [ (float(x), float(y)) for x, y in zip(t, vector[indices]) ]
            series, xaxis, yaxis = self._charts[key]; series.replace(points)
            xaxis.setRange(float(t[0]), max(float(t[-1]), float(t[0]) + summary.sample_period_s)); lo, hi = float(np.min(vector[indices])), float(np.max(vector[indices])); pad = max((hi-lo)*.05, 1e-3); yaxis.setRange(lo-pad, hi+pad)
    def closeEvent(self, event: Any) -> None:
        if callable(self._unsubscribe): self._unsubscribe()
        super().closeEvent(event)
