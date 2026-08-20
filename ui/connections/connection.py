
## `ui/connections/connection.py`

```python
# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/connection.py
#
# Purpose:
#     Logical representation of an SLD connection.
#
# Architectural Role:
#     Represents a validated relationship between two equipment
#     terminals.
#
# Responsibilities:
#     - stable connection identity;
#     - source terminal identity;
#     - target terminal identity;
#     - connection metadata;
#     - connection state;
#     - serialization.
#
# Does NOT:
#     - draw the connection;
#     - calculate electrical impedance;
#     - own LineItem;
#     - modify Core topology.
#
# ============================================================

"""
GridForge V2 — Logical SLD Connection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Connection:
    """
    Logical connection between two SLD terminals.

    Terminal identifiers are stable logical identifiers and are not
    references to Qt graphics objects.
    """

    connection_id: str
    source_terminal_id: str
    target_terminal_id: str

    connection_type: str = "electrical"

    properties: Dict[str, Any] = field(
        default_factory=dict
    )

    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.connection_id:
            raise ValueError(
                "connection_id must not be empty"
            )

        if not self.source_terminal_id:
            raise ValueError(
                "source_terminal_id must not be empty"
            )

        if not self.target_terminal_id:
            raise ValueError(
                "target_terminal_id must not be empty"
            )

        if (
            self.source_terminal_id
            == self.target_terminal_id
        ):
            raise ValueError(
                "A terminal cannot connect to itself"
            )

        if not self.connection_type:
            raise ValueError(
                "connection_type must not be empty"
            )

    def connects_terminal(
        self,
        terminal_id: str,
    ) -> bool:
        return terminal_id in {
            self.source_terminal_id,
            self.target_terminal_id,
        }

    def other_terminal(
        self,
        terminal_id: str,
    ) -> str:
        if terminal_id == self.source_terminal_id:
            return self.target_terminal_id

        if terminal_id == self.target_terminal_id:
            return self.source_terminal_id

        raise KeyError(terminal_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "source_terminal_id": self.source_terminal_id,
            "target_terminal_id": self.target_terminal_id,
            "connection_type": self.connection_type,
            "properties": dict(self.properties),
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "Connection":
        return cls(
            connection_id=str(
                data["connection_id"]
            ),
            source_terminal_id=str(
                data["source_terminal_id"]
            ),
            target_terminal_id=str(
                data["target_terminal_id"]
            ),
            connection_type=str(
                data.get(
                    "connection_type",
                    "electrical",
                )
            ),
            properties=dict(
                data.get(
                    "properties",
                    {},
                )
            ),
            enabled=bool(
                data.get(
                    "enabled",
                    True,
                )
            ),
        )
