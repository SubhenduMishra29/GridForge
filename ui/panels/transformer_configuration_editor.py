# ============================================================
# GridForge V2 — Dedicated Transformer Configuration Editor
# ============================================================

"""Engineer-facing Transformer configuration surface.

The widget owns only staged presentation values. All accepted edits are
translated to an immutable Application intent and committed through the
existing Application command pipeline.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from ui.core.qt import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from ui.projection.projection_state import ProjectionState
from .engineering_parameter_editor import (
    EngineeringConfigurationIntent,
    EngineeringParameterEditor,
)


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, complex):
        return [value.real, value.imag]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _json_value(getattr(value, item.name)) for item in fields(value)}
    return value


def _json_text(value: Any) -> str:
    if value is None:
        return ""
    return json.dumps(_json_value(value), separators=(",", ":"), sort_keys=True)


def _parse_json(control: QLineEdit, field: str, *, blank: Any = None) -> Any:
    raw = control.text().strip()
    if not raw:
        return blank
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field} must contain valid JSON: {exc.msg}.") from exc


def _parse_optional_complex(control: QLineEdit, field: str) -> Any:
    value = _parse_json(control, field)
    if value is None:
        return None
    if isinstance(value, dict) and set(value) == {"real", "imag"}:
        return {"real": float(value["real"]), "imag": float(value["imag"])}
    if isinstance(value, list) and len(value) == 2:
        return [float(value[0]), float(value[1])]
    raise ValueError(f"{field} must be blank or a JSON [real, imag] pair.")


class TransformerConfigurationEditor(QWidget):
    """Staged winding, test-evidence and multiport editor for one Transformer."""

    _TEXT_FIELDS = (
        "hv_winding_connection", "lv_winding_connection",
        "hv_terminal_role", "lv_terminal_role",
        "hv_neutral_terminal_role", "lv_neutral_terminal_role",
        "hv_neutral_grounding_impedance_ohm", "lv_neutral_grounding_impedance_ohm",
        "hv_neutral_earth_return_impedance_ohm", "lv_neutral_earth_return_impedance_ohm",
        "hv_phase_roles", "lv_phase_roles", "core_construction",
        "impedance_reference_winding", "zero_sequence_test_basis",
        "zero_sequence_resistance_ohm", "zero_sequence_reactance_ohm",
        "vector_group_configuration", "zero_sequence_test_configuration",
        "zero_sequence_two_winding_test_data",
        "phase_domain_terminal_admittance_siemens",
        "zero_sequence_multiport_evidence", "phase_domain_delta_loop_states",
        "phase_domain_multiport_tap_ratio", "phase_domain_multiport_phase_shift_rad",
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TransformerConfigurationEditor")
        self._target: ProjectionState | None = None
        self._editor: EngineeringParameterEditor | None = None
        self._controls: dict[str, QLineEdit] = {}
        self._status = QLabel("Select a committed Transformer to configure winding and multiport data.", self)
        self._status.setWordWrap(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 8)

        winding_group = QGroupBox("Winding construction and zero-sequence tests", self)
        winding_form = QFormLayout(winding_group)
        for field, label, hint in (
            ("hv_winding_connection", "HV winding connection", "Core winding-connection value"),
            ("lv_winding_connection", "LV winding connection", "Core winding-connection value"),
            ("hv_terminal_role", "HV terminal role", "SLD terminal role"),
            ("lv_terminal_role", "LV terminal role", "SLD terminal role"),
            ("hv_neutral_terminal_role", "HV neutral terminal role", "Blank when no neutral terminal is declared"),
            ("lv_neutral_terminal_role", "LV neutral terminal role", "Blank when no neutral terminal is declared"),
            ("hv_phase_roles", "HV ordered phase roles", 'JSON array, e.g. ["A","B","C"]'),
            ("lv_phase_roles", "LV ordered phase roles", 'JSON array, e.g. ["A","B","C"]'),
            ("hv_neutral_grounding_impedance_ohm", "HV neutral grounding impedance (ohm)", "JSON [real, imag]"),
            ("lv_neutral_grounding_impedance_ohm", "LV neutral grounding impedance (ohm)", "JSON [real, imag]"),
            ("hv_neutral_earth_return_impedance_ohm", "HV neutral earth-return impedance (ohm)", "JSON [real, imag] or null"),
            ("lv_neutral_earth_return_impedance_ohm", "LV neutral earth-return impedance (ohm)", "JSON [real, imag] or null"),
            ("core_construction", "Core construction", "THREE_LIMB, FIVE_LIMB or SHELL_FORM"),
            ("impedance_reference_winding", "Impedance reference winding", "HV or LV"),
            ("zero_sequence_test_basis", "Zero-sequence test basis", "Manufacturer/test basis identifier"),
            ("zero_sequence_resistance_ohm", "Zero-sequence resistance (ohm)", "Measured/test value"),
            ("zero_sequence_reactance_ohm", "Zero-sequence reactance (ohm)", "Measured/test value"),
            ("vector_group_configuration", "Vector-group contract", "JSON object with connection, clock_number and polarity declarations"),
            ("zero_sequence_test_configuration", "Zero-sequence test contract", "JSON object with energized_winding and test conditions"),
            ("zero_sequence_two_winding_test_data", "Two-winding test data", "JSON object matching the typed test-data contract"),
        ):
            control = QLineEdit(winding_group)
            control.setPlaceholderText(hint)
            self._controls[field] = control
            winding_form.addRow(label, control)
        root.addWidget(winding_group)

        multiport_group = QGroupBox("Externally supplied terminal-admittance multiport", self)
        multiport_form = QFormLayout(multiport_group)
        self._matrix_table = QTableWidget(multiport_group)
        self._matrix_table.setObjectName("TransformerTerminalAdmittanceMatrix")
        self._matrix_grid_button = QPushButton("Build / load ordered terminal matrix grid", multiport_group)
        self._matrix_grid_button.clicked.connect(self._build_matrix_grid)
        multiport_form.addRow("Ordered terminal matrix", self._matrix_grid_button)
        multiport_form.addRow("Admittance matrix (S)", self._matrix_table)
        for field, label, hint in (
            ("phase_domain_terminal_admittance_siemens", "Terminal admittance matrix (S)", "JSON square matrix; each complex cell is [real, imag]"),
            ("zero_sequence_multiport_evidence", "Manufacturer / test evidence", 'JSON object: {"core_zero_sequence_test_reference":"...","delta_circulating_test_references":{"HV":"..."} }'),
            ("phase_domain_delta_loop_states", "Internal delta-loop states", "JSON array of explicit loop-state records; not external terminal currents"),
            ("phase_domain_multiport_tap_ratio", "Matrix tap-ratio snapshot", "Numeric ratio used when the matrix was supplied"),
            ("phase_domain_multiport_phase_shift_rad", "Matrix phase-shift snapshot (rad)", "Numeric phase shift used when the matrix was supplied"),
        ):
            control = QLineEdit(multiport_group)
            control.setPlaceholderText(hint)
            control.setToolTip(hint)
            self._controls[field] = control
            multiport_form.addRow(label, control)
        root.addWidget(multiport_group)

        note = QLabel(
            "Matrix data is explicit manufacturer/test input; it is never synthesized from scalar r/x or vector-group labels. "
            "Use SIEMENS for matrix values. Core/Application validation remains authoritative for terminal ordering, "
            "dimensions, grounding, topology and evidence fingerprints.",
            self,
        )
        note.setWordWrap(True)
        root.addWidget(note)

        actions = QHBoxLayout()
        self._apply_winding = QPushButton("Apply Winding / Test Configuration", self)
        self._apply_multiport = QPushButton("Apply Multiport and Evidence", self)
        self._cancel = QPushButton("Discard Staged Edits", self)
        actions.addWidget(self._apply_winding)
        actions.addWidget(self._apply_multiport)
        actions.addWidget(self._cancel)
        root.addLayout(actions)
        root.addWidget(self._status)
        self._apply_winding.clicked.connect(self._submit_winding)
        self._apply_multiport.clicked.connect(self._submit_multiport)
        self._cancel.clicked.connect(self._restore_projection)
        self.setVisible(False)

    def bind_application(self, application: Any) -> None:
        self._editor = EngineeringParameterEditor(application)

    def set_target(self, target: ProjectionState | None) -> None:
        self._target = target if target is not None and str(target.display_type).lower() in {"transformer", "transformers"} else None
        visible = self._target is not None and self._target.identity_kind == "element"
        self.setVisible(visible)
        if not visible:
            self._status.setText("Select a committed Transformer to configure winding and multiport data.")
            return
        self._load_projection()

    def _summary(self) -> Mapping[str, Any]:
        if self._target is None:
            return {}
        value = self._target.attributes.get("transformer_configuration_summary", {})
        return value if isinstance(value, Mapping) else {}

    def _load_projection(self) -> None:
        summary = self._summary()
        mapping = {
            "hv_winding_connection": "hv_winding_connection",
            "lv_winding_connection": "lv_winding_connection",
            "hv_terminal_role": "hv_terminal_role",
            "lv_terminal_role": "lv_terminal_role",
            "hv_neutral_terminal_role": "hv_neutral_terminal_role",
            "lv_neutral_terminal_role": "lv_neutral_terminal_role",
            "hv_neutral_grounding_impedance_ohm": "hv_neutral_grounding_impedance_ohm",
            "lv_neutral_grounding_impedance_ohm": "lv_neutral_grounding_impedance_ohm",
            "hv_neutral_earth_return_impedance_ohm": "hv_neutral_earth_return_impedance_ohm",
            "lv_neutral_earth_return_impedance_ohm": "lv_neutral_earth_return_impedance_ohm",
            "hv_phase_roles": "hv_phase_roles",
            "lv_phase_roles": "lv_phase_roles",
            "core_construction": "core_construction",
            "impedance_reference_winding": "impedance_reference_winding",
            "zero_sequence_test_basis": "zero_sequence_test_basis",
            "zero_sequence_resistance_ohm": "zero_sequence_resistance_ohm",
            "zero_sequence_reactance_ohm": "zero_sequence_reactance_ohm",
            "vector_group_configuration": "vector_group",
            "zero_sequence_test_configuration": "zero_sequence_test",
            "zero_sequence_two_winding_test_data": "zero_sequence_two_winding_test_data",
            "phase_domain_terminal_admittance_siemens": "phase_domain_terminal_admittance_siemens",
            "zero_sequence_multiport_evidence": "zero_sequence_multiport_evidence",
            "phase_domain_delta_loop_states": "phase_domain_delta_loop_states",
            "phase_domain_multiport_tap_ratio": "phase_domain_multiport_tap_ratio",
            "phase_domain_multiport_phase_shift_rad": "phase_domain_multiport_phase_shift_rad",
        }
        for field, key in mapping.items():
            value = summary.get(key)
            if field in {"hv_neutral_grounding_impedance_ohm", "lv_neutral_grounding_impedance_ohm",
                         "hv_neutral_earth_return_impedance_ohm", "lv_neutral_earth_return_impedance_ohm"}:
                rendered = _json_text(value)
            elif field in {"hv_phase_roles", "lv_phase_roles", "vector_group_configuration",
                           "zero_sequence_test_configuration", "zero_sequence_two_winding_test_data",
                           "phase_domain_terminal_admittance_siemens", "zero_sequence_multiport_evidence",
                           "phase_domain_delta_loop_states"}:
                rendered = _json_text(value)
            else:
                rendered = "" if value is None else str(_json_value(value))
            self._controls[field].setText(rendered)
        self._load_matrix_table(summary.get("phase_domain_terminal_admittance_siemens"))
        self._status.setText(
            f"Transformer {self._target.object_id}: staged values are read-only until an Apply action. "
            "Discard restores the latest projected configuration."
        )

    def _terminal_labels(self) -> tuple[str, ...]:
        labels: list[str] = []
        for winding, field, neutral_field in (
            ("HV", "hv_phase_roles", "hv_neutral_terminal_role"),
            ("LV", "lv_phase_roles", "lv_neutral_terminal_role"),
        ):
            roles = _parse_json(self._controls[field], field, blank=[])
            if not isinstance(roles, list) or any(not isinstance(role, str) or not role.strip() for role in roles):
                raise ValueError(f"{field} must be a JSON array of ordered phase roles.")
            labels.extend(f"{winding}:{role.strip()}" for role in roles)
            if self._controls[neutral_field].text().strip():
                labels.append(f"{winding}:N")
        if len(labels) < 2 or len(set(labels)) != len(labels):
            raise ValueError("The winding inventory must produce a unique ordered terminal list.")
        return tuple(labels)

    def _load_matrix_table(self, matrix: Any) -> None:
        if matrix is None:
            self._matrix_table.setRowCount(0)
            self._matrix_table.setColumnCount(0)
            return
        self._build_matrix_grid(matrix)

    def _build_matrix_grid(self, matrix: Any = None) -> None:
        labels = self._terminal_labels()
        if matrix is None:
            matrix = _parse_json(
                self._controls["phase_domain_terminal_admittance_siemens"],
                "phase_domain_terminal_admittance_siemens",
            )
        if matrix is not None and (
            not isinstance(matrix, (tuple, list))
            or len(matrix) != len(labels)
            or any(not isinstance(row, (tuple, list)) or len(row) != len(labels) for row in matrix)
        ):
            raise ValueError("Matrix dimensions must match the current ordered HV/LV terminal inventory.")
        self._matrix_table.setRowCount(len(labels))
        self._matrix_table.setColumnCount(len(labels))
        self._matrix_table.setHorizontalHeaderLabels(list(labels))
        self._matrix_table.setVerticalHeaderLabels(list(labels))
        for row in range(len(labels)):
            for column in range(len(labels)):
                value = "" if matrix is None else matrix[row][column]
                if isinstance(value, Mapping):
                    rendered = f"{value.get('real', 0.0)},{value.get('imag', 0.0)}"
                elif isinstance(value, (tuple, list)) and len(value) == 2:
                    rendered = f"{value[0]},{value[1]}"
                elif isinstance(value, complex):
                    rendered = f"{value.real},{value.imag}"
                else:
                    rendered = "" if value is None else str(value)
                self._matrix_table.setItem(row, column, QTableWidgetItem(rendered))
        self._status.setText("Matrix grid terminal order: " + ", ".join(labels))

    def _matrix_from_grid(self) -> list[list[list[float]]]:
        labels = self._terminal_labels()
        if self._matrix_table.rowCount() != len(labels) or self._matrix_table.columnCount() != len(labels):
            raise ValueError("Build the matrix grid after confirming the ordered winding terminal inventory.")
        matrix: list[list[list[float]]] = []
        for row in range(len(labels)):
            cells: list[list[float]] = []
            for column in range(len(labels)):
                item = self._matrix_table.item(row, column)
                raw = "" if item is None else item.text().strip()
                if not raw:
                    raise ValueError(f"Matrix cell {labels[row]} × {labels[column]} is empty.")
                parts = [part.strip() for part in raw.split(",")]
                if len(parts) == 1:
                    real, imag = float(parts[0]), 0.0
                elif len(parts) == 2:
                    real, imag = float(parts[0]), float(parts[1])
                else:
                    raise ValueError(f"Matrix cell {labels[row]} × {labels[column]} must be real or real,imag.")
                cells.append([real, imag])
            matrix.append(cells)
        self._controls["phase_domain_terminal_admittance_siemens"].setText(_json_text(matrix))
        return matrix

    def _base_inventory(self) -> dict[str, Any]:
        def text(field: str) -> str:
            return self._controls[field].text().strip()
        def optional_text(field: str) -> str | None:
            return text(field) or None
        def string_array(field: str) -> tuple[str, ...]:
            value = _parse_json(self._controls[field], field, blank=[])
            if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError(f"{field} must be a JSON array of non-empty strings in terminal order.")
            return tuple(item.strip() for item in value)
        hv_roles = string_array("hv_phase_roles")
        lv_roles = string_array("lv_phase_roles")
        if not hv_roles or not lv_roles:
            raise ValueError("Explicit non-empty HV and LV phase-role arrays are required.")
        for field in ("hv_winding_connection", "lv_winding_connection", "hv_terminal_role", "lv_terminal_role", "core_construction"):
            if not text(field):
                raise ValueError(f"{field} is required for a complete Transformer winding inventory.")
        return {
            "hv_winding_connection": text("hv_winding_connection"),
            "lv_winding_connection": text("lv_winding_connection"),
            "hv_terminal_role": text("hv_terminal_role"),
            "lv_terminal_role": text("lv_terminal_role"),
            "hv_neutral_terminal_role": optional_text("hv_neutral_terminal_role"),
            "lv_neutral_terminal_role": optional_text("lv_neutral_terminal_role"),
            "hv_phase_roles": hv_roles,
            "lv_phase_roles": lv_roles,
            "core_construction": text("core_construction"),
            "hv_neutral_grounding_impedance_ohm": _parse_optional_complex(self._controls["hv_neutral_grounding_impedance_ohm"], "hv_neutral_grounding_impedance_ohm"),
            "lv_neutral_grounding_impedance_ohm": _parse_optional_complex(self._controls["lv_neutral_grounding_impedance_ohm"], "lv_neutral_grounding_impedance_ohm"),
            "hv_neutral_earth_return_impedance_ohm": _parse_optional_complex(self._controls["hv_neutral_earth_return_impedance_ohm"], "hv_neutral_earth_return_impedance_ohm"),
            "lv_neutral_earth_return_impedance_ohm": _parse_optional_complex(self._controls["lv_neutral_earth_return_impedance_ohm"], "lv_neutral_earth_return_impedance_ohm"),
            "replace_physical_conductor_configuration": True,
        }

    def _winding_values(self) -> dict[str, Any]:
        values = self._base_inventory()
        for field in ("impedance_reference_winding", "zero_sequence_test_basis"):
            value = self._controls[field].text().strip()
            if value:
                values[field] = value
        for field in ("zero_sequence_resistance_ohm", "zero_sequence_reactance_ohm"):
            raw = self._controls[field].text().strip()
            if raw:
                values[field] = float(raw)
        for field in ("vector_group_configuration", "zero_sequence_test_configuration", "zero_sequence_two_winding_test_data"):
            value = _parse_json(self._controls[field], field)
            if value is not None:
                values[field] = value
        return values

    def _submit_winding(self) -> None:
        try:
            self._submit(self._winding_values(), "Winding and zero-sequence test configuration accepted.")
        except (RuntimeError, TypeError, ValueError, OverflowError) as exc:
            self._status.setText(f"Transformer configuration rejected: {exc}")

    def _submit_multiport(self) -> None:
        try:
            values = self._winding_values()
            matrix = self._matrix_from_grid() if self._matrix_table.rowCount() else _parse_json(self._controls["phase_domain_terminal_admittance_siemens"], "phase_domain_terminal_admittance_siemens")
            evidence = _parse_json(self._controls["zero_sequence_multiport_evidence"], "zero_sequence_multiport_evidence")
            loops = _parse_json(self._controls["phase_domain_delta_loop_states"], "phase_domain_delta_loop_states", blank=[])
            if matrix is not None and (not isinstance(matrix, list) or not matrix or any(not isinstance(row, list) for row in matrix)):
                raise ValueError("The terminal admittance matrix must be a non-empty JSON row matrix.")
            if not isinstance(loops, list):
                raise ValueError("Delta-loop states must be a JSON array.")
            values.update({
                "phase_domain_terminal_admittance_siemens": matrix,
                "zero_sequence_multiport_evidence": evidence,
                "phase_domain_delta_loop_states": loops,
                "phase_domain_multiport_tap_ratio": self._optional_float("phase_domain_multiport_tap_ratio"),
                "phase_domain_multiport_phase_shift_rad": self._optional_float("phase_domain_multiport_phase_shift_rad"),
                "replace_phase_domain_multiport_configuration": True,
            })
            self._submit(values, "Transformer multiport and evidence configuration accepted.")
        except (RuntimeError, TypeError, ValueError, OverflowError) as exc:
            self._status.setText(f"Transformer multiport rejected: {exc}")

    def _optional_float(self, field: str) -> float | None:
        raw = self._controls[field].text().strip()
        return None if not raw else float(raw)

    def _submit(self, values: Mapping[str, Any], success_message: str) -> None:
        if self._target is None or self._editor is None:
            raise RuntimeError("Transformer editor is not bound to a selected Transformer and Application.")
        if self._target.identity_kind != "element":
            raise ValueError("Transformer engineering configuration is available only for committed elements.")
        intent = EngineeringConfigurationIntent(
            element_type="transformer",
            element_id=self._target.object_id,
            values=values,
            identity_kind="element",
        )
        result = self._editor.submit(intent)
        if not getattr(result, "success", False):
            raise ValueError(getattr(result, "message", None) or "Application rejected the Transformer update.")
        self._status.setText(success_message + " The Application command completed; the projected read model remains authoritative.")
        
    def _restore_projection(self) -> None:
        self._load_projection()


__all__ = ["TransformerConfigurationEditor"]
