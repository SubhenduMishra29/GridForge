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
#     Represents a validated relationship between two logical
#     equipment terminals.
#
# Responsibilities:
#     - stable connection identity;
#     - source terminal identity;
#     - target terminal identity;
#     - connection metadata;
#     - connection enabled state;
#     - serialization/deserialization;
#     - endpoint relationship queries.
#
# Does NOT:
#     - draw the connection;
#     - own LineItem;
#     - perform graphical hit testing;
#     - perform routing;
#     - validate terminal existence;
#     - validate electrical topology;
#     - calculate electrical parameters;
#     - modify Core topology.
#
# Architectural Boundary:
#
#     TerminalResolver
#            │
#            ▼
#     ConnectionValidator
#            │
#            ▼
#       Connection
#            │
#            ├── ConnectionRouter
#            ├── ConnectionPreview
#            └── TopologyAdapter
#
# Core remains authoritative for electrical-network state.
#
# ============================================================

"""
GridForge V2 — Logical SLD Connection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class Connection:
    """
    Logical connection between two SLD terminals.

    Terminal identifiers are stable logical identifiers. They are
    never Qt graphics-object references.

    Connection deliberately contains no graphical state.
    """

    connection_id: str
    source_terminal_id: str
    target_terminal_id: str

    connection_type: str = "electrical"

    properties: dict[str, Any] = field(
        default_factory=dict
    )

    enabled: bool = True

    # ========================================================
    # INITIALIZATION / VALIDATION
    # ========================================================

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the intrinsic connection contract.

        Only invariants that can be established without access to
        the terminal registry or Core are checked here.
        """

        self.connection_id = self._validate_identifier(
            self.connection_id,
            "connection_id",
        )

        self.source_terminal_id = (
            self._validate_identifier(
                self.source_terminal_id,
                "source_terminal_id",
            )
        )

        self.target_terminal_id = (
            self._validate_identifier(
                self.target_terminal_id,
                "target_terminal_id",
            )
        )

        self.connection_type = (
            self._validate_identifier(
                self.connection_type,
                "connection_type",
            )
        )

        if (
            self.source_terminal_id
            == self.target_terminal_id
        ):
            raise ValueError(
                "A terminal cannot connect to itself."
            )

        if not isinstance(
            self.properties,
            Mapping,
        ):
            raise TypeError(
                "properties must be a mapping."
            )

        normalized_properties: dict[
            str,
            Any,
        ] = {}

        for key, value in self.properties.items():

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    "property keys must be strings."
                )

            if not key.strip():
                raise ValueError(
                    "property keys must not be empty."
                )

            normalized_properties[key] = value

        self.properties = normalized_properties

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be a bool."
            )

    # ========================================================
    # ENDPOINT QUERIES
    # ========================================================

    def connects_terminal(
        self,
        terminal_id: str,
    ) -> bool:
        """
        Return True when this connection touches the supplied
        terminal.
        """

        if not isinstance(
            terminal_id,
            str,
        ):
            return False

        return terminal_id in {
            self.source_terminal_id,
            self.target_terminal_id,
        }

    # --------------------------------------------------------

    def other_terminal(
        self,
        terminal_id: str,
    ) -> str:
        """
        Return the opposite endpoint of this connection.

        Raises
        ------
        KeyError
            If the supplied terminal does not belong to this
            connection.
        """

        if (
            terminal_id
            == self.source_terminal_id
        ):
            return self.target_terminal_id

        if (
            terminal_id
            == self.target_terminal_id
        ):
            return self.source_terminal_id

        raise KeyError(
            terminal_id
        )

    # --------------------------------------------------------

    def endpoint_ids(
        self,
    ) -> tuple[str, str]:
        """
        Return the connection endpoints in source/target order.
        """

        return (
            self.source_terminal_id,
            self.target_terminal_id,
        )

    # --------------------------------------------------------

    def unordered_endpoint_ids(
        self,
    ) -> frozenset[str]:
        """
        Return endpoint IDs as an unordered pair.

        Useful for duplicate detection where connection direction
        is not semantically significant.
        """

        return frozenset(
            {
                self.source_terminal_id,
                self.target_terminal_id,
            }
        )

    # --------------------------------------------------------

    def connects_pair(
        self,
        terminal_a: str,
        terminal_b: str,
    ) -> bool:
        """
        Return True when this connection joins the supplied pair
        of terminals, regardless of direction.
        """

        if not isinstance(
            terminal_a,
            str,
        ):
            return False

        if not isinstance(
            terminal_b,
            str,
        ):
            return False

        if terminal_a == terminal_b:
            return False

        return (
            self.unordered_endpoint_ids()
            == frozenset(
                {
                    terminal_a,
                    terminal_b,
                }
            )
        )

    # ========================================================
    # STATE
    # ========================================================

    def is_enabled(
        self,
    ) -> bool:
        """Return whether the connection is enabled."""

        return self.enabled

    # --------------------------------------------------------

    def set_enabled(
        self,
        enabled: bool,
    ) -> None:
        """Enable or disable the logical connection."""

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be a bool."
            )

        self.enabled = enabled

    # ========================================================
    # PROPERTIES
    # ========================================================

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return one connection property."""

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "key must be a string."
            )

        return self.properties.get(
            key,
            default,
        )

    # --------------------------------------------------------

    def set_property(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set one connection property."""

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "key must be a string."
            )

        if not key.strip():
            raise ValueError(
                "key must not be empty."
            )

        self.properties[key] = value

    # --------------------------------------------------------

    def remove_property(
        self,
        key: str,
    ) -> Any:
        """Remove and return one connection property."""

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "key must be a string."
            )

        if not key.strip():
            raise ValueError(
                "key must not be empty."
            )

        return self.properties.pop(
            key
        )

    # --------------------------------------------------------

    def has_property(
        self,
        key: str,
    ) -> bool:
        """Return whether a property exists."""

        if not isinstance(
            key,
            str,
        ):
            return False

        return key in self.properties

    # --------------------------------------------------------

    def clear_properties(
        self,
    ) -> None:
        """Remove all connection metadata."""

        self.properties.clear()

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the logical connection.

        A new properties dictionary is returned so callers cannot
        mutate the Connection through the serialized result.
        """

        return {
            "connection_id": self.connection_id,
            "source_terminal_id": self.source_terminal_id,
            "target_terminal_id": self.target_terminal_id,
            "connection_type": self.connection_type,
            "properties": dict(
                self.properties
            ),
            "enabled": self.enabled,
        }

    # --------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "Connection":
        """
        Reconstruct a Connection from serialized data.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "data must be a mapping."
            )

        required_fields = (
            "connection_id",
            "source_terminal_id",
            "target_terminal_id",
        )

        for field_name in required_fields:

            if field_name not in data:
                raise KeyError(
                    field_name
                )

        properties = data.get(
            "properties",
            {},
        )

        if properties is None:
            properties = {}

        if not isinstance(
            properties,
            Mapping,
        ):
            raise TypeError(
                "properties must be a mapping."
            )

        enabled = data.get(
            "enabled",
            True,
        )

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be a bool."
            )

        return cls(
            connection_id=cls._deserialize_identifier(
                data["connection_id"],
                "connection_id",
            ),
            source_terminal_id=cls._deserialize_identifier(
                data["source_terminal_id"],
                "source_terminal_id",
            ),
            target_terminal_id=cls._deserialize_identifier(
                data["target_terminal_id"],
                "target_terminal_id",
            ),
            connection_type=cls._deserialize_identifier(
                data.get(
                    "connection_type",
                    "electrical",
                ),
                "connection_type",
            ),
            properties=dict(
                properties
            ),
            enabled=enabled,
        )

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _validate_identifier(
        value: str,
        name: str,
    ) -> str:
        """
        Validate an intrinsic string identifier.

        Identifiers are not silently stripped because identifiers
        must remain stable and deterministic.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"{name} must not be empty."
            )

        return value

    # --------------------------------------------------------

    @staticmethod
    def _deserialize_identifier(
        value: Any,
        name: str,
    ) -> str:
        """
        Validate an identifier supplied by serialized data.

        Arbitrary objects are not silently converted with str().
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be a string."
            )

        return Connection._validate_identifier(
            value,
            name,
        )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """Return a concise diagnostic representation."""

        return (
            "Connection("
            f"id={self.connection_id!r}, "
            f"source={self.source_terminal_id!r}, "
            f"target={self.target_terminal_id!r}, "
            f"type={self.connection_type!r}, "
            f"enabled={self.enabled}"
            ")"
        )


__all__ = [
    "Connection",
]
