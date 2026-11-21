# ============================================================
# File: core/application/configuration_review.py
# GridForge V2 — Application Configuration Review Records
# ============================================================

"""Immutable Application-owned records for pending engineering configuration review."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ConfigurationReviewRecord:
    """One committed equipment element's canonical field-review obligations."""

    record_id: str
    project_id: str
    element_id: str
    element_type: str
    field_dispositions: Mapping[str, Mapping[str, Any]]
    status: str = "pending"
    completion_command_id: str | None = None
    completion_command_type: str | None = None

    def __post_init__(self) -> None:
        for name in ("record_id", "project_id", "element_id", "element_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"ConfigurationReviewRecord.{name} must be non-empty.")
            object.__setattr__(self, name, value.strip())
        if self.status not in {"pending", "resolved", "not_applicable"}:
            raise ValueError("ConfigurationReviewRecord.status is unsupported.")
        if not isinstance(self.field_dispositions, Mapping) or not self.field_dispositions:
            raise ValueError("ConfigurationReviewRecord.field_dispositions must be a non-empty mapping.")
        frozen = {}
        for field_name, disposition in self.field_dispositions.items():
            if not isinstance(field_name, str) or not field_name.strip():
                raise ValueError("Configuration review field names must be non-empty strings.")
            if not isinstance(disposition, Mapping):
                raise TypeError("Each configuration field disposition must be a mapping.")
            kind = disposition.get("kind")
            if not isinstance(kind, str) or not kind.strip():
                raise ValueError(f"Configuration disposition for {field_name!r} requires a kind.")
            frozen[field_name.strip()] = MappingProxyType(dict(disposition))
        object.__setattr__(self, "field_dispositions", MappingProxyType(frozen))
        command_id = self.completion_command_id
        command_type = self.completion_command_type
        if (command_id is None) != (command_type is None):
            raise ValueError("Configuration review completion command identity must be all-or-none.")
        if command_id is not None:
            if not isinstance(command_id, str) or not command_id.strip():
                raise ValueError("completion_command_id must be non-empty when supplied.")
            if not isinstance(command_type, str) or not command_type.strip():
                raise ValueError("completion_command_type must be non-empty when supplied.")
            object.__setattr__(self, "completion_command_id", command_id.strip())
            object.__setattr__(self, "completion_command_type", command_type.strip())
        if self.status == "pending" and command_id is not None:
            raise ValueError("Pending configuration review cannot carry completion command provenance.")
        if self.status == "resolved" and command_id is None:
            raise ValueError("Resolved configuration review requires completion command provenance.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "project_id": self.project_id,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "field_dispositions": {
                field_name: dict(disposition)
                for field_name, disposition in self.field_dispositions.items()
            },
            "status": self.status,
            "completion_command_id": self.completion_command_id,
            "completion_command_type": self.completion_command_type,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConfigurationReviewRecord":
        if not isinstance(data, Mapping):
            raise TypeError("Configuration review record must be an object.")
        return cls(
            record_id=data.get("record_id"),
            project_id=data.get("project_id"),
            element_id=data.get("element_id"),
            element_type=data.get("element_type"),
            field_dispositions=data.get("field_dispositions"),
            status=data.get("status", "pending"),
            completion_command_id=data.get("completion_command_id"),
            completion_command_type=data.get("completion_command_type"),
        )


__all__ = ["ConfigurationReviewRecord"]
