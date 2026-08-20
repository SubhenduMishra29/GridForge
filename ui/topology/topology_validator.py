# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/topology/topology_validator.py
#
# Purpose:
#     Validates proposed SLD connections against the UI-side
#     topology rules before they are committed to the SLD model.
#
# Architectural Role:
#     TopologyValidator is the boundary between:
#
#         SLD editing operations
#                 |
#                 v
#         topology validation
#                 |
#                 v
#         SLDModel
#
#     It prevents the Canvas, tools, or Qt graphics layer from
#     becoming responsible for electrical-topology decisions.
#
# Detailed Working:
#
#     User / Tool
#          |
#          v
#     Connection request
#          |
#          v
#     TopologyValidator
#          |
#       +--+-------------------+
#       |                      |
#       v                      v
#   EquipmentManager     ConnectionManager
#       |                      |
#       +----------+-----------+
#                  |
#                  v
#             ValidationResult
#                  |
#          +-------+-------+
#          |               |
#       valid           invalid
#          |               |
#          v               v
#      SLDModel        rejected
#
# Responsibilities:
#     - verify endpoint equipment exists;
#     - verify endpoint terminals exist;
#     - reject self-connections where prohibited;
#     - detect duplicate endpoint connections where required;
#     - provide structured validation results;
#     - remain independent of Qt and rendering.
#
# Does NOT:
#     - create QGraphicsItem objects;
#     - render connections;
#     - route graphical lines;
#     - modify the SLD model;
#     - modify Core network objects;
#     - calculate electrical quantities;
#     - decide voltage compatibility;
#     - perform power-flow calculations.
#
# Important Boundary:
#
#     TopologyValidator validates UI/document topology rules.
#
#     It is NOT the electrical solver and NOT the Core network
#     topology engine.
#
# Future Expansion:
#
#     Additional topology policies can later validate:
#
#         - terminal directionality;
#         - terminal cardinality;
#         - bus connectivity;
#         - equipment compatibility;
#         - voltage-domain compatibility;
#         - prohibited connection classes.
#
#     Those rules should be introduced deliberately rather than
#     embedded into the Canvas or graphics items.
#
# ============================================================

