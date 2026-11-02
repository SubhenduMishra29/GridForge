"""Durable append-only audit for live protection execution outcomes.

The store is Application infrastructure. It records facts already established by
the protection execution path; it never creates decisions or device feedback.
"""
from __future__ import annotations

from datetime import datetime, timezone
from contextlib import closing
import json
import math
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any, Callable, Mapping


class ProtectionExecutionAuditStore:
    """SQLite-backed append-only protection audit, partitioned by project ID."""

    def __init__(self, database_path_provider: Callable[[str], str | Path]) -> None:
        if not callable(database_path_provider):
            raise TypeError("database_path_provider must be callable.")
        self._database_path_provider = database_path_provider
        self._lock = RLock()

    @staticmethod
    def _json_value(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, complex):
            return {"real": value.real, "imag": value.imag}
        if isinstance(value, Mapping):
            return {str(key): ProtectionExecutionAuditStore._json_value(item) for key, item in value.items()}
        if isinstance(value, (tuple, list, set, frozenset)):
            return [ProtectionExecutionAuditStore._json_value(item) for item in value]
        return str(value)

    @classmethod
    def _result_payload(cls, result: Any) -> dict[str, Any]:
        outcomes = []
        for item in getattr(result, "outcomes", ()):
            decision = item.protection_decision
            control = item.control_decision
            command = item.command
            application_result = item.application_result
            postcondition = item.postcondition_verification
            outcomes.append({
                "element_id": getattr(decision, "element_id", None),
                "function_code": getattr(decision, "function_code", None),
                "actionable": getattr(decision, "actionable", None),
                "decision_reason": getattr(decision, "reason", None),
                "control_action": getattr(getattr(control, "action_type", None), "value", None),
                "target_type": getattr(control, "target_equipment_type", None),
                "target_id": getattr(control, "target_equipment_id", None),
                "command_id": str(getattr(command, "command_id", "")) or None,
                "command_type": getattr(command, "command_type", None),
                "application_success": getattr(application_result, "success", None),
                "application_message": getattr(application_result, "message", None),
                "status": item.status,
                "diagnostic": item.diagnostic,
                "core_state_observation": item.core_state_observation,
                "physical_acknowledgement": item.physical_acknowledgement,
                "postcondition": None if postcondition is None else {
                    "status": postcondition.status.value,
                    "expected": postcondition.expected_state,
                    "observed": postcondition.observed_state,
                    "diagnostic": postcondition.diagnostic,
                },
                "field_device_delivery_status": getattr(item, "field_device_delivery_status", "not_configured"),
                "field_device_acknowledgement_id": getattr(item, "field_device_acknowledgement_id", None),
            })
        return {
            "decisions": len(getattr(result, "decisions", ())),
            "diagnostics": list(getattr(result, "diagnostics", ())),
            "outcomes": outcomes,
        }

    def append(
        self,
        *,
        project_id: str,
        activation_generation: int,
        event_id: str,
        event_type: str,
        occurred_at: float,
        payload: Mapping[str, Any],
    ) -> bool:
        """Append one immutable event; duplicate event IDs are idempotently ignored."""
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be non-empty.")
        if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("activation_generation must be positive.")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be non-empty.")
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("event_type must be non-empty.")
        if isinstance(occurred_at, bool) or not isinstance(occurred_at, (int, float)) or not math.isfinite(occurred_at):
            raise TypeError("occurred_at must be a finite numeric timestamp.")
        path = Path(self._database_path_provider(project_id)).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(self._json_value(payload), sort_keys=True, separators=(",", ":"), allow_nan=False)
        with self._lock, closing(sqlite3.connect(path, timeout=10.0)) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS protection_execution_audit ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, "
                "activation_generation INTEGER NOT NULL, event_id TEXT NOT NULL, "
                "event_type TEXT NOT NULL, occurred_at REAL NOT NULL, recorded_at TEXT NOT NULL, "
                "payload_json TEXT NOT NULL, UNIQUE(project_id, activation_generation, event_id, event_type))"
            )
            connection.execute(
                "CREATE TRIGGER IF NOT EXISTS protection_audit_no_update "
                "BEFORE UPDATE ON protection_execution_audit "
                "BEGIN SELECT RAISE(ABORT, 'protection audit is append-only'); END"
            )
            connection.execute(
                "CREATE TRIGGER IF NOT EXISTS protection_audit_no_delete "
                "BEFORE DELETE ON protection_execution_audit "
                "BEGIN SELECT RAISE(ABORT, 'protection audit is append-only'); END"
            )
            cursor = connection.execute(
                "INSERT OR IGNORE INTO protection_execution_audit "
                "(project_id, activation_generation, event_id, event_type, occurred_at, recorded_at, payload_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project_id, activation_generation, event_id, event_type, float(occurred_at),
                 datetime.now(timezone.utc).isoformat(), encoded),
            )
            connection.commit()
            return cursor.rowcount == 1

    def claim_cycle(self, *, project_id: str, activation_generation: int,
                    event_id: str, occurred_at: float, attestation: Any) -> bool:
        """Durably reserve a cycle identity before any protection command can dispatch.

        A crash after claim is intentionally left as an auditable in-progress
        record; automatic replay is not allowed to risk a duplicate trip.
        """
        payload = {
            "producer_id": getattr(attestation, "producer_id", None),
            "channel_id": getattr(attestation, "channel_id", None),
            "sample_sequence": getattr(attestation, "sample_sequence", None),
            "source_timestamp": getattr(attestation, "timestamp", None),
            "timestamp_domain": getattr(attestation, "timestamp_domain", None),
            "claim_state": "claimed_before_evaluation",
        }
        return self.append(
            project_id=project_id, activation_generation=activation_generation,
            event_id=event_id, event_type="PROTECTION_CYCLE_CLAIMED",
            occurred_at=occurred_at, payload=payload,
        )

    def append_cycle(self, *, project_id: str, activation_generation: int,
                     event_id: str, occurred_at: float, attestation: Any, result: Any) -> bool:
        attestation_data = {
            "producer_id": getattr(attestation, "producer_id", None),
            "channel_id": getattr(attestation, "channel_id", None),
            "sample_sequence": getattr(attestation, "sample_sequence", None),
            "source_timestamp": getattr(attestation, "timestamp", None),
            "timestamp_domain": getattr(attestation, "timestamp_domain", None),
        }
        return self.append(
            project_id=project_id, activation_generation=activation_generation,
            event_id=event_id, event_type="PROTECTION_CYCLE_COMPLETED",
            occurred_at=occurred_at,
            payload={"attestation": attestation_data, "execution": self._result_payload(result)},
        )

    def append_execution(self, *, project_id: str, activation_generation: int,
                         event_id: str, occurred_at: float, metadata: Mapping[str, Any],
                         result: Any) -> bool:
        return self.append(
            project_id=project_id, activation_generation=activation_generation,
            event_id=event_id, event_type="PROTECTION_CYCLE_EXECUTED",
            occurred_at=occurred_at,
            payload={"metadata": self._json_value(metadata),
                     "execution": self._result_payload(result)},
        )

    def append_watchdog(self, *, project_id: str, activation_generation: int,
                        event_id: str, occurred_at: float, findings: Any) -> bool:
        return self.append(
            project_id=project_id, activation_generation=activation_generation,
            event_id=event_id, event_type="MEASUREMENT_WATCHDOG",
            occurred_at=occurred_at,
            payload={"findings": self._json_value(findings)},
        )


__all__ = ["ProtectionExecutionAuditStore"]
