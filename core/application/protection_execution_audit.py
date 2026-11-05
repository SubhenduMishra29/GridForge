"""Durable, Application-owned audit storage for live Protection execution.

This module persists execution evidence only. It does not evaluate Protection,
authorize actions, mutate Core state, or infer field-device acknowledgement.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any, Mapping
from types import MappingProxyType
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProtectionExecutionAuditRecord:
    """Detached immutable row returned by the Protection audit read model."""

    sequence: int
    project_id: str
    activation_generation: int
    cycle_id: str
    record_type: str
    record_key: str
    occurred_at: float
    timestamp_domain: str
    recorded_at: str
    relay_id: str | None
    element_id: str | None
    function_code: str | None
    command_id: str | None
    target_type: str | None
    target_id: str | None
    status: str | None
    payload: Mapping[str, Any]
    previous_hash: str
    record_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, Mapping):
            raise TypeError("audit payload must be a mapping.")
        object.__setattr__(self, "payload", _freeze_json(self.payload))


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    return value


class ProtectionExecutionAuditStore:
    """SQLite-backed append-only audit store with idempotency and hash chaining."""

    def __init__(self, database_path: str | Path) -> None:
        if not isinstance(database_path, (str, Path)) or not str(database_path).strip():
            raise ValueError("database_path must be a non-empty path.")
        self._database_path = Path(database_path).expanduser()
        self._lock = RLock()

    @property
    def database_path(self) -> Path:
        return self._database_path

    @staticmethod
    def _json_value(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, bool)):
            return value
        if isinstance(value, float):
            if math.isfinite(value):
                return value
            return "Infinity" if value > 0 else "-Infinity" if value < 0 else "NaN"
        if isinstance(value, complex):
            return {"real": value.real, "imag": value.imag}
        if isinstance(value, (UUID, Path)):
            return str(value)
        if isinstance(value, Enum):
            return ProtectionExecutionAuditStore._json_value(value.value)
        if isinstance(value, Mapping):
            return {
                str(key): ProtectionExecutionAuditStore._json_value(item)
                for key, item in value.items()
            }
        if isinstance(value, (tuple, list, set, frozenset)):
            return [ProtectionExecutionAuditStore._json_value(item) for item in value]
        if hasattr(value, "__dataclass_fields__"):
            return {
                name: ProtectionExecutionAuditStore._json_value(getattr(value, name))
                for name in value.__dataclass_fields__
            }
        return str(value)

    @classmethod
    def _decision_payload(cls, decision: Any) -> dict[str, Any]:
        return {
            "relay_id": cls._json_value(getattr(decision, "relay_id", None)),
            "element_id": cls._json_value(getattr(decision, "element_id", None)),
            "function_code": getattr(decision, "function_code", None),
            "pickup": getattr(decision, "pickup", None),
            "operate": getattr(decision, "operate", None),
            "trip_request": getattr(decision, "trip_request", None),
            "blocked": getattr(decision, "blocked", None),
            "valid": getattr(decision, "valid", None),
            "actionable": getattr(decision, "actionable", None),
            "operating_time": cls._json_value(getattr(decision, "operating_time", None)),
            "timestamp": cls._json_value(getattr(decision, "timestamp", None)),
            "reason": getattr(decision, "reason", ""),
            "metadata": cls._json_value(getattr(decision, "metadata", {})),
        }

    @classmethod
    def _outcome_payload(cls, outcome: Any) -> dict[str, Any]:
        decision = getattr(outcome, "protection_decision", None)
        control = getattr(outcome, "control_decision", None)
        command = getattr(outcome, "command", None)
        result = getattr(outcome, "application_result", None)
        postcondition = getattr(outcome, "postcondition_verification", None)
        action_type = getattr(control, "action_type", None)
        return {
            "decision": cls._decision_payload(decision) if decision is not None else None,
            "control_action": cls._json_value(action_type),
            "target_type": getattr(control, "target_equipment_type", None),
            "target_id": getattr(control, "target_equipment_id", None),
            "command": None if command is None else {
                "command_id": str(getattr(command, "command_id", "")),
                "command_type": getattr(command, "command_type", None),
                "correlation_id": cls._json_value(getattr(command, "correlation_id", None)),
                "causation_id": cls._json_value(getattr(command, "causation_id", None)),
                "payload": cls._json_value(getattr(command, "payload", {})),
            },
            "application_result": None if result is None else {
                "success": getattr(result, "success", None),
                "message": getattr(result, "message", ""),
                "metadata": cls._json_value(getattr(result, "metadata", {})),
            },
            "status": getattr(outcome, "status", None),
            "diagnostic": getattr(outcome, "diagnostic", ""),
            "core_state_observation": getattr(outcome, "core_state_observation", "unknown/unavailable"),
            "physical_acknowledgement": "unknown/unavailable",
            "postcondition": None if postcondition is None else {
                "command_id": getattr(postcondition, "command_id", None),
                "target_equipment_type": getattr(postcondition, "target_equipment_type", None),
                "target_equipment_id": getattr(postcondition, "target_equipment_id", None),
                "action_type": getattr(postcondition, "action_type", None),
                "status": cls._json_value(getattr(postcondition, "status", None)),
                "expected_state": getattr(postcondition, "expected_state", None),
                "observed_state": getattr(postcondition, "observed_state", None),
                "diagnostic": getattr(postcondition, "diagnostic", ""),
                "observed_at": getattr(postcondition, "observed_at", None),
                "timestamp_domain": getattr(postcondition, "timestamp_domain", "unknown"),
            },
        }

    def _connect(self) -> sqlite3.Connection:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path, timeout=0.1)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=100")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS protection_execution_audit ("
            "sequence INTEGER PRIMARY KEY AUTOINCREMENT, "
            "project_id TEXT NOT NULL, activation_generation INTEGER NOT NULL, "
            "cycle_id TEXT NOT NULL, record_type TEXT NOT NULL, record_key TEXT NOT NULL, "
            "occurred_at REAL NOT NULL, timestamp_domain TEXT NOT NULL DEFAULT 'protection_evaluation', "
            "recorded_at TEXT NOT NULL, "
            "relay_id TEXT, element_id TEXT, function_code TEXT, command_id TEXT, "
            "target_type TEXT, target_id TEXT, status TEXT, payload_json TEXT NOT NULL, "
            "previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL, "
            "UNIQUE(project_id, activation_generation, cycle_id, record_type, record_key))"
        )
        columns = {
            row["name"] for row in connection.execute(
                "PRAGMA table_info(protection_execution_audit)"
            ).fetchall()
        }
        if "timestamp_domain" not in columns:
            connection.execute(
                "ALTER TABLE protection_execution_audit ADD COLUMN "
                "timestamp_domain TEXT NOT NULL DEFAULT 'protection_evaluation'"
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_protection_audit_project_domain_time "
            "ON protection_execution_audit(project_id, timestamp_domain, occurred_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_protection_audit_relay "
            "ON protection_execution_audit(project_id, relay_id, occurred_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_protection_audit_element "
            "ON protection_execution_audit(project_id, element_id, occurred_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_protection_audit_command "
            "ON protection_execution_audit(project_id, command_id)"
        )
        connection.execute(
            "CREATE TRIGGER IF NOT EXISTS protection_audit_no_update "
            "BEFORE UPDATE ON protection_execution_audit "
            "BEGIN SELECT RAISE(ABORT, 'Protection audit records are append-only'); END"
        )
        connection.execute(
            "CREATE TRIGGER IF NOT EXISTS protection_audit_no_delete "
            "BEFORE DELETE ON protection_execution_audit "
            "BEGIN SELECT RAISE(ABORT, 'Protection audit records are append-only'); END"
        )
        return connection

    @staticmethod
    def _identity(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def _insert_rows(self, rows: tuple[dict[str, Any], ...]) -> int:
        if not rows:
            return 0
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                previous = connection.execute(
                    "SELECT record_hash FROM protection_execution_audit "
                    "ORDER BY sequence DESC LIMIT 1"
                ).fetchone()
                previous_hash = previous["record_hash"] if previous else "GENESIS"
                inserted = 0
                for row in rows:
                    exists = connection.execute(
                        "SELECT 1 FROM protection_execution_audit WHERE "
                        "project_id=? AND activation_generation=? AND cycle_id=? "
                        "AND record_type=? AND record_key=?",
                        (
                            row["project_id"], row["activation_generation"], row["cycle_id"],
                            row["record_type"], row["record_key"],
                        ),
                    ).fetchone()
                    if exists:
                        continue
                    command_id = row.get("command_id")
                    if command_id and row["record_type"] in {"DISPATCH_INTENT", "OUTCOME"}:
                        prior_command = connection.execute(
                            "SELECT cycle_id FROM protection_execution_audit WHERE "
                            "project_id=? AND command_id=? "
                            "AND record_type IN ('DISPATCH_INTENT', 'OUTCOME') LIMIT 1",
                            (row["project_id"], command_id),
                        ).fetchone()
                        if prior_command is not None and prior_command["cycle_id"] != row["cycle_id"]:
                            raise ValueError(
                                f"Command identity {command_id!r} is already assigned to "
                                f"Protection cycle {prior_command['cycle_id']!r}."
                            )
                    recorded_at = datetime.now(timezone.utc).isoformat()
                    canonical = json.dumps(
                        {
                            **row,
                            "recorded_at": recorded_at,
                            "previous_hash": previous_hash,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    )
                    record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                    connection.execute(
                        "INSERT INTO protection_execution_audit "
                        "(project_id, activation_generation, cycle_id, record_type, record_key, "
                        "occurred_at, timestamp_domain, recorded_at, relay_id, element_id, function_code, command_id, "
                        "target_type, target_id, status, payload_json, previous_hash, record_hash) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            row["project_id"], row["activation_generation"], row["cycle_id"],
                            row["record_type"], row["record_key"], row["occurred_at"],
                            row["timestamp_domain"], recorded_at, row.get("relay_id"), row.get("element_id"),
                            row.get("function_code"), row.get("command_id"), row.get("target_type"),
                            row.get("target_id"), row.get("status"), row["payload_json"],
                            previous_hash, record_hash,
                        ),
                    )
                    previous_hash = record_hash
                    inserted += 1
                connection.commit()
                return inserted
            except BaseException:
                connection.rollback()
                raise
            finally:
                connection.close()

    def _row(
        self, *, project_id: str, activation_generation: int, cycle_id: str,
        record_type: str, record_key: str, occurred_at: float, payload: Mapping[str, Any],
        timestamp_domain: str = "protection_evaluation",
        relay_id: Any = None, element_id: Any = None, function_code: Any = None,
        command_id: Any = None, target_type: Any = None, target_id: Any = None, status: Any = None,
    ) -> dict[str, Any]:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be non-empty.")
        if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if not isinstance(cycle_id, str) or not cycle_id.strip():
            raise ValueError("cycle_id must be non-empty.")
        if isinstance(occurred_at, bool) or not isinstance(occurred_at, (int, float)) or not math.isfinite(occurred_at):
            raise ValueError("occurred_at must be a finite timestamp.")
        if not isinstance(timestamp_domain, str) or not timestamp_domain.strip():
            raise ValueError("timestamp_domain must be a non-empty string.")
        encoded = json.dumps(self._json_value(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        return {
            "project_id": project_id,
            "activation_generation": activation_generation,
            "cycle_id": cycle_id,
            "record_type": record_type,
            "record_key": record_key,
            "occurred_at": float(occurred_at),
            "timestamp_domain": timestamp_domain,
            "relay_id": self._identity(relay_id),
            "element_id": self._identity(element_id),
            "function_code": self._identity(function_code),
            "command_id": self._identity(command_id),
            "target_type": self._identity(target_type),
            "target_id": self._identity(target_id),
            "status": self._identity(status),
            "payload_json": encoded,
        }

    def begin_cycle(
        self, *, project_id: str, activation_generation: int, cycle_id: str,
        occurred_at: float, metadata: Mapping[str, Any],
    ) -> bool:
        row = self._row(
            project_id=project_id, activation_generation=activation_generation,
            cycle_id=cycle_id, record_type="CYCLE_STARTED", record_key=cycle_id,
            occurred_at=occurred_at, payload={"metadata": metadata, "state": "in_progress"},
            status="in_progress",
        )
        return self._insert_rows((row,)) == 1

    def append_decisions(
        self, *, project_id: str, activation_generation: int, cycle_id: str,
        occurred_at: float, decisions: tuple[Any, ...], metadata: Mapping[str, Any],
    ) -> int:
        """Persist the complete immutable decision set before action dispatch."""
        rows = []
        for decision in decisions:
            payload = {
                "decision": self._decision_payload(decision),
                "cycle_metadata": metadata,
                "physical_acknowledgement": "unknown/unavailable",
            }
            element_id = self._identity(getattr(decision, "element_id", None)) or "unknown"
            rows.append(self._row(
                project_id=project_id, activation_generation=activation_generation,
                cycle_id=cycle_id, record_type="DECISION", record_key=element_id,
                occurred_at=occurred_at, payload=payload,
                relay_id=getattr(decision, "relay_id", None), element_id=element_id,
                function_code=getattr(decision, "function_code", None),
                status="actionable" if getattr(decision, "actionable", False) else "non_actionable",
            ))
        return self._insert_rows(tuple(rows))

    def append_dispatch_intent(
        self, *, project_id: str, activation_generation: int, cycle_id: str,
        occurred_at: float, decision: Any, control_decision: Any, command: Any,
    ) -> bool:
        """Persist command identity and target before crossing the dispatcher boundary."""
        action_type = getattr(control_decision, "action_type", None)
        action_value = getattr(action_type, "value", action_type)
        command_id = str(getattr(command, "command_id", ""))
        element_id = self._identity(getattr(decision, "element_id", None)) or "unknown"
        payload = {
            "decision": self._decision_payload(decision),
            "action_type": action_value,
            "target_type": getattr(control_decision, "target_equipment_type", None),
            "target_id": getattr(control_decision, "target_equipment_id", None),
            "command": {
                "command_id": command_id,
                "command_type": getattr(command, "command_type", None),
                "correlation_id": self._json_value(getattr(command, "correlation_id", None)),
                "causation_id": self._json_value(getattr(command, "causation_id", None)),
                "payload": self._json_value(getattr(command, "payload", {})),
            },
            "dispatch_state": "intent_persisted_before_dispatch",
            "commit_boundary_status": "unknown",
            "physical_acknowledgement": "unknown/unavailable",
        }
        row = self._row(
            project_id=project_id, activation_generation=activation_generation,
            cycle_id=cycle_id, record_type="DISPATCH_INTENT",
            record_key=command_id, occurred_at=occurred_at, payload=payload,
            relay_id=getattr(decision, "relay_id", None), element_id=element_id,
            function_code=getattr(decision, "function_code", None),
            command_id=command_id,
            target_type=getattr(control_decision, "target_equipment_type", None),
            target_id=getattr(control_decision, "target_equipment_id", None),
            status="dispatch_intent",
        )
        return self._insert_rows((row,)) == 1

    def append_cycle(
        self, *, project_id: str, activation_generation: int, cycle_id: str,
        occurred_at: float, metadata: Mapping[str, Any], result: Any,
    ) -> int:
        rows: list[dict[str, Any]] = []
        decisions = tuple(getattr(result, "decisions", ()))
        outcomes = tuple(getattr(result, "outcomes", ()))
        rows.append(self._row(
            project_id=project_id, activation_generation=activation_generation,
            cycle_id=cycle_id, record_type="CYCLE_COMPLETED", record_key=cycle_id,
            occurred_at=occurred_at,
            payload={
                "metadata": metadata, "decision_count": len(decisions),
                "command_count": len(getattr(result, "commands", ())),
                "diagnostics": tuple(getattr(result, "diagnostics", ())),
                "physical_acknowledgement": "unknown/unavailable",
            },
            status="completed",
        ))
        for decision in decisions:
            payload = self._decision_payload(decision)
            element_id = self._identity(getattr(decision, "element_id", None)) or "unknown"
            rows.append(self._row(
                project_id=project_id, activation_generation=activation_generation,
                cycle_id=cycle_id, record_type="DECISION", record_key=element_id,
                occurred_at=occurred_at, payload=payload,
                relay_id=getattr(decision, "relay_id", None), element_id=element_id,
                function_code=getattr(decision, "function_code", None),
                status="actionable" if getattr(decision, "actionable", False) else "non_actionable",
            ))
        for outcome in outcomes:
            payload = self._outcome_payload(outcome)
            decision = getattr(outcome, "protection_decision", None)
            element_id = self._identity(getattr(decision, "element_id", None)) or "unknown"
            control = getattr(outcome, "control_decision", None)
            command = getattr(outcome, "command", None)
            rows.append(self._row(
                project_id=project_id, activation_generation=activation_generation,
                cycle_id=cycle_id, record_type="OUTCOME", record_key=element_id,
                occurred_at=occurred_at, payload=payload,
                relay_id=getattr(decision, "relay_id", None), element_id=element_id,
                function_code=getattr(decision, "function_code", None),
                command_id=getattr(command, "command_id", None),
                target_type=getattr(control, "target_equipment_type", None),
                target_id=getattr(control, "target_equipment_id", None),
                status=getattr(outcome, "status", None),
            ))
        return self._insert_rows(tuple(rows))

    def append_failure(
        self, *, project_id: str, activation_generation: int, cycle_id: str,
        occurred_at: float, diagnostic: str, metadata: Mapping[str, Any] | None = None,
    ) -> bool:
        row = self._row(
            project_id=project_id, activation_generation=activation_generation,
            cycle_id=cycle_id, record_type="CYCLE_FAILED", record_key=cycle_id,
            occurred_at=occurred_at,
            payload={"diagnostic": diagnostic, "metadata": metadata or {},
                     "physical_acknowledgement": "unknown/unavailable"},
            status="failed",
        )
        return self._insert_rows((row,)) == 1

    def append_field_feedback(
        self, *, project_id: str, activation_generation: int, cycle_id: str,
        feedback_id: str, command_id: str, source_id: str, source_timestamp: float,
        correlation_id: str, delivery_status: str, acknowledgement_status: str,
        quality_status: str, authenticity_status: str, timestamp_domain: str,
        delivery_id: str | None = None, acknowledgement_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> bool:
        if not all(isinstance(value, str) and value.strip() for value in (
            feedback_id, command_id, source_id, correlation_id, delivery_status,
            acknowledgement_status, quality_status, authenticity_status, timestamp_domain,
        )):
            raise ValueError("Field feedback identities and status fields must be non-empty strings.")
        for name, value in (("delivery_id", delivery_id), ("acknowledgement_id", acknowledgement_id)):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty string or None.")
        body = {
            "source_id": source_id, "source_timestamp": source_timestamp,
            "delivery_id": delivery_id, "acknowledgement_id": acknowledgement_id,
            "correlation_id": correlation_id, "delivery_status": delivery_status,
            "acknowledgement_status": acknowledgement_status,
            "quality_status": quality_status, "authenticity_status": authenticity_status,
            "timestamp_domain": timestamp_domain, "payload": payload or {},
        }
        with self._lock:
            connection = self._connect()
            try:
                exists = connection.execute(
                    "SELECT 1 FROM protection_execution_audit WHERE project_id=? "
                    "AND activation_generation=? AND cycle_id=? AND command_id=?",
                    (project_id, activation_generation, cycle_id, command_id),
                ).fetchone()
            finally:
                connection.close()
        if exists is None:
            raise ValueError("Field feedback must correlate to an existing audited command in the same project cycle.")
        row = self._row(
            project_id=project_id, activation_generation=activation_generation,
            cycle_id=cycle_id, record_type="FIELD_FEEDBACK", record_key=feedback_id,
            occurred_at=source_timestamp, timestamp_domain=timestamp_domain,
            payload=body, command_id=command_id, status=acknowledgement_status,
        )
        return self._insert_rows((row,)) == 1

    def query(
        self, *, project_id: str, start_time: float | None = None,
        end_time: float | None = None, relay_id: str | None = None,
        element_id: str | None = None, command_id: str | None = None,
        cycle_id: str | None = None, timestamp_domain: str | None = None,
        limit: int = 500,
    ) -> tuple[ProtectionExecutionAuditRecord, ...]:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required for Protection audit queries.")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5000:
            raise ValueError("limit must be an integer from 1 to 5000.")
        if (start_time is not None or end_time is not None) and (
            not isinstance(timestamp_domain, str) or not timestamp_domain.strip()
        ):
            raise ValueError("timestamp_domain is required when filtering by time.")
        clauses = ["project_id=?"]
        values: list[Any] = [project_id]
        if timestamp_domain is not None:
            clauses.append("timestamp_domain=?")
            values.append(timestamp_domain)
        for bound, operator in ((start_time, ">="), (end_time, "<=")):
            if bound is not None:
                if isinstance(bound, bool) or not isinstance(bound, (int, float)) or not math.isfinite(bound):
                    raise ValueError("occurred_at filters must be finite.")
                clauses.append(f"occurred_at{operator} ?")
                values.append(float(bound))
        for column, value in (
            ("relay_id", relay_id), ("element_id", element_id),
            ("command_id", command_id), ("cycle_id", cycle_id),
        ):
            if value is not None:
                clauses.append(f"{column}=?")
                values.append(value)
        values.append(limit)
        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute(
                    "SELECT * FROM protection_execution_audit WHERE "
                    + " AND ".join(clauses) + " ORDER BY sequence DESC LIMIT ?",
                    values,
                ).fetchall()
            finally:
                connection.close()
        return tuple(ProtectionExecutionAuditRecord(
            sequence=row["sequence"], project_id=row["project_id"],
            activation_generation=row["activation_generation"], cycle_id=row["cycle_id"],
            record_type=row["record_type"], record_key=row["record_key"],
            occurred_at=row["occurred_at"], timestamp_domain=row["timestamp_domain"],
            recorded_at=row["recorded_at"],
            relay_id=row["relay_id"], element_id=row["element_id"],
            function_code=row["function_code"], command_id=row["command_id"],
            target_type=row["target_type"], target_id=row["target_id"],
            status=row["status"], payload=json.loads(row["payload_json"]),
            previous_hash=row["previous_hash"], record_hash=row["record_hash"],
        ) for row in rows)

    def verify_integrity(self) -> tuple[bool, int | None]:
        """Verify the append-only hash chain; return validity and first bad sequence."""
        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute(
                    "SELECT * FROM protection_execution_audit ORDER BY sequence"
                ).fetchall()
            finally:
                connection.close()
        previous_hash = "GENESIS"
        for row in rows:
            if row["previous_hash"] != previous_hash:
                return False, int(row["sequence"])
            canonical_row = {
                "project_id": row["project_id"],
                "activation_generation": row["activation_generation"],
                "cycle_id": row["cycle_id"],
                "record_type": row["record_type"],
                "record_key": row["record_key"],
                "occurred_at": row["occurred_at"],
                "timestamp_domain": row["timestamp_domain"],
                "relay_id": row["relay_id"],
                "element_id": row["element_id"],
                "function_code": row["function_code"],
                "command_id": row["command_id"],
                "target_type": row["target_type"],
                "target_id": row["target_id"],
                "status": row["status"],
                "payload_json": row["payload_json"],
                "recorded_at": row["recorded_at"],
                "previous_hash": previous_hash,
            }
            encoded = json.dumps(
                canonical_row, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            )
            actual = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            if actual != row["record_hash"]:
                return False, int(row["sequence"])
            previous_hash = actual
        return True, None

    def read_cycle(self, *, project_id: str, cycle_id: str) -> tuple[ProtectionExecutionAuditRecord, ...]:
        return self.query(project_id=project_id, cycle_id=cycle_id, limit=5000)


__all__ = ["ProtectionExecutionAuditRecord", "ProtectionExecutionAuditStore"]
