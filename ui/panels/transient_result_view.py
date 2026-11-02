"""Dedicated presentation widget for complete transient-stability results."""

from __future__ import annotations

from core.application.read_models import TransientResultPresentationReadModel
from ui.core.qt import (
    QChart,
    QChartView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineSeries,
    QListWidget,
    QValueAxis,
    QVBoxLayout,
    Qt,
    QWidget,
)


class TransientResultViewWidget(QWidget):
    """Inspect complete transient signals and ordered event history.

    The widget renders every source sample. It does not down-sample, interpolate,
    reorder or regenerate solver data.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgeTransientResultView")
        self._model: TransientResultPresentationReadModel | None = None
        self._signal_combo = QComboBox(self)
        self._provenance = QLabel(self)
        self._provenance.setWordWrap(True)
        self._chart_view = QChartView(self)
        self._chart_view.setMinimumHeight(260)
        self._event_list = QListWidget(self)
        self._event_details = QLabel("Select an event to inspect its complete transition evidence.", self)
        self._event_details.setWordWrap(True)
        self._message = QLabel("Select a transient signal to inspect its complete time series.", self)
        self._message.setWordWrap(True)

        signal_row = QHBoxLayout()
        signal_row.addWidget(QLabel("Signal", self))
        signal_row.addWidget(self._signal_combo, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._provenance)
        layout.addLayout(signal_row)
        layout.addWidget(self._chart_view)
        layout.addWidget(QLabel("Event timeline (solver dispatch order)", self))
        layout.addWidget(self._event_list)
        layout.addWidget(self._event_details)
        layout.addWidget(self._message)

        self._signal_combo.currentIndexChanged.connect(self._render_selected_signal)
        self._event_list.currentRowChanged.connect(self._show_selected_event_details)
        self.setVisible(False)

    def set_result(self, model: TransientResultPresentationReadModel) -> None:
        if not isinstance(model, TransientResultPresentationReadModel):
            raise TypeError("TransientResultViewWidget requires TransientResultPresentationReadModel.")
        self._model = model

        blocked = self._signal_combo.blockSignals(True)
        try:
            self._signal_combo.clear()
            for signal in model.signals:
                self._signal_combo.addItem(
                    f"{signal.label} [{signal.unit}]",
                    signal.signal_id,
                )
            self._signal_combo.setCurrentIndex(0 if model.signals else -1)
        finally:
            self._signal_combo.blockSignals(blocked)

        identity = model.provenance.get("execution_identity", {})
        mode = "ARCHIVED / HISTORICAL" if model.historical else (
            "LIVE / CURRENT" if model.current else "LIVE / STALE"
        )
        details = [
            mode,
            f"Project: {model.project_id}",
            f"Study: {model.study_id}",
            f"Activation: {model.activation_generation}",
            f"Source revision: {model.source_revision}",
            f"Study type/status: {model.study_type} / {model.status}",
            f"Samples: {model.sample_count}",
            f"Signals: {len(model.signals)}",
            f"Events: {len(model.events)}",
        ]
        if model.record_id is not None:
            details.append(f"Archive record: {model.record_id}")
        if model.saved_at:
            details.append(f"Saved at (UTC): {model.saved_at}")
        if model.message:
            details.append(f"Message: {model.message}")
        self._provenance.setText(" | ".join(details))

        self._event_list.clear()
        for index, event in enumerate(model.events, start=1):
            dispatch_label = (
                f"dispatched {event.dispatch_time:.9g} s"
                if event.dispatch_time is not None
                else "dispatch unavailable (scheduled-time marker)"
            )
            line = (
                f"{index}. {event.event_type} — {event.event_id} | "
                f"scheduled {event.scheduled_time:.9g} s / {dispatch_label} | "
                f"{event.status} | "
                f"revision {event.pre_event_revision} → {event.post_event_revision} | "
                f"post-event solve: {event.post_event_re_evaluation_status}"
            )
            if event.failure_type:
                line += f" | {event.failure_type}: {event.failure_message or ''}"
            if event.post_event_re_evaluation_failure_type:
                line += (
                    f" | re-evaluation failure: "
                    f"{event.post_event_re_evaluation_failure_type}: "
                    f"{event.post_event_re_evaluation_failure_message or ''}"
                )
            self._event_list.addItem(line)
        if model.events:
            self._event_list.setCurrentRow(0)
        else:
            self._event_details.setText("No event executions were recorded.")

        if model.historical:
            self._message.setText(
                "Historical archive record. This view is read-only and is never projected onto the live SLD."
            )
        elif not model.current:
            self._message.setText(
                "This live result is stale relative to the current project revision. "
                "Its samples remain inspectable but are not eligible for current SLD projection."
            )
        else:
            self._message.setText(
                "All source samples are rendered in original order. Event markers use recorded dispatch times."
            )

        self.setVisible(True)
        self._render_selected_signal()

    def clear(self) -> None:
        self._model = None
        self._signal_combo.clear()
        self._event_list.clear()
        self._event_details.clear()
        self._provenance.clear()
        self._message.setText("Select a transient result to inspect its time series.")
        self._chart_view.setChart(QChart())
        self.setVisible(False)

    def _show_selected_event_details(self, row: int) -> None:
        model = self._model
        if model is None or row < 0 or row >= len(model.events):
            self._event_details.setText("Select an event to inspect its transition evidence.")
            return
        event = model.events[row]
        details = [
            f"Event: {event.event_id} ({event.event_type})",
            f"Status: {event.status}; priority: {event.priority if event.priority is not None else 'unavailable'}",
            f"Description: {event.description or 'unavailable'}",
            (
                f"Scheduled: {event.scheduled_time:.12g} s; dispatched: {event.dispatch_time:.12g} s"
                if event.dispatch_time is not None
                else f"Scheduled: {event.scheduled_time:.12g} s; dispatch time unavailable (marker uses scheduled time)"
            ),
            f"Detached revision: {event.pre_event_revision} → {event.post_event_revision}",
            f"Post-event algebraic solve: {event.post_event_re_evaluation_status}",
            f"Metadata: {dict(event.metadata)!r}",
            f"Transition result: {event.result!r}",
        ]
        if event.failure_type:
            details.append(f"Action failure: {event.failure_type}: {event.failure_message or ''}")
        if event.post_event_re_evaluation_failure_type:
            details.append(
                "Post-event solve failure: "
                f"{event.post_event_re_evaluation_failure_type}: "
                f"{event.post_event_re_evaluation_failure_message or ''}"
            )
        self._event_details.setText(" | ".join(details))

    def _render_selected_signal(self, _index: int = -1) -> None:
        model = self._model
        if model is None:
            return
        signal_id = self._signal_combo.currentData()
        signal = next((item for item in model.signals if item.signal_id == signal_id), None)
        chart = QChart()
        if signal is None or model.sample_count == 0:
            chart.setTitle("No source samples are available for this signal.")
            self._chart_view.setChart(chart)
            return

        line = QLineSeries()
        line.setName(signal.label)
        for position, source_index in enumerate(signal.source_indices):
            # Source indices are retained by the Application read model and
            # map directly to the original solver time vector.
            line.append(model.time_s[source_index], signal.values[position])
        chart.addSeries(line)

        x_min = model.time_s[0]
        x_max = model.time_s[-1]
        if x_min == x_max:
            x_min -= 0.5
            x_max += 0.5
        y_min = min(signal.values)
        y_max = max(signal.values)
        if y_min == y_max:
            padding = max(abs(y_min) * 0.05, 1e-6)
        else:
            padding = (y_max - y_min) * 0.05
        y_min -= padding
        y_max += padding

        x_axis = QValueAxis(chart)
        x_axis.setTitleText("Time (s)")
        x_axis.setRange(x_min, x_max)
        y_axis = QValueAxis(chart)
        y_axis.setTitleText(signal.unit)
        y_axis.setRange(y_min, y_max)
        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        line.attachAxis(x_axis)
        line.attachAxis(y_axis)

        # Each event marker is a vertical line at the actual recorded dispatch
        # time. The separate event list preserves all events, including events
        # outside the displayed time interval and simultaneous events.
        for event in model.events:
            marker_time = event.marker_time
            if model.time_s[0] <= marker_time <= model.time_s[-1]:
                marker = QLineSeries()
                marker.setName(event.event_id)
                marker.append(marker_time, y_min)
                marker.append(marker_time, y_max)
                chart.addSeries(marker)
                marker.attachAxis(x_axis)
                marker.attachAxis(y_axis)

        chart.setTitle(signal.label)
        chart.legend().hide()
        self._chart_view.setChart(chart)
        self._message.setText(
            f"Displaying {len(signal.values)} of {model.sample_count} source samples "
            f"using original indices {signal.source_indices[0]}–{signal.source_indices[-1]}."
        )


__all__ = ["TransientResultViewWidget"]
