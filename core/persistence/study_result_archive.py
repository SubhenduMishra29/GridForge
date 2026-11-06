"""Versioned durable archive for detached Application StudyResult values.

Study outputs are execution artifacts, not project configuration. This archive
stores them beside the user's GridForge application data, keyed by project and
activation provenance, without modifying the canonical .gridforge package.

Schema v1 remains readable with its historical generic-dataclass mapping
semantics. Schema v2 adds allowlisted transient result/event reconstruction;
schema v3 adds typed detached event-transition reconstruction.
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
from core.solver.power_flow.result import PowerFlowResult
from core.solver.dynamics.events import EventExecution, EventTransition
from core.solver.dynamics.dae_solver import AlgebraicNetworkSolution
from core.solver.dynamics.transient_stability import TransientDiscontinuity, TransientStabilityResult
from core.solver.short_circuit.fault_types import FaultType
from core.solver.short_circuit.result import (
    ContributionStatus,
    ShortCircuitBranchCurrent,
    ShortCircuitConductorCurrent,
    ShortCircuitEquipmentCurrent,
    ShortCircuitResult,
    ShortCircuitSourceContribution,
    ShortCircuitStatus,
    ShortCircuitTerminalCurrent,
    ShortCircuitTransformerDeltaLoopCurrent,
)


ARCHIVE_FORMAT = "GridForgeStudyResult"
ARCHIVE_SCHEMA_VERSION = 4


class StudyResultArchiveError(RuntimeError):
    """Raised when a Study Result archive cannot be written or restored."""


class StudyResultArchiveCommitUncertain(StudyResultArchiveError):
    """The record was atomically published, but directory durability is uncertain."""

    record_committed = True
    durability_confirmed = False

    def __init__(self, record_id: UUID, saved_at: str, cause: OSError) -> None:
        self.record_id = record_id
        self.saved_at = saved_at
        super().__init__(
            f"Study Result {record_id} is visible in the archive, but directory "
            f"durability could not be confirmed: {cause}"
        )


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

@dataclass(frozen=True, slots=True)
class StudyResultArchiveVerification:
    """Read-only integrity report; corrupt records are reported, never repaired."""

    project_id: str
    scanned_count: int
    valid_record_ids: tuple[UUID, ...]
    invalid_records: tuple[tuple[str, str], ...]

    @property
    def is_valid(self) -> bool:
        return not self.invalid_records


def _qualified_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


_SOLVER_RESULT_TYPES = {
    f"{cls.__module__}.{cls.__qualname__}": cls
    for cls in (
        PowerFlowResult,
        TransientStabilityResult,
        ShortCircuitResult,
        ShortCircuitSourceContribution,
        ShortCircuitBranchCurrent,
        ShortCircuitEquipmentCurrent,
        ShortCircuitTerminalCurrent,
        ShortCircuitConductorCurrent,
        ShortCircuitTransformerDeltaLoopCurrent,
    )
}
_SOLVER_EVENT_TYPES = {
    f"{EventExecution.__module__}.{EventExecution.__qualname__}": EventExecution,
}
_SOLVER_DISCONTINUITY_TYPES = {
    f"{TransientDiscontinuity.__module__}.{TransientDiscontinuity.__qualname__}": TransientDiscontinuity,
}
_SOLVER_TRANSITION_TYPES = {
    f"{EventTransition.__module__}.{EventTransition.__qualname__}": EventTransition,
}
_SOLVER_ALGEBRAIC_TYPES = {
    f"{AlgebraicNetworkSolution.__module__}.{AlgebraicNetworkSolution.__qualname__}": AlgebraicNetworkSolution,
}
_SOLVER_ENUM_TYPES = {
    f"{cls.__module__}.{cls.__qualname__}": cls
    for cls in (FaultType, ContributionStatus, ShortCircuitStatus)
}


def _encode_value(value: Any) -> Any:
    """Encode supported result values explicitly; reject unknown runtime objects."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        special = "nan" if math.isnan(value) else (
            "positive_infinity" if value > 0 else "negative_infinity"
        )
        return {"$type": "float", "value": special}
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
        if value.dtype.kind not in "biufc" or value.dtype.hasobject:
            raise StudyResultArchiveError(
                f"Study Result contains an unsupported NumPy array dtype: {value.dtype}."
            )
        return {
            "$type": "ndarray",
            "dtype": value.dtype.str,
            "shape": list(value.shape),
            "data": _encode_value(value.tolist()),
        }
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
        qualified = _qualified_name(value)
        if qualified in _SOLVER_RESULT_TYPES:
            tag = "solver_result"
        elif qualified in _SOLVER_EVENT_TYPES:
            tag = "event_execution"
        elif qualified in _SOLVER_TRANSITION_TYPES:
            tag = "event_transition"
        elif qualified in _SOLVER_DISCONTINUITY_TYPES:
            tag = "transient_discontinuity"
        elif qualified in _SOLVER_ALGEBRAIC_TYPES:
            tag = "algebraic_network_solution"
        else:
            tag = "dataclass"
        return {
            "$type": tag,
            "class": qualified,
            "fields": {item.name: _encode_value(getattr(value, item.name)) for item in fields(value)},
        }
    raise StudyResultArchiveError(
        f"Study Result contains unsupported runtime value: {type(value).__name__}."
    )