"""
GridForge V2 — SLD Topology Validator.

Qt-independent validation of logical SLD connection requests.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ui.equipment.connection import EquipmentConnection
from ui.equipment.connection_manager import ConnectionManager
from ui.equipment.equipment_manager import EquipmentManager


class TopologyValidationCode(str, Enum):
    """
    Stable machine-readable validation result codes.
    """

    VALID = "valid"

    EMPTY_EQUIPMENT_ID = "empty_equipment_id"
    EMPTY_TERMINAL_ID = "empty_terminal_id"

    UNKNOWN_SOURCE_EQUIPMENT = (
        "unknown_source_equipment"
    )

    UNKNOWN_TARGET_EQUIPMENT = (
        "unknown_target_equipment"
    )

    UNKNOWN_SOURCE_TERMINAL = (
        "unknown_source_terminal"
    )

    UNKNOWN_TARGET_TERMINAL = (
        "unknown_target_terminal"
    )

    SELF_CONNECTION = "self_connection"

    DUPLICATE_CONNECTION = (
        "duplicate_connection"
    )


@dataclass(frozen=True)
class TopologyValidationResult:
    """
    Immutable result returned by TopologyValidator.

    ``valid`` determines whether the proposed operation may proceed.

    ``code`` provides a stable machine-readable reason.

    ``message`` provides a human-readable explanation suitable for
    diagnostics, logging, or UI feedback.
    """

    valid: bool
    code: TopologyValidationCode
    message: str

    @classmethod
    def success(cls) -> "TopologyValidationResult":
        return cls(
            valid=True,
            code=TopologyValidationCode.VALID,
            message="Topology validation successful.",
        )

    @classmethod
    def failure(
        cls,
        code: TopologyValidationCode,
        message: str,
    ) -> "TopologyValidationResult":
        return cls(
            valid=False,
            code=code,
            message=message,
        )


class TopologyValidator:
    """
    Validates logical SLD connection requests.

    The validator receives managers rather than a Qt scene or
    graphics objects. This keeps topology decisions independent
    from presentation.
    """

    def __init__(
        self,
        equipment_manager: EquipmentManager,
        connection_manager: ConnectionManager,
        *,
        allow_self_connection: bool = False,
        allow_duplicate_connections: bool = False,
    ) -> None:
        if equipment_manager is None:
            raise ValueError(
                "equipment_manager must not be None"
            )

        if connection_manager is None:
            raise ValueError(
                "connection_manager must not be None"
            )

        self._equipment_manager = equipment_manager
        self._connection_manager = connection_manager

        self._allow_self_connection = bool(
            allow_self_connection
        )

        self._allow_duplicate_connections = bool(
            allow_duplicate_connections
        )

    # ------------------------------------------------------------
    # Managers
    # ------------------------------------------------------------

    @property
    def equipment_manager(
        self,
    ) -> EquipmentManager:
        return self._equipment_manager

    @property
    def connection_manager(
        self,
    ) -> ConnectionManager:
        return self._connection_manager

    # ------------------------------------------------------------
    # Policy
    # ------------------------------------------------------------

    @property
    def allow_self_connection(self) -> bool:
        return self._allow_self_connection

    @property
    def allow_duplicate_connections(self) -> bool:
        return self._allow_duplicate_connections

    # ------------------------------------------------------------
    # Connection validation
    # ------------------------------------------------------------

    def validate_connection(
        self,
        connection: EquipmentConnection,
    ) -> TopologyValidationResult:
        """
        Validate one proposed logical connection.

        Validation is deliberately non-mutating.

        The connection is not added to the model by this method.
        """

        if connection is None:
            return TopologyValidationResult.failure(
                TopologyValidationCode.EMPTY_EQUIPMENT_ID,
                "Connection must not be None.",
            )

        if not connection.source_equipment_id:
            return TopologyValidationResult.failure(
                TopologyValidationCode.EMPTY_EQUIPMENT_ID,
                "Source equipment ID must not be empty.",
            )

        if not connection.target_equipment_id:
            return TopologyValidationResult.failure(
                TopologyValidationCode.EMPTY_EQUIPMENT_ID,
                "Target equipment ID must not be empty.",
            )

        if not connection.source_terminal_id:
            return TopologyValidationResult.failure(
                TopologyValidationCode.EMPTY_TERMINAL_ID,
                "Source terminal ID must not be empty.",
            )

        if not connection.target_terminal_id:
            return TopologyValidationResult.failure(
                TopologyValidationCode.EMPTY_TERMINAL_ID,
                "Target terminal ID must not be empty.",
            )

        source_equipment = (
            self._equipment_manager.get(
                connection.source_equipment_id
            )
        )

        if source_equipment is None:
            return TopologyValidationResult.failure(
                TopologyValidationCode.UNKNOWN_SOURCE_EQUIPMENT,
                (
                    "Unknown source equipment: "
                    f"{connection.source_equipment_id}"
                ),
            )

        target_equipment = (
            self._equipment_manager.get(
                connection.target_equipment_id
            )
        )

        if target_equipment is None:
            return TopologyValidationResult.failure(
                TopologyValidationCode.UNKNOWN_TARGET_EQUIPMENT,
                (
                    "Unknown target equipment: "
                    f"{connection.target_equipment_id}"
                ),
            )

        if not source_equipment.has_terminal(
            connection.source_terminal_id
        ):
            return TopologyValidationResult.failure(
                TopologyValidationCode.UNKNOWN_SOURCE_TERMINAL,
                (
                    "Unknown source terminal: "
                    f"{connection.source_equipment_id}:"
                    f"{connection.source_terminal_id}"
                ),
            )

        if not target_equipment.has_terminal(
            connection.target_terminal_id
        ):
            return TopologyValidationResult.failure(
                TopologyValidationCode.UNKNOWN_TARGET_TERMINAL,
                (
                    "Unknown target terminal: "
                    f"{connection.target_equipment_id}:"
                    f"{connection.target_terminal_id}"
                ),
            )

        if (
            not self._allow_self_connection
            and (
                connection.source_equipment_id
                == connection.target_equipment_id
            )
        ):
            return TopologyValidationResult.failure(
                TopologyValidationCode.SELF_CONNECTION,
                (
                    "Connections from an equipment instance "
                    "back to the same equipment instance are "
                    "not permitted."
                ),
            )

        if not self._allow_duplicate_connections:
            existing = (
                self._connection_manager
                .find_between_endpoints(
                    connection.source_endpoint,
                    connection.target_endpoint,
                )
            )

            for existing_connection in existing:
                if (
                    existing_connection.connection_id
                    != connection.connection_id
                ):
                    return TopologyValidationResult.failure(
                        TopologyValidationCode
                        .DUPLICATE_CONNECTION,
                        (
                            "A connection already exists between "
                            f"{connection.source_equipment_id}:"
                            f"{connection.source_terminal_id} and "
                            f"{connection.target_equipment_id}:"
                            f"{connection.target_terminal_id}."
                        ),
                    )

        return TopologyValidationResult.success()

    # ------------------------------------------------------------
    # Convenience validation
    # ------------------------------------------------------------

    def is_valid(
        self,
        connection: EquipmentConnection,
    ) -> bool:
        """
        Return only the validation status.
        """
        return self.validate_connection(
            connection
        ).valid

    def validate_endpoints(
        self,
        source_equipment_id: str,
        source_terminal_id: str,
        target_equipment_id: str,
        target_terminal_id: str,
    ) -> TopologyValidationResult:
        """
        Validate endpoint identities without requiring the caller
        to construct a temporary connection object.

        A temporary connection ID is used only for validation.
        No object is inserted into the model.
        """
        connection = EquipmentConnection(
            connection_id="__topology_validation__",
            source_equipment_id=source_equipment_id,
            source_terminal_id=source_terminal_id,
            target_equipment_id=target_equipment_id,
            target_terminal_id=target_terminal_id,
        )

        return self.validate_connection(
            connection
        )
