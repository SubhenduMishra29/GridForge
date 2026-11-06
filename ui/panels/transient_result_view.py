"""Dedicated presentation widget for complete transient-stability results."""

from __future__ import annotations

from bisect import bisect_right
from time import monotonic

from core.application.read_models import TransientResultPresentationReadModel
from core.application.transient_playback import (
    TransientPlaybackFrameReadModel,
    build_transient_playback_frame,
)
from ui.core.qt import (
    QChart,
    QChartView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineSeries,
    QListWidget,
    QValueAxis,
    QPushButton,
    QSlider,
    QTimer,
    Signal,
    QVBoxLayout,
    Qt,
    QWidget,
)


class TransientResultViewWidget(QWidget):
    playback_frame_changed = Signal(object)
    """Inspect complete transient signals and ordered event history.

    The widget renders every source sample. It does not down-sample, interpolate,
    reorder or regenerate solver data.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgeTransientResultView")
        self._model: TransientResultPresentationReadModel | None = None
        self._playback_index = 0
        self._playing = False
        self._last_tick = 0.0
        self._playback_clock_s = 0.0
        self._play_timer = QTimer(self)
        self._play_timer.setInterval(33)
        self._play_timer.timeout.connect(self._advance_playback)
        self._play_button = QPushButton("Play", self)
        self._pause_button = QPushButton("Pause", self)
        self._stop_button = QPushButton("Stop", self)
        self._previous_button = QPushButton("Step −", self)
        self._next_button = QPushButton("Step +", self)
        self._rate_combo = QComboBox(self)
        for label, rate in (("0.25×", 0.25), ("0.5×", 0.5), ("1×", 1.0), ("2×", 2.0), ("4×", 4.0)):
            self._rate_combo.addItem(label, rate)
        self._rate_combo.setCurrentIndex(2)
        self._timeline = QSlider(Qt.Orientation.Horizontal, self)
        self._timeline.setRange(0, 0)
        self._timeline.setEnabled(False)
        self._time_label = QLabel("t = — s", self)
        self._cursor_series = None
        self._cursor_y_range = (0.0, 1.0)
        self._signal_combo = QComboBox(self)
        self._provenance = QLabel(self)
        self._provenance.setWordWrap(True)
        self._solver_provenance = QLabel(self)
        self._solver_provenance.setWordWrap(True)
        self._chart_view = QChartView(self)
        self._chart_view.setMinimumHeight(260)
        self._event_list = QListWidget(self)
        self._event_details = QLabel("Select an event to inspect its complete transition evidence.", self)
        self._quality_list = QListWidget(self)
        self._discontinuity_list = QListWidget(self)
        self._discontinuity_details = QLabel("Select an event boundary to inspect its pre/post electrical states.", self)
        self._discontinuity_details.setWordWrap(True)
        self._quality_details = QLabel("Select a recorded sample to inspect algebraic solver quality.", self)
        self._quality_details.setWordWrap(True)
        self._event_details.setWordWrap(True)
        self._message = QLabel("Select a transient signal to inspect its complete time series.", self)
        self._message.setWordWrap(True)

        signal_row = QHBoxLayout()
        signal_row.addWidget(QLabel("Signal", self))
        signal_row.addWidget(self._signal_combo, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._provenance)
        layout.addWidget(self._solver_provenance)
        layout.addLayout(signal_row)
        playback_row = QHBoxLayout()
        playback_row.addWidget(self._play_button)
        playback_row.addWidget(self._pause_button)
        playback_row.addWidget(self._stop_button)
        playback_row.addWidget(self._previous_button)
        playback_row.addWidget(self._next_button)
        playback_row.addWidget(QLabel("Rate", self))
        playback_row.addWidget(self._rate_combo)
        playback_row.addWidget(self._time_label)
        layout.addLayout(playback_row)
        layout.addWidget(self._timeline)
        layout.addWidget(self._chart_view)
        layout.addWidget(QLabel("Event timeline (solver dispatch order)", self))
        layout.addWidget(self._event_list)
        layout.addWidget(self._event_details)
        layout.addWidget(QLabel("Algebraic solver quality (recorded samples)", self))
        layout.addWidget(self._quality_list)
        layout.addWidget(self._quality_details)
        layout.addWidget(QLabel("Event discontinuities (pre/post sides)", self))
        layout.addWidget(self._discontinuity_list)
        layout.addWidget(self._discontinuity_details)
        layout.addWidget(self._message)

        self._signal_combo.currentIndexChanged.connect(self._render_selected_signal)
        self._play_button.clicked.connect(self.play)
        self._pause_button.clicked.connect(self.pause)
        self._stop_button.clicked.connect(self.stop)
        self._previous_button.clicked.connect(lambda: self.step(-1))
        self._next_button.clicked.connect(lambda: self.step(1))
        self._timeline.valueChanged.connect(self.seek)
        self._play_button.setEnabled(False)
        self._pause_button.setEnabled(False)
        self._stop_button.setEnabled(False)
        self._previous_button.setEnabled(False)
        self._next_button.setEnabled(False)
        self._event_list.currentRowChanged.connect(self._show_selected_event_details)
        self._quality_list.currentRowChanged.connect(self._show_selected_quality_details)
        self._discontinuity_list.currentRowChanged.connect(self._show_selected_discontinuity_details)
        self.setVisible(False)

    def set_result(self, model: TransientResultPresentationReadModel) -> None:
        if not isinstance(model, TransientResultPresentationReadModel):
            raise TypeError("TransientResultViewWidget requires TransientResultPresentationReadModel.")
        self.pause()
        self.playback_frame_changed.emit(None)
        self._model = model
        playable = model.status == "completed" and model.sample_count > 0
        slider_blocked = self._timeline.blockSignals(True)
        try:
            self._timeline.setRange(0, max(0, model.sample_count - 1))
        finally:
            self._timeline.blockSignals(slider_blocked)
        self._timeline.setEnabled(playable)
        for control in (self._play_button, self._stop_button, self._previous_button, self._next_button):
            control.setEnabled(playable)
        self._pause_button.setEnabled(False)

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
            f"Algebraic quality records: {len(model.algebraic_quality)}",
            f"Event discontinuities: {len(model.discontinuities)}",
        ]
        if model.record_id is not None:
            details.append(f"Archive record: {model.record_id}")
        if model.saved_at:
            details.append(f"Saved at (UTC): {model.saved_at}")
        if model.message:
            details.append(f"Message: {model.message}")
        self._provenance.setText(" | ".join(details))
        provenance_keys = (
            "machine_connections",
            "switch_connections",
            "initial_switch_states",
            "final_switch_states",
            "switch_availability_states",
            "final_detached_network_revision",
            "state_signals",
        )
        solver_details = {
            key: model.provenance[key]
            for key in provenance_keys
            if key in model.provenance
        }
        self._solver_provenance.setText(
            f"Solver provenance: {solver_details!r}" if solver_details else "Solver provenance: no additional fields recorded."
        )

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

        self._quality_list.clear()
        for quality in model.algebraic_quality:
            if quality.accepted and quality.quality_verified:
                quality_label = "VERIFIED / ACCEPTED"
            elif not quality.accepted:
                quality_label = f"{quality.status} / REJECTED"
                if not quality.quality_verified:
                    quality_label += " / quality unverified"
            else:
                quality_label = f"{quality.status} / accepted, quality unverified"
            self._quality_list.addItem(
                f"Sample {quality.sample_index} — {quality.time_s:.9g} s — {quality_label}"
            )
        if model.algebraic_quality:
            self._quality_list.setCurrentRow(0)
        else:
            self._quality_details.setText(
                "Algebraic solver quality was not persisted for this result. "
                "No legacy quality records have been inferred or generated."
            )

        self._discontinuity_list.clear()
        for item in model.discontinuities:
            self._discontinuity_list.addItem(
                f"{item.time_s:.9g} s — {', '.join(item.event_ids)} — {item.post_status}"
            )
        if model.discontinuities:
            self._discontinuity_list.setCurrentRow(0)
        else:
            self._discontinuity_details.setText("No event discontinuity sides were recorded.")

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
                "All source samples are rendered in original order. Playback steps exact recorded samples without interpolation; event markers use recorded dispatch times."
            )

        self.setVisible(True)
        self._render_selected_signal()
        if playable:
            self._set_playback_index(0, emit_frame=True)

    def clear(self) -> None:
        self.pause()
        self.playback_frame_changed.emit(None)
        self._model = None
        self._timeline.setRange(0, 0)
        self._timeline.setEnabled(False)
        self._time_label.setText("t = — s")
        for control in (self._play_button, self._pause_button, self._stop_button, self._previous_button, self._next_button):
            control.setEnabled(False)
        self._signal_combo.clear()
        self._event_list.clear()
        self._event_details.clear()
        self._quality_list.clear()
        self._quality_details.clear()
        self._discontinuity_list.clear()
        self._discontinuity_details.clear()
        self._provenance.clear()
        self._solver_provenance.clear()
        self._message.setText("Select a transient result to inspect its time series.")
        self._chart_view.setChart(QChart())
        self._cursor_series = None
        self.setVisible(False)

    def play(self) -> None:
        """Start wall-clock playback over recorded samples only."""
        model = self._model
        if model is None or model.status != "completed" or model.sample_count == 0:
            return
        if self._playback_index >= model.sample_count - 1:
            self._set_playback_index(0, emit_frame=True)
        self._playing = True
        self._playback_clock_s = model.time_s[self._playback_index]
        self._last_tick = monotonic()
        self._play_timer.start()
        self._play_button.setEnabled(False)
        self._pause_button.setEnabled(True)

    def pause(self) -> None:
        self._play_timer.stop()
        self._playing = False
        self._play_button.setEnabled(self._model is not None and self._model.status == "completed" and self._model.sample_count > 0)
        self._pause_button.setEnabled(False)

    def stop(self) -> None:
        self.pause()
        if self._model is not None and self._model.sample_count:
            self._set_playback_index(0, emit_frame=True)

    def seek(self, sample_index: int) -> None:
        if self._model is None or not self._model.sample_count:
            return
        self._set_playback_index(int(sample_index), emit_frame=True)
        self._playback_clock_s = self._model.time_s[self._playback_index]
        self._last_tick = monotonic()

    def step(self, offset: int) -> None:
        self.pause()
        if self._model is None or not self._model.sample_count:
            return
        self._set_playback_index(self._playback_index + int(offset), emit_frame=True)

    def _set_playback_index(self, sample_index: int, *, emit_frame: bool) -> None:
        model = self._model
        if model is None or not model.sample_count:
            return
        index = max(0, min(int(sample_index), model.sample_count - 1))
        self._playback_index = index
        blocked = self._timeline.blockSignals(True)
        try:
            self._timeline.setValue(index)
        finally:
            self._timeline.blockSignals(blocked)
        time_s = model.time_s[index]
        self._playback_clock_s = time_s
        self._time_label.setText(f"Sample {index + 1}/{model.sample_count}  |  t = {time_s:.9g} s")
        if self._cursor_series is not None:
            self._cursor_series.clear()
            self._cursor_series.append(time_s, self._cursor_y_range[0])
            self._cursor_series.append(time_s, self._cursor_y_range[1])
        if emit_frame:
            frame = build_transient_playback_frame(model, index)
            self.playback_frame_changed.emit(frame)

    def _advance_playback(self) -> None:
        model = self._model
        if not self._playing or model is None or not model.sample_count:
            self.pause()
            return
        now = monotonic()
        elapsed = max(0.0, now - self._last_tick)
        self._last_tick = now
        rate = float(self._rate_combo.currentData() or 1.0)
        self._playback_clock_s += elapsed * rate
        target_time = self._playback_clock_s
        if target_time >= model.time_s[-1]:
            self._set_playback_index(model.sample_count - 1, emit_frame=True)
            self.pause()
            return
        index = max(0, bisect_right(model.time_s, target_time) - 1)
        if index != self._playback_index:
            self._set_playback_index(index, emit_frame=True)

    def hideEvent(self, event) -> None:
        self.pause()
        self.playback_frame_changed.emit(None)
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        self.pause()
        self.playback_frame_changed.emit(None)
        super().closeEvent(event)

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

    def _show_selected_discontinuity_details(self, row: int) -> None:
        model = self._model
        if model is None or row < 0 or row >= len(model.discontinuities):
            self._discontinuity_details.setText("Select an event boundary to inspect its pre/post electrical states.")
            return
        item = model.discontinuities[row]
        details = [
            f"Boundary: {item.time_s:.12g} s",
            f"Events: {item.event_ids}",
            f"Post-state status: {item.post_status}",
            f"Pre-event dynamic state: {item.pre_state!r}",
            f"Pre-event terminal voltages: {dict(item.pre_terminal_voltages)!r}",
            f"Pre-event electrical powers: {dict(item.pre_electrical_powers)!r}",
            f"Pre-event topology revision: {item.pre_topology_revision}",
        ]
        if item.post_status == "succeeded":
            details.extend((
                f"Post-event dynamic state: {item.post_state!r}",
                f"Post-event terminal voltages: {dict(item.post_terminal_voltages or {})!r}",
                f"Post-event electrical powers: {dict(item.post_electrical_powers or {})!r}",
                f"Post-event topology revision: {item.post_topology_revision}",
            ))
        else:
            details.append("Post-event electrical solution: unavailable; no successful post-state is claimed.")
            details.append(f"Observed detached topology revision after dispatch: {item.post_topology_revision}")
        self._discontinuity_details.setText(" | ".join(details))

    def _show_selected_quality_details(self, row: int) -> None:
        model = self._model
        if model is None or row < 0 or row >= len(model.algebraic_quality):
            self._quality_details.setText("Select a recorded sample to inspect algebraic solver quality.")
            return
        quality = model.algebraic_quality[row]

        def display(value: object) -> str:
            return "unavailable" if value is None else str(value)

        details = [
            f"Recorded sample: {quality.sample_index} at {quality.time_s:.12g} s",
            f"Solver-reported time: {display(quality.solver_time_s)}",
            f"Status: {quality.status}",
            f"Accepted: {quality.accepted}; quality verified: {quality.quality_verified}",
            f"Solver: {quality.solver_name}",
            (
                f"Absolute residual: {display(quality.absolute_residual_norm)}; "
                f"normalized residual: {display(quality.normalized_residual)}; "
                f"tolerance: {display(quality.residual_tolerance)}"
            ),
            (
                f"Condition estimate: {display(quality.condition_number)}; "
                f"limit: {display(quality.condition_limit)}"
            ),
            f"Bus IDs: {quality.bus_ids}",
            f"Topology revision: {display(quality.topology_revision)}",
            f"Source IDs: {quality.source_ids}",
            (
                f"Active fault: {display(quality.active_fault_id)} / "
                f"{display(quality.active_fault_type)} / Bus {display(quality.active_fault_bus_id)}"
            ),
            f"Bus voltages: {dict(quality.bus_voltages)!r}",
            f"Study provenance: {dict(quality.study_provenance)!r}",
        ]
        if quality.diagnostics:
            details.append(f"Diagnostics: {'; '.join(quality.diagnostics)}")
        self._quality_details.setText(" | ".join(details))

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

        cursor = QLineSeries()
        cursor.setName("Playback cursor")
        cursor_time = model.time_s[self._playback_index]
        cursor.append(cursor_time, y_min)
        cursor.append(cursor_time, y_max)
        chart.addSeries(cursor)
        cursor.attachAxis(x_axis)
        cursor.attachAxis(y_axis)
        self._cursor_series = cursor
        self._cursor_y_range = (y_min, y_max)

        chart.setTitle(signal.label)
        chart.legend().hide()
        self._chart_view.setChart(chart)
        self._message.setText(
            f"Displaying {len(signal.values)} of {model.sample_count} source samples "
            f"using original indices {signal.source_indices[0]}–{signal.source_indices[-1]}."
        )


__all__ = ["TransientResultViewWidget"]
