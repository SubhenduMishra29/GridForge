"""StudyCompleted-driven charts; presentation updates are marshalled to the Qt thread."""
from __future__ import annotations

from typing import Any

import numpy as np

from core.application.events import StudyCompleted
from ui.core.qt import (
    QObject, QPointF, QChart, QChartView, QLineSeries, QSplitter,
    QValueAxis, QVBoxLayout, QWidget, Qt, Signal,
)


class _StudyCompletionBridge(QObject):
    """Queued signal bridge from the synchronous Application event bus to Qt."""

    completed = Signal(object)


class MotorTelemetryDashboardWidget(QWidget):
    def __init__(self, read_models: Any, event_bus: Any = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.read_models = read_models
        self.event_bus = event_bus
        self._bridge = _StudyCompletionBridge(self)
        self._bridge.completed.connect(self._on_study_completed)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        self._charts = {}

        for key, title, ytitle in (
            ("current", "Stator Inrush Current Profile", "Current (A)"),
            ("temperature", "Winding Temperature Dynamics", "Temperature (°C)"),
        ):
            series = QLineSeries()
            chart = QChart()
            chart.setTitle(title)
            chart.addSeries(series)
            xaxis, yaxis = QValueAxis(), QValueAxis()
            xaxis.setTitleText("Time (s)")
            yaxis.setTitleText(ytitle)
            chart.addAxis(xaxis, Qt.AlignmentFlag.AlignBottom)
            chart.addAxis(yaxis, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(xaxis)
            series.attachAxis(yaxis)
            self.splitter.addWidget(QChartView(chart))
            self._charts[key] = (series, xaxis, yaxis)

        self._subscribed = False
        self._subscribe(event_bus)

    def _subscribe(self, bus: Any) -> None:
        subscribe = getattr(bus, "subscribe", None) if bus is not None else None
        if callable(subscribe):
            subscribe(StudyCompleted, self._handle_study_completed_event)
            self._subscribed = True

    def _handle_study_completed_event(self, event: StudyCompleted) -> None:
        # ApplicationEventBus publishes synchronously; emitting a Qt signal
        # ensures widget mutations run on the widget's owning thread.
        self._bridge.completed.emit(event)

    def _on_study_completed(self, event: StudyCompleted) -> None:
        payload = event.payload
        motor_id = payload.get("motor_id")
        if not isinstance(motor_id, str) or not motor_id:
            return

        summary = self.read_models.get_simulation_summary(motor_id)
        if summary is None:
            return

        for key, channel in (
            ("current", "stator_current_a"),
            ("temperature", "winding_temperature_c"),
        ):
            vector = self.read_models.get_raw_channel_vector(motor_id, channel)
            if vector is None or not vector.size:
                continue
            stride = max(1, int(np.ceil(vector.size / 1500)))
            indices = np.arange(0, vector.size, stride)
            times = indices * summary.sample_period_s
            points = [QPointF(float(t), float(y)) for t, y in zip(times, vector[indices])]
            series, xaxis, yaxis = self._charts[key]
            series.replace(points)
            xaxis.setRange(float(times[0]), max(float(times[-1]), float(times[0]) + summary.sample_period_s))
            values = vector[indices]
            lo, hi = float(np.min(values)), float(np.max(values))
            pad = max((hi - lo) * 0.05, 1e-3)
            yaxis.setRange(lo - pad, hi + pad)

    def closeEvent(self, event: Any) -> None:
        if self._subscribed and self.event_bus is not None:
            self.event_bus.unsubscribe(StudyCompleted, self._handle_study_completed_event)
            self._subscribed = False
        super().closeEvent(event)