def _decode_value(value: Any, *, schema_version: int = 1) -> Any:
    if isinstance(value, list):
        return tuple(_decode_value(item, schema_version=schema_version) for item in value)
    if not isinstance(value, Mapping):
        return value
    kind = value.get("$type")
    qualified_hint = value.get("class")
    transient_result_name = f"{TransientStabilityResult.__module__}.{TransientStabilityResult.__qualname__}"
    event_execution_name = f"{EventExecution.__module__}.{EventExecution.__qualname__}"
    algebraic_solution_name = f"{AlgebraicNetworkSolution.__module__}.{AlgebraicNetworkSolution.__qualname__}"
    event_transition_name = f"{EventTransition.__module__}.{EventTransition.__qualname__}"
    if schema_version >= 2 and qualified_hint in {transient_result_name, event_execution_name, algebraic_solution_name}:
        expected_kind = (
            "solver_result" if qualified_hint == transient_result_name else
            "event_execution" if qualified_hint == event_execution_name else
            "algebraic_network_solution"
        )
        if kind != expected_kind:
            raise StudyResultArchiveError(
                f"Known transient type {qualified_hint} must use the {expected_kind!r} archive tag in schema v2."
            )
    if qualified_hint == event_transition_name and (
        schema_version < 3 or kind != "event_transition"
    ):
        raise StudyResultArchiveError("Known EventTransition must use the 'event_transition' archive tag in schema v3.")
    if kind == "event_transition" and schema_version < 3:
        raise StudyResultArchiveError("EventTransition tags require Study Result archive schema v3.")
    if kind == "transient_discontinuity" and schema_version < 4:
        raise StudyResultArchiveError("TransientDiscontinuity tags require Study Result archive schema v4.")
    if kind in {"solver_result", "event_execution", "algebraic_network_solution", "event_transition", "transient_discontinuity"} and set(value) != {"$type", "class", "fields"}:
        raise StudyResultArchiveError(f"Persisted {kind} archive value has missing or unknown fields.")
    if kind == "ndarray":
        if schema_version < 2:
            raise StudyResultArchiveError("NumPy ndarray tags require Study Result archive schema v2.")
        if set(value) != {"$type", "dtype", "shape", "data"}:
            raise StudyResultArchiveError("Persisted NumPy ndarray tag contains missing or unknown fields.")
        try:
            dtype = np.dtype(value["dtype"])
            shape_data = value["shape"]
            if dtype.kind not in "biufc" or dtype.hasobject:
                raise ValueError("unsupported numeric dtype")
            if not isinstance(shape_data, list) or any(
                isinstance(item, bool) or not isinstance(item, int) or item < 0
                for item in shape_data
            ):
                raise ValueError("invalid array shape")
            decoded_data = _decode_value(value["data"], schema_version=schema_version)
            array = np.asarray(decoded_data, dtype=dtype)
            array = array.reshape(tuple(shape_data))
            return array
        except (TypeError, ValueError, OverflowError) as exc:
            raise StudyResultArchiveError(f"Persisted NumPy ndarray payload is invalid: {exc}") from exc
    if kind == "float" and set(value) == {"$type", "value"}:
        special = value["value"]
        if special == "nan":
            return float("nan")
        if special == "positive_infinity":
            return float("inf")
        if special == "negative_infinity":
            return float("-inf")
        raise StudyResultArchiveError("Persisted non-finite float tag is invalid.")
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
        qualified = value["class"]
        decoded = _decode_value(value["value"], schema_version=schema_version)
        enum_type = _SOLVER_ENUM_TYPES.get(qualified)
        if enum_type is not None:
            try:
                return enum_type(decoded)
            except (TypeError, ValueError) as exc:
                raise StudyResultArchiveError("Persisted solver enum value is invalid.") from exc
        # Unknown enums remain detached scalar values; never import archive names.
        return decoded
    if kind in {"solver_result", "event_execution", "algebraic_network_solution", "event_transition", "transient_discontinuity", "dataclass"} and set(value) == {"$type", "class", "fields"}:
        payload = value["fields"]
        if not isinstance(payload, Mapping):
            raise StudyResultArchiveError("Persisted dataclass fields must be an object.")
        decoded_fields = {key: _decode_value(item, schema_version=schema_version) for key, item in payload.items()}
        qualified = value["class"]

        if kind == "algebraic_network_solution":
            if schema_version < 2:
                raise StudyResultArchiveError("AlgebraicNetworkSolution tags require Study Result archive schema v2.")
            solution_type = _SOLVER_ALGEBRAIC_TYPES.get(qualified)
            if solution_type is None:
                raise StudyResultArchiveError("Persisted algebraic network solution type is not allowlisted.")
            allowed_fields = {item.name for item in fields(solution_type)}
            if set(decoded_fields) != allowed_fields:
                raise StudyResultArchiveError(
                    "Persisted AlgebraicNetworkSolution fields do not match its canonical contract."
                )
            try:
                return solution_type(**decoded_fields)
            except (TypeError, ValueError) as exc:
                raise StudyResultArchiveError(
                    f"Persisted AlgebraicNetworkSolution violates its result contract: {exc}"
                ) from exc

        if kind == "transient_discontinuity":
            if schema_version < 4:
                raise StudyResultArchiveError("TransientDiscontinuity tags require Study Result archive schema v4.")
            discontinuity_type = _SOLVER_DISCONTINUITY_TYPES.get(qualified)
            if discontinuity_type is None:
                raise StudyResultArchiveError("Persisted transient discontinuity type is not allowlisted.")
            allowed_fields = {item.name for item in fields(discontinuity_type)}
            if set(decoded_fields) != allowed_fields:
                raise StudyResultArchiveError("Persisted TransientDiscontinuity fields do not match its canonical contract.")
            try:
                return discontinuity_type(**decoded_fields)
            except (TypeError, ValueError) as exc:
                raise StudyResultArchiveError(f"Persisted TransientDiscontinuity violates its result contract: {exc}") from exc

        if kind == "event_transition":
            if schema_version < 3:
                raise StudyResultArchiveError("EventTransition tags require Study Result archive schema v3.")
            transition_type = _SOLVER_TRANSITION_TYPES.get(qualified)
            if transition_type is None:
                raise StudyResultArchiveError("Persisted event transition type is not allowlisted.")
            allowed_fields = {item.name for item in fields(transition_type)}
            if set(decoded_fields) != allowed_fields:
                raise StudyResultArchiveError("Persisted EventTransition fields do not match its canonical contract.")
            try:
                return transition_type(**decoded_fields)
            except (TypeError, ValueError) as exc:
                raise StudyResultArchiveError(f"Persisted EventTransition violates its result contract: {exc}") from exc

        if kind == "event_execution":
            if schema_version < 2:
                raise StudyResultArchiveError("EventExecution tags require Study Result archive schema v2.")
            execution_type = _SOLVER_EVENT_TYPES.get(qualified)
            if execution_type is None:
                raise StudyResultArchiveError("Persisted event execution type is not allowlisted.")
            allowed_fields = {item.name for item in fields(execution_type)}
            if schema_version < 3 and "transition" in allowed_fields:
                legacy_fields = allowed_fields - {"transition"}
                if set(decoded_fields) == legacy_fields:
                    decoded_fields["transition"] = None
                elif set(decoded_fields) != allowed_fields:
                    raise StudyResultArchiveError(
                        "Persisted EventExecution fields do not match the schema-v2 canonical contract."
                    )
            elif set(decoded_fields) != allowed_fields:
                raise StudyResultArchiveError(
                    "Persisted EventExecution fields do not match its versioned canonical contract."
                )
            try:
                return execution_type(**decoded_fields)
            except (TypeError, ValueError) as exc:
                raise StudyResultArchiveError(
                    f"Persisted EventExecution violates its result contract: {exc}"
                ) from exc

        if kind == "solver_result":
            result_type = _SOLVER_RESULT_TYPES.get(qualified)
            if result_type is None:
                raise StudyResultArchiveError("Persisted solver result type is not allowlisted.")
            allowed_fields = {item.name for item in fields(result_type)}
            if result_type is TransientStabilityResult and schema_version < 4:
                legacy_fields = allowed_fields - {"discontinuities"}
                if set(decoded_fields) == legacy_fields:
                    decoded_fields["discontinuities"] = ()
            if set(decoded_fields) != allowed_fields:
                raise StudyResultArchiveError(
                    f"Persisted {result_type.__name__} fields do not match its versioned canonical contract."
                )
            if result_type is TransientStabilityResult:
                algebraic_quality = decoded_fields.get("algebraic_quality")
                if not isinstance(algebraic_quality, (tuple, list)) or any(
                    not isinstance(item, AlgebraicNetworkSolution) for item in algebraic_quality
                ):
                    raise StudyResultArchiveError(
                        "Persisted TransientStabilityResult algebraic_quality must contain only "
                        "allowlisted AlgebraicNetworkSolution records."
                    )
                events = decoded_fields.get("events")
                if not isinstance(events, (tuple, list)) or any(
                    not isinstance(item, EventExecution) for item in events
                ):
                    raise StudyResultArchiveError(
                        "Persisted TransientStabilityResult events must be allowlisted EventExecution records."
                    )
                discontinuities = decoded_fields.get("discontinuities", ())
                if not isinstance(discontinuities, (tuple, list)) or any(
                    not isinstance(item, TransientDiscontinuity) for item in discontinuities
                ):
                    raise StudyResultArchiveError(
                        "Persisted TransientStabilityResult discontinuities must be allowlisted TransientDiscontinuity records."
                    )
            try:
                return result_type(**decoded_fields)
            except (TypeError, ValueError) as exc:
                raise StudyResultArchiveError(
                    f"Persisted {result_type.__name__} violates its result contract: {exc}"
                ) from exc

        if schema_version >= 2 and qualified in {
            f"{TransientStabilityResult.__module__}.{TransientStabilityResult.__qualname__}",
            f"{EventExecution.__module__}.{EventExecution.__qualname__}",
            f"{AlgebraicNetworkSolution.__module__}.{AlgebraicNetworkSolution.__qualname__}",
        }:
            raise StudyResultArchiveError(
                f"Known transient type {qualified} cannot use the generic dataclass archive tag in schema v2."
            )
        if schema_version >= 3 and qualified == event_transition_name:
            raise StudyResultArchiveError(
                "Known EventTransition cannot use the generic dataclass archive tag in schema v3."
            )
        discontinuity_name = f"{TransientDiscontinuity.__module__}.{TransientDiscontinuity.__qualname__}"
        if schema_version >= 4 and qualified == discontinuity_name:
            raise StudyResultArchiveError("Known TransientDiscontinuity cannot use the generic dataclass archive tag in schema v4.")
        return {"$dataclass": qualified, "fields": decoded_fields}
    return {key: _decode_value(item, schema_version=schema_version) for key, item in value.items()}


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
        envelope = {**envelope_without_digest, "record_sha256": digest}
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
                    if os.name != "nt":
                        try:
                            directory_fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                            try:
                                os.fsync(directory_fd)
                            finally:
                                os.close(directory_fd)
                        except OSError as durability_exc:
                            raise StudyResultArchiveCommitUncertain(
                                record_id, saved_at, durability_exc
                            ) from durability_exc
                except Exception:
                    try:
                        os.unlink(temporary_name)
                    except FileNotFoundError:
                        pass
                    raise
            except StudyResultArchiveCommitUncertain:
                raise
            except Exception as exc:
                raise StudyResultArchiveError(f"Unable to archive Study Result: {exc}") from exc
        return ArchivedStudyResult(record_id=record_id, saved_at=saved_at, result=result)

    def _read(self, path: Path, *, expected_project_id: str | None = None) -> ArchivedStudyResult:
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(envelope, Mapping):
                raise StudyResultArchiveError("Study Result archive record must be an object.")
            if set(envelope) != {"format", "schema_version", "record_id", "saved_at", "payload", "record_sha256"}:
                raise StudyResultArchiveError("Study Result archive envelope contains missing or unknown fields.")
            if envelope.get("format") != ARCHIVE_FORMAT:
                raise StudyResultArchiveError("Unsupported Study Result archive format.")
            schema_version = envelope.get("schema_version")
            if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version not in {1, 2, 3, 4}:
                raise StudyResultArchiveError(
                    f"Unsupported Study Result archive schema: {schema_version!r}."
                )
            payload = envelope.get("payload")
            if not isinstance(payload, Mapping):
                raise StudyResultArchiveError("Study Result archive payload must be an object.")
            if set(payload) != {"study_id", "project_id", "activation_generation", "source_revision", "study_type", "status", "value", "message", "metadata"}:
                raise StudyResultArchiveError("Study Result archive payload contains missing or unknown fields.")
            unsigned = {key: envelope[key] for key in ("format", "schema_version", "record_id", "saved_at", "payload")}
            expected_digest = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
            if envelope.get("record_sha256") != expected_digest:
                raise StudyResultArchiveError("Study Result archive checksum mismatch.")
            project_id = payload["project_id"]
            if not isinstance(project_id, str) or not project_id.strip():
                raise StudyResultArchiveError("Persisted Study Result project identity is invalid.")
            if expected_project_id is not None and project_id != expected_project_id:
                raise StudyResultArchiveError("Study Result archive project identity mismatch.")
            generation = payload["activation_generation"]
            if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
                raise StudyResultArchiveError("Persisted Study Result activation generation is invalid.")
            revision_data = payload["source_revision"]
            revision = ProjectRevision(
                model_revision=revision_data["model_revision"],
                topology_revision=revision_data["topology_revision"],
                presentation_revision=revision_data["presentation_revision"],
                persisted_revision=revision_data["persisted_revision"],
            )
            metadata = _decode_value(payload.get("metadata", {}), schema_version=schema_version)
            if not isinstance(metadata, Mapping):
                raise StudyResultArchiveError("Restored Study Result metadata must be an object.")
            result = StudyResult(
                study_id=UUID(str(payload["study_id"])),
                project_id=str(project_id),
                activation_generation=generation,
                source_revision=revision,
                study_type=str(payload["study_type"]),
                status=str(payload["status"]),
                value=_decode_value(payload.get("value"), schema_version=schema_version),
                message=str(payload.get("message", "")),
                metadata=metadata,
            )
            record_id = UUID(str(envelope["record_id"]))
            if path.name != f"{result.study_id}.{record_id}.json":
                raise StudyResultArchiveError("Study Result archive filename does not match its record identity.")
            if path.parent.name != str(result.activation_generation):
                raise StudyResultArchiveError("Study Result archive directory does not match activation provenance.")
            return ArchivedStudyResult(
                record_id=record_id,
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
        project_id = project_id.strip() if isinstance(project_id, str) else project_id
        project_dir = self._root / self._project_key(project_id)
        if activation_generation is not None and (
            isinstance(activation_generation, bool)
            or not isinstance(activation_generation, int)
            or activation_generation < 1
        ):
            raise ValueError("activation_generation must be a positive integer.")
        if study_id is not None and not isinstance(study_id, UUID):
            raise TypeError("study_id must be a UUID or None.")
        if not project_dir.exists():
            return ()
        if activation_generation is None:
            generation_dirs = tuple(item for item in project_dir.iterdir() if item.is_dir())
        else:
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

    def verify(
        self, project_id: str, *, activation_generation: int | None = None
    ) -> StudyResultArchiveVerification:
        """Inspect every record in scope and report corruption without mutating it."""
        project_dir = self._root / self._project_key(project_id)
        if activation_generation is not None and (
            isinstance(activation_generation, bool)
            or not isinstance(activation_generation, int)
            or activation_generation < 1
        ):
            raise ValueError("activation_generation must be a positive integer.")
        if not project_dir.exists():
            return StudyResultArchiveVerification(project_id, 0, (), ())
        directories = (
            (project_dir / str(activation_generation),)
            if activation_generation is not None
            else tuple(item for item in project_dir.iterdir() if item.is_dir())
        )
        valid: list[UUID] = []
        invalid: list[tuple[str, str]] = []
        scanned = 0
        for directory in directories:
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.json")):
                scanned += 1
                try:
                    record = self._read(path, expected_project_id=project_id)
                    if activation_generation is not None and record.result.activation_generation != activation_generation:
                        raise StudyResultArchiveError("Study Result archive activation-generation path mismatch.")
                    valid.append(record.record_id)
                except StudyResultArchiveError as exc:
                    invalid.append((path.name, str(exc)))
        return StudyResultArchiveVerification(
            project_id=project_id,
            scanned_count=scanned,
            valid_record_ids=tuple(valid),
            invalid_records=tuple(invalid),
        )


__all__ = [
    "ARCHIVE_FORMAT",
    "ARCHIVE_SCHEMA_VERSION",
    "ArchivedStudyResult",
    "StudyResultArchiveVerification",
    "StudyResultArchive",
    "StudyResultArchiveError",
    "StudyResultArchiveCommitUncertain",
]
