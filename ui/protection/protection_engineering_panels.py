"""Protection engineering capability and curve presentation panels.

These widgets are read-only projections of canonical Core catalog and TCC
read models. They do not create relay elements, alter settings, grade studies,
or issue equipment commands.
"""
from __future__ import annotations

from typing import Any

from core.protection import (
    ProtectionFunctionStatus,
    build_protection_tcc_read_model,
    get_protection_function,
    list_protection_functions,
)
from ui.core.qt import (
    QGroupBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
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
        self._table = QTableWidget(0, 5, self)
        self._table.setHorizontalHeaderLabels(("Function element", "Curve", "Current multiple", "Current (A)", "Operating time (s)"))
        self._table.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._summary)
        layout.addWidget(self._table, 1)
        selection_manager.selection_changed.connect(lambda _ids: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        self._table.setRowCount(0)
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
            for point in model.points:
                rows.append((
                    str(configuration.element_id),
                    curve_label,
                    f"{point.multiple:.4g}",
                    f"{point.current:.6g}",
                    "∞" if point.time == float("inf") else f"{point.time:.6g}",
                ))
        self._table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))
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
]
