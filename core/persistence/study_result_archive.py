"""Versioned durable archive for detached Application StudyResult values.

Study outputs are execution artifacts, not project configuration. This archive
stores them beside the user's GridForge application data, keyed by project and
activation provenance, without modifying the canonical .gridforge package.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Any, Mapping
from uuid import UUID, uuid4

import numpy as np

from core.application.revision import ProjectRevision
from core.application.study import StudyResult
from core.solver.short_circuit.result import ShortCircuitTransformerDeltaLoopCurrent


ARCHIVE_FORMAT = "GridForgeStudyResult"
ARCHIVE_SCHEMA_VERSION = 1


class StudyResultArchiveError(RuntimeError):
    """Raised when a Study Result archive cannot be written or restored."""


@dataclass(frozen=True, slots=True)
class ArchivedStudyResult:
    """One durable StudyResult plus its archive record identity and timestamp."""

    record_id: UUID
    saved_at: str
    result: StudyResult

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, UUID):
            raise TypeError("record_id must be a UUID.")
        if not isinstance(self.saved_at, str) or not self.saved_at.strip():
            raise ValueError("saved_at must be a non-empty ISO timestamp.")
        if not isinstance(self.result, StudyResult):
            raise TypeError("result must be a StudyResult.")


def _qualified_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _encode_value(value: Any) -> Any:
    """Encode supported result values explicitly; reject unknown runtime objects."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise StudyResultArchiveError("Study Result contains a non-finite float.")
        return value
    if isinstance(value, ShortCircuitTransformerDeltaLoopCurrent):
        return {
            "$type": "ShortCircuitTransformerDeltaLoopCurrent",
            "value": value.to_dict(),
        }
    if isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise StudyResultArchiveError("Study Result contains a non-finite complex value.")
        return {"$type": "complex", "real": value.real, "imag": value.imag}
    if isinstance(value, UUID):
        return {"$type": "uuid", "value": str(value)}
    if isinstance(value, Enum):
        return {"$type": "enum", "class": _qualified_name(value), "value": _encode_value(value.value)}
    if isinstance(value, np.ndarray):
        return _encode_value(value.tolist())
    if isinstance(value, np.generic):
        return _encode_value(value.item())
    if isinstance(value, Mapping):
        encoded: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise StudyResultArchiveError("Study Result mapping keys must be strings.")
            encoded[key] = _encode_value(item)
        return encoded
    if isinstance(value, (tuple, list)):
        return [_encode_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_encode_value(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "$type": "dataclass",
            "class": _qualified_name(value),
            "fields": {item.name: _encode_value(getattr(value, item.name)) for item in fields(value)},
        }
    raise StudyResultArchiveError(
        f"Study Result contains unsupported runtime value: {type(value).__name__}."
    )


def _decode_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_decode_value(item) for item in value)
    if not isinstance(value, Mapping):
        return value
    kind = value.get("$type")
    if kind == "complex" and set(value) == {"$type", "real", "imag"}:
        real, imag = float(value["real"]), float(value["imag"])
        if not math.isfinite(real) or not math.isfinite(imag):
            raise StudyResultArchiveError("Persisted complex value is not finite.")
        return complex(real, imag)
    if kind == "uuid" and set(value) == {"$type", "value"}:
        return UUID(str(value["value"]))
    if kind == "ShortCircuitTransformerDeltaLoopCurrent" and set(value) == {"$type", "value"}:
        return ShortCircuitTransformerDeltaLoopCurrent.from_dict(value["value"])
    if kind == "enum" and set(value) == {"$type", "class", "value"}:
        # Preserve the enum's canonical value without importing arbitrary
        # classes from persisted data.
        return _decode_value(value["value"])
    if kind == "dataclass" and set(value) == {"$type", "class", "fields"}:
        payload = value["fields"]
        if not isinstance(payload, Mapping):
            raise StudyResultArchiveError("Persisted dataclass fields must be an object.")
        return {
            "$dataclass": value["class"],
            "fields": {key: _decode_value(item) for key, item in payload.items()},
        }
    return {key: _decode_value(item) for key, item in value.items()}


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise StudyResultArchiveError(f"Study Result is not canonical JSON: {exc}") from exc


