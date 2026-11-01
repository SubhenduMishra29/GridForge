"""Protection engineering capability and curve presentation panels.

These widgets are read-only projections of canonical Core catalog and TCC
read models. They do not create relay elements, alter settings, grade studies,
or issue equipment commands.
"""
from __future__ import annotations

from math import isfinite, log10
from typing import Any

from core.protection import (
    ProtectionFunctionStatus,
    build_protection_tcc_read_model,
    get_protection_function,
    list_protection_functions,
)
from ui.core.qt import (
    QChart,
    QChartView,
    QGroupBox,
    QLabel,
    QLineSeries,
    QTableWidget,
    QTableWidgetItem,
    Qt,
    QValueAxis,
    QVBoxLayout,
    QWidget,
)


class ProtectionFunctionCatalogPanel(QGroupBox):
    """Display every canonical ANSI function and its actual implementation status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("ANSI Protection Function Catalogue", parent)
        self._table = QTableWidget(0, 5, self)
        self._table.setHorizontalHeaderLabels(
            ("ANSI", "Function", "Implementation", "Input contract", "Creation policy")
        )
        self._table.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        self.refresh()

    def refresh(self) -> None:
        codes = list_protection_functions()
        self._table.setRowCount(len(codes))
        for row, code in enumerate(codes):
            specification = get_protection_function(code)
            implementation = (
                specification.implementation.__name__
                if specification.implementation is not None
                else "—"
            )
            contract = specification.input_contract
            if contract is None:
                input_text = "No declared input contract"
            elif not contract.supported:
                input_text = f"FAIL-CLOSED: {contract.unsupported_reason}"
            else:
                input_text = ", ".join(contract.inputs) or "No inputs declared"
            if specification.status is ProtectionFunctionStatus.IMPLEMENTED:
                policy = "Available to factory"
            elif specification.status is ProtectionFunctionStatus.PARTIAL:
                policy = "Blocked until closure"
            else:
                policy = "Unavailable"
            values = (
                specification.code,
                specification.name,
                f"{specification.status.value} · {implementation}",
                input_text,
                policy,
            )
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(str(value)))
        self._table.resizeColumnsToContents()


class ProtectionTCCPanel(QGroupBox):
    """Render an immutable IEC/IEEE TCC read model for the selected 51/51N relay."""

    def __init__(
        self,
        *,
        application: Any,
        selection_manager: Any,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Time-Current Characteristic (TCC)", parent)
        self._application = application
        self._selection_manager = selection_manager
        self._summary = QLabel("Select an ANSI 51 or 51N relay with complete settings.", self)
        self._summary.setWordWrap(True)
        self._chart = QChart()
        self._chart.setTitle("IEC 60255 / IEEE C37.112 inverse-time characteristics")
        self._chart.legend().setVisible(True)
        self._chart_x_axis = QValueAxis()
        self._chart_y_axis = QValueAxis()
        self._chart_x_axis.setTitleText("log10(Current / A)")
        self._chart_y_axis.setTitleText("log10(Operating time / s)")
        self._chart_x_axis.setLabelFormat("%.2f")
        self._chart_y_axis.setLabelFormat("%.2f")
        self._chart.addAxis(self._chart_x_axis, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(self._chart_y_axis, Qt.AlignmentFlag.AlignLeft)
        self._chart_view = QChartView(self._chart, self)
        self._chart_view.setMinimumHeight(260)
        self._table = QTableWidget(0, 5, self)
        self._table.setHorizontalHeaderLabels(("Function element", "Curve", "Current multiple", "Current (A)", "Operating time (s)"))
        self._table.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._summary)
        layout.addWidget(self._chart_view, 2)
        layout.addWidget(self._table, 1)
        selection_manager.selection_changed.connect(lambda _ids: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        self._table.setRowCount(0)
        self._chart.removeAllSeries()
        selected = self._selection_manager.selected_ids
        if not selected:
            self._summary.setText("Select a relay to inspect its configured inverse-time function TCCs.")
            return
        relay_id = str(selected[0]).split(":", 1)[0]
        try:
            protection = self._application.read_protection()
            configurations = self._application.read_protection_configuration()
        except RuntimeError:
            self._summary.setText("Protection read boundary unavailable.")
            return
        relay = next(
            (item for item in protection.relays if str(item.object_id) == relay_id),
            None,
        )
        if relay is None:
            self._summary.setText("The selected presentation object is not a relay.")
            return
        # A physical relay can host multiple independent protection elements.
        # Resolve each function by its canonical element configuration rather
        # than assuming one function_type per physical relay.
        relay_configurations = tuple(
            item for item in configurations if str(item.relay_id) == relay_id
        )
        if not relay_configurations:
            self._summary.setText(
                f"Relay {relay_id} has no configured protection-function elements."
            )
            return

        rows: list[tuple[str, str, str, str, str]] = []
        chart_points: dict[str, list[tuple[float, float]]] = {}
        curve_labels: dict[str, str] = {}
        notices: list[str] = []
        for configuration in relay_configurations:
            code = str(configuration.function_code).strip().upper()
            if code not in {"51", "51N"}:
                notices.append(
                    f"{configuration.element_id}: ANSI {code} does not use an inverse-time TCC in this view."
                )
                continue
            settings = dict(configuration.settings or {})
            pickup = settings.get("pickup")
            curve = settings.get("curve")
            time_dial = settings.get("TMS", settings.get("time_dial"))
            standard = settings.get("curve_standard", "IEC")
            missing = [
                name for name, value in (
                    ("pickup", pickup), ("curve", curve), ("TMS/time_dial", time_dial)
                ) if value is None
            ]
            if missing:
                notices.append(
                    f"{configuration.element_id}: TCC unavailable; missing "
                    + ", ".join(missing)
                    + "."
                )
                continue
            try:
                model = build_protection_tcc_read_model(
                    pickup,
                    curve_standard=standard,
                    curve=curve,
                    time_dial=time_dial,
                    points=31,
                )
            except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
                notices.append(
                    f"{configuration.element_id}: TCC refused: {type(exc).__name__}: {exc}"
                )
                continue
            curve_label = f"{model.curve_standard} {model.curve}"
            element_id = str(configuration.element_id)
            chart_points[element_id] = []
            curve_labels[element_id] = (
                f"{configuration.function_code} · {model.curve_standard} {model.curve}"
            )
            for point in model.points:
                rows.append((
                    element_id,
                    curve_label,
                    f"{point.multiple:.4g}",
                    f"{point.current:.6g}",
                    "∞" if point.time == float("inf") else f"{point.time:.6g}",
                ))
                if (
                    isfinite(point.current)
                    and isfinite(point.time)
                    and point.current > 0.0
                    and point.time > 0.0
                ):
                    chart_points[element_id].append((point.current, point.time))
        self._table.setRowCount(len(rows))
        series_by_element: dict[str, QLineSeries] = {}
        chart_x: list[float] = []
        chart_y: list[float] = []
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))
        for element_id, points in chart_points.items():
            if not points:
                continue
            series = QLineSeries()
            series.setName(f"{element_id} · {curve_labels.get(element_id, 'TCC')}")
            series_by_element[element_id] = series
            self._chart.addSeries(series)
            series.attachAxis(self._chart_x_axis)
            series.attachAxis(self._chart_y_axis)
            for current_a, operating_time_s in points:
                # Plot full-precision Core read-model values, not rounded table text.
                x_value = log10(current_a)
                y_value = log10(operating_time_s)
                series.append(x_value, y_value)
                chart_x.append(x_value)
                chart_y.append(y_value)
        if chart_x and chart_y:
            x_min, x_max = min(chart_x), max(chart_x)
            y_min, y_max = min(chart_y), max(chart_y)
            self._chart_x_axis.setRange(
                x_min - 0.1, x_max + 0.1 if x_max > x_min else x_max + 0.5
            )
            self._chart_y_axis.setRange(
                y_min - 0.1, y_max + 0.1 if y_max > y_min else y_max + 0.5
            )
        self._table.resizeColumnsToContents()
        if rows:
            summary = (
                f"Relay {relay_id}: generated {len(rows)} immutable TCC samples "
                "for configured ANSI 51/51N elements. Current values use each "
                "element's configured pickup basis; CT scaling is not inferred."
            )
        else:
            summary = f"Relay {relay_id}: no eligible ANSI 51/51N TCC was generated."
        if notices:
            summary += "\n\n" + "\n".join(notices)
        self._summary.setText(summary)


class ProtectionCoordinationStudyPanel(QGroupBox):
    """Project actual Protection Study coordination grades as a read-only table."""

    _COLUMNS = (
        "Study / Scenario", "Downstream function", "Downstream current (A)",
        "Downstream time (s)", "Upstream function", "Upstream current (A)",
        "Upstream time (s)", "Breaker clearing (s)", "Available CTI (s)",
        "Required CTI (s)", "Nominal grade", "Tolerance CTI (s)",
        "Tolerance grade", "Tolerance assessment reason",
    )

    def __init__(self, *, application: Any, parent: QWidget | None = None) -> None:
        super().__init__("Protection Coordination Study Results", parent)
        self._application = application
        self._summary = QLabel("No Protection Study coordination results are available.", self)
        self._summary.setWordWrap(True)
        self._table = QTableWidget(0, len(self._COLUMNS), self)
        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._summary)
        layout.addWidget(self._table, 1)
        self.refresh()

    @staticmethod
    def _number(value: Any) -> str:
        if value is None:
            return "—"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number == float("inf"):
            return "∞"
        if number == float("-inf"):
            return "−∞"
        return f"{number:.6g}"

    def refresh(self) -> None:
        self._table.setRowCount(0)
        reader = getattr(self._application, "read_study_results", None)
        if not callable(reader):
            self._summary.setText("Application does not expose the Protection Study result read model.")
            return
        try:
            results = tuple(reader())
        except Exception as exc:
            self._summary.setText(f"Protection Study results unavailable: {type(exc).__name__}: {exc}")
            return

        rows: list[tuple[str, ...]] = []
        stale_rows = 0
        reports_seen = 0
        for result in results:
            if str(getattr(result, "study_type", "")).strip().lower() != "protection":
                continue
            study_id = str(getattr(result, "study_id", "unknown"))
            current = bool(getattr(result, "current", False))
            completed = str(getattr(result, "status", "")).strip().lower() == "completed"
            if not current or not completed:
                stale_rows += 1
                continue
            protection_result = getattr(result, "value", None)
            for scenario in tuple(getattr(protection_result, "fault_scenarios", ()) or ()):
                report = getattr(scenario, "coordination_report", None)
                if report is None:
                    continue
                reports_seen += 1
                for grade in tuple(getattr(report, "grades", ()) or ()):
                    rows.append((
                        study_id,
                        str(getattr(grade, "scenario_id", getattr(scenario, "scenario_id", "unknown"))),
                        str(getattr(grade, "downstream_function_id", "—")),
                        self._number(getattr(grade, "downstream_current_a", None)),
                        self._number(getattr(grade, "downstream_operating_time_s", None)),
                        str(getattr(grade, "upstream_function_id", "—")),
                        self._number(getattr(grade, "upstream_current_a", None)),
                        self._number(getattr(grade, "upstream_operating_time_s", None)),
                        self._number(getattr(grade, "downstream_breaker_clearing_time_s", None)),
                        self._number(getattr(grade, "available_cti_s", None)),
                        self._number(getattr(grade, "required_cti_s", None)),
                        str(getattr(grade, "status", "NOT_EVALUABLE")),
                        self._number(getattr(grade, "tolerance_available_cti_s", None)),
                        str(getattr(grade, "tolerance_status", "NOT_ASSESSED")),
                        str(getattr(grade, "tolerance_reason", "No tolerance assessment reason published.")),
                    ))

        # Include study identity in the first visible column without inventing
        # relationships: each row is copied from one explicit Core grade.
        self._table.setColumnCount(len(self._COLUMNS) + 1)
        self._table.setHorizontalHeaderLabels(("Study ID",) + self._COLUMNS)
        self._table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self._table.setItem(row_index, column, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()
        self._summary.setText(
            f"{len(rows)} explicit coordination grade(s) from {reports_seen} current, "
            f"completed Protection Study report(s). {stale_rows} non-current or "
            "non-completed Protection result(s) were excluded. Tolerance CTI and reason "
            "are taken directly from the Core grade; raw manufacturer envelope bounds "
            "are not retained in this result contract."
            if rows else
            "No current, completed Protection Study contains a static coordination report. "
            f"{stale_rows} non-current or non-completed Protection result(s) were excluded."
        )


class ProtectionAnalysisCoveragePanel(QGroupBox):
    """Expose analysis capability and explicit model boundaries to engineers."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Protection Analysis Coverage", parent)
        self._label = QLabel(self)
        self._label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        self.refresh()

    def refresh(self) -> None:
        self._label.setText(
            "STATIC COORDINATION\n"
            "Application Protection Study grades explicitly configured ANSI 51/51N "
            "pairs against fault-scenario current. Pair identity, CT binding, "
            "breaker clearing time and required CTI are explicit inputs. Missing "
            "or unsupported data produces diagnostics, not a pass.\n\n"
            "TRANSIENT COORDINATION\n"
            "Time-series traces are bound to individual protection functions. "
            "Characteristic-normalized progress requires relay-specific confirmation. "
            "Reset-memory and overshoot require supplied evidence; an unassessed "
            "overshoot cannot produce a COORDINATED grade.\n\n"
            "RL FAULT TRANSIENT\n"
            "The analytical producer is an independent per-phase Thevenin series-RL "
            "model. It reports instantaneous signed primary amperes and a decaying "
            "DC offset. It is not a network EMT solver and is not a CT-secondary or "
            "relay-RMS measurement trace.\n\n"
            "FUNCTION STATUS\n"
            "IMPLEMENTED functions may be constructed through the canonical factory. "
            "PARTIAL functions remain blocked. NOT_IMPLEMENTED functions remain "
            "unavailable. The ANSI catalogue tab shows the live canonical status "
            "and input-contract reason."
        )


__all__ = [
    "ProtectionFunctionCatalogPanel",
    "ProtectionTCCPanel",
    "ProtectionAnalysisCoveragePanel",
    "ProtectionCoordinationStudyPanel",
]
