
---

# `ui/workspace/document.py`

```python
# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/workspace/document.py
#
# Purpose:
#     Generic application-level document descriptor.
#
# Architectural Role:
#     Provides a common document lifecycle abstraction for the
#     workspace without forcing the workspace to depend directly
#     on the SLD implementation.
#
# Responsibilities:
#     - document identity;
#     - document type;
#     - document name;
#     - modified state;
#     - document metadata.
#
# Does NOT:
#     - own QGraphicsScene;
#     - render content;
#     - perform electrical calculations.
#
# ============================================================

"""
GridForge V2 — Workspace Document.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Document:
    """
    Generic UI application document descriptor.

    Specialized documents such as SLDDocument may contain their own
    domain model while still being represented by the workspace layer.
    """

    def __init__(
        self,
        document_id: str,
        document_type: str,
        name: str = "Untitled",
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not document_id:
            raise ValueError(
                "document_id must not be empty"
            )

        if not document_type:
            raise ValueError(
                "document_type must not be empty"
            )

        if not name:
            raise ValueError(
                "name must not be empty"
            )

        self._document_id = str(document_id)
        self._document_type = str(document_type)
        self._name = str(name)
        self._metadata = dict(metadata or {})
        self._modified = False

    @property
    def document_id(self) -> str:
        return self._document_id

    @property
    def document_type(self) -> str:
        return self._document_type

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value:
            raise ValueError(
                "name must not be empty"
            )

        if value != self._name:
            self._name = str(value)
            self.mark_modified()

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def modified(self) -> bool:
        return self._modified

    def mark_modified(self) -> None:
        self._modified = True

    def mark_clean(self) -> None:
        self._modified = False

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._metadata.get(
            key,
            default,
        )

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        if not key:
            raise ValueError(
                "metadata key must not be empty"
            )

        self._metadata[key] = value
        self.mark_modified()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "name": self.name,
            "metadata": dict(self.metadata),
            "modified": self.modified,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "Document":
        document = cls(
            document_id=str(
                data["document_id"]
            ),
            document_type=str(
                data["document_type"]
            ),
            name=str(
                data.get(
                    "name",
                    "Untitled",
                )
            ),
            metadata=dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
        )

        if data.get("modified", False):
            document.mark_modified()

        return document