class StudyResultArchive:
    """Append-only, versioned persistence for detached StudyResult executions.

    The archive is deliberately outside the .gridforge project package:
    project configuration saves cannot overwrite or discard study history.
    """

    def __init__(self, root: str | Path) -> None:
        if not isinstance(root, (str, Path)) or not str(root).strip():
            raise ValueError("Study Result archive root must be a non-empty path.")
        self._root = Path(root).expanduser()
        self._lock = RLock()

    @property
    def root(self) -> Path:
        return self._root

    @staticmethod
    def _project_key(project_id: str) -> str:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        return hashlib.sha256(project_id.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def _revision_payload(revision: ProjectRevision) -> dict[str, int]:
        return {
            "model_revision": revision.model_revision,
            "topology_revision": revision.topology_revision,
            "presentation_revision": revision.presentation_revision,
            "persisted_revision": revision.persisted_revision,
        }

    @classmethod
    def _result_payload(cls, result: StudyResult) -> dict[str, Any]:
        return {
            "study_id": str(result.study_id),
            "project_id": result.project_id,
            "activation_generation": result.activation_generation,
            "source_revision": cls._revision_payload(result.source_revision),
            "study_type": result.study_type,
            "status": result.status,
            "value": _encode_value(result.value),
            "message": result.message,
            "metadata": _encode_value(result.metadata),
        }

    def save(self, result: StudyResult) -> ArchivedStudyResult:
        if not isinstance(result, StudyResult):
            raise TypeError("result must be a StudyResult.")
        record_id = uuid4()
        saved_at = datetime.now(timezone.utc).isoformat()
        payload = self._result_payload(result)
        envelope_without_digest = {
            "format": ARCHIVE_FORMAT,
            "schema_version": ARCHIVE_SCHEMA_VERSION,
            "record_id": str(record_id),
            "saved_at": saved_at,
            "payload": payload,
        }
        digest = hashlib.sha256(_canonical_json(envelope_without_digest)).hexdigest()
        envelope = {**envelope_without_digest, "payload_sha256": digest}
        encoded = _canonical_json(envelope)
        directory = (
            self._root
            / self._project_key(result.project_id)
            / str(result.activation_generation)
        )
        target = directory / f"{result.study_id}.{record_id}.json"
        with self._lock:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=".study-result-", suffix=".tmp", dir=directory
                )
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(encoded)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary_name, target)
                except Exception:
                    try:
                        os.unlink(temporary_name)
                    except FileNotFoundError:
                        pass
                    raise
            except Exception as exc:
                raise StudyResultArchiveError(f"Unable to archive Study Result: {exc}") from exc
        return ArchivedStudyResult(record_id=record_id, saved_at=saved_at, result=result)

    def _read(self, path: Path, *, expected_project_id: str | None = None) -> ArchivedStudyResult:
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(envelope, Mapping):
                raise StudyResultArchiveError("Study Result archive record must be an object.")
            if envelope.get("format") != ARCHIVE_FORMAT:
                raise StudyResultArchiveError("Unsupported Study Result archive format.")
            if envelope.get("schema_version") != ARCHIVE_SCHEMA_VERSION:
                raise StudyResultArchiveError(
                    f"Unsupported Study Result archive schema: {envelope.get('schema_version')!r}."
                )
            payload = envelope.get("payload")
            if not isinstance(payload, Mapping):
                raise StudyResultArchiveError("Study Result archive payload must be an object.")
            unsigned = {key: envelope[key] for key in ("format", "schema_version", "record_id", "saved_at", "payload")}
            expected_digest = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
            if envelope.get("payload_sha256") != expected_digest:
                raise StudyResultArchiveError("Study Result archive checksum mismatch.")
            project_id = payload["project_id"]
            if expected_project_id is not None and project_id != expected_project_id:
                raise StudyResultArchiveError("Study Result archive project identity mismatch.")
            revision_data = payload["source_revision"]
            revision = ProjectRevision(
                model_revision=revision_data["model_revision"],
                topology_revision=revision_data["topology_revision"],
                presentation_revision=revision_data["presentation_revision"],
                persisted_revision=revision_data["persisted_revision"],
            )
            metadata = _decode_value(payload.get("metadata", {}))
            if not isinstance(metadata, Mapping):
                raise StudyResultArchiveError("Restored Study Result metadata must be an object.")
            result = StudyResult(
                study_id=UUID(str(payload["study_id"])),
                project_id=str(project_id),
                activation_generation=int(payload["activation_generation"]),
                source_revision=revision,
                study_type=str(payload["study_type"]),
                status=str(payload["status"]),
                value=_decode_value(payload.get("value")),
                message=str(payload.get("message", "")),
                metadata=metadata,
            )
            return ArchivedStudyResult(
                record_id=UUID(str(envelope["record_id"])),
                saved_at=str(envelope["saved_at"]),
                result=result,
            )
        except StudyResultArchiveError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise StudyResultArchiveError(f"Malformed Study Result archive record {path.name}: {exc}") from exc

    def load_all(
        self,
        project_id: str,
        *,
        activation_generation: int | None = None,
        study_id: UUID | None = None,
    ) -> tuple[ArchivedStudyResult, ...]:
        project_dir = self._root / self._project_key(project_id)
        if not project_dir.exists():
            return ()
        if activation_generation is None:
            generation_dirs = tuple(item for item in project_dir.iterdir() if item.is_dir())
        else:
            if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
                raise ValueError("activation_generation must be a positive integer.")
            generation_dirs = (project_dir / str(activation_generation),)
        prefix = f"{study_id}." if study_id is not None else ""
        records: list[ArchivedStudyResult] = []
        for directory in generation_dirs:
            if not directory.exists():
                continue
            for path in directory.glob(f"{prefix}*.json"):
                record = self._read(path, expected_project_id=project_id)
                if activation_generation is not None and record.result.activation_generation != activation_generation:
                    raise StudyResultArchiveError("Study Result archive activation-generation path mismatch.")
                if study_id is not None and record.result.study_id != study_id:
                    raise StudyResultArchiveError("Study Result archive study identity path mismatch.")
                records.append(record)
        return tuple(sorted(records, key=lambda item: (item.saved_at, str(item.record_id))))

    def load_latest(
        self, project_id: str, activation_generation: int, study_id: UUID
    ) -> ArchivedStudyResult | None:
        records = self.load_all(
            project_id, activation_generation=activation_generation, study_id=study_id
        )
        return records[-1] if records else None


__all__ = [
    "ARCHIVE_FORMAT",
    "ARCHIVE_SCHEMA_VERSION",
    "ArchivedStudyResult",
    "StudyResultArchive",
    "StudyResultArchiveError",
]
