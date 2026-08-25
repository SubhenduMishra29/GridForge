# ============================================================
# File: core/application/services/model_service.py
# GridForge V2
# Author: Subhendu Mishra
# ============================================================

"""
Headless Application Model Service.

ModelService is the Application-layer service responsible for
creating and deleting Core model objects.

Responsibilities
----------------
- Validate Application-level model input.
- Create Core model objects.
- Add objects through the public Network API.
- Remove canonical Core objects through the public Network API.
- Register inverse operations with the active Transaction.
- Return ApplicationResult objects.

ModelService does NOT:
- resolve EndpointReference objects;
- access UI/Qt/SLD state;
- access Network internal collections;
- perform direct registry manipulation;
- own transactions;
- commit or rollback transactions;
"""

from __future__ import annotations

from typing import Any

from ..errors import DomainError, ResourceError
from ..results import ApplicationResult
from ..transaction import Transaction

from ...model.bus import Bus
from ...model.line import Line
from ...model.transformer import Transformer
from ...model.terminal import Terminal


class ModelService:
    """
    Application service for Core model mutation.

    The service receives already-resolved Core endpoints from
    command handlers.

    Network remains the authoritative owner of model objects.
    """

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError("network is required.")

        self._network = network

    # ========================================================
    # BUS
    # ========================================================

    def create_bus(
        self,
        *,
        bus_id: str,
        name: str | None = None,
        bus_type: str = "PQ",
        voltage: float = 1.0,
        angle: float = 0.0,
        p_spec: float = 0.0,
        q_spec: float = 0.0,
        v_setpoint: float = 1.0,
        q_min: float | None = None,
        q_max: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Bus]:
        """
        Create and register a Bus.
        """

        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")

        if self._network.get_by_id(bus_id) is not None:
            raise DomainError(
                code="BUS_ALREADY_EXISTS",
                message=f"Bus already exists: {bus_id}",
                details={"bus_id": bus_id},
            )

        bus = Bus(
            bus_id=bus_id,
            name=name,
            bus_type=bus_type,
            voltage=voltage,
            angle=angle,
            p_spec=p_spec,
            q_spec=q_spec,
            v_setpoint=v_setpoint,
            q_min=q_min,
            q_max=q_max,
        )

        self._network.add_bus(bus)

        transaction.record_undo(
            lambda bus=bus: self._network.remove_bus(bus)
        )

        return ApplicationResult.success_result(
            value=bus,
            message=f"Bus created: {bus_id}",
            metadata={
                "object_type": "bus",
                "object_id": bus_id,
            },
        )

    def delete_bus(
        self,
        *,
        bus_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Bus]:
        """
        Delete the canonical Bus identified by bus_id.

        Network.get_by_id() is the authoritative lookup boundary.
        """

        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")

        bus = self._network.get_by_id(bus_id)

        if bus is None:
            raise ResourceError(
                code="BUS_NOT_FOUND",
                message=f"Bus not found: {bus_id}",
                details={"bus_id": bus_id},
            )

        if not isinstance(bus, Bus):
            raise DomainError(
                code="INVALID_BUS_REFERENCE",
                message=(
                    f"Object {bus_id!r} is not a Bus."
                ),
                details={
                    "bus_id": bus_id,
                    "object_type": type(bus).__name__,
                },
            )

        self._network.remove_bus(bus)

        transaction.record_undo(
            lambda bus=bus: self._network.add_bus(bus)
        )

        return ApplicationResult.success_result(
            value=bus,
            message=f"Bus deleted: {bus_id}",
            metadata={
                "object_type": "bus",
                "object_id": bus_id,
            },
        )

    # ========================================================
    # LINE
    # ========================================================

    def create_line(
        self,
        *,
        endpoint_from: Bus | Terminal,
        endpoint_to: Bus | Terminal,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        name: str | None = None,
        rate_mva: float = 100.0,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
        """
        Create and register a Line between resolved Core endpoints.
        """

        self._require_transaction(transaction)

        self._validate_endpoint(
            endpoint_from,
            "endpoint_from",
        )
        self._validate_endpoint(
            endpoint_to,
            "endpoint_to",
        )

        if endpoint_from is endpoint_to:
            raise DomainError(
                code="INVALID_LINE_ENDPOINTS",
                message=(
                    "Line endpoints must be different."
                ),
                details={},
            )

        line = Line(
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
        )

        self._network.add_line(line)

        transaction.record_undo(
            lambda line=line: self._network.remove_line(line)
        )

        return ApplicationResult.success_result(
            value=line,
            message="Line created.",
            metadata={
                "object_type": "line",
                "object_id": str(line.id),
            },
        )

    def delete_line(
        self,
        *,
        line_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
        """
        Delete the canonical Line identified by line_id.
        """

        self._require_transaction(transaction)
        self._require_id(line_id, "line_id")

        line = self._network.get_by_id(line_id)

        if line is None:
            raise ResourceError(
                code="LINE_NOT_FOUND",
                message=f"Line not found: {line_id}",
                details={"line_id": line_id},
            )

        if not isinstance(line, Line):
            raise DomainError(
                code="INVALID_LINE_REFERENCE",
                message=(
                    f"Object {line_id!r} is not a Line."
                ),
                details={
                    "line_id": line_id,
                    "object_type": type(line).__name__,
                },
            )

        self._network.remove_line(line)

        transaction.record_undo(
            lambda line=line: self._network.add_line(line)
        )

        return ApplicationResult.success_result(
            value=line,
            message=f"Line deleted: {line_id}",
            metadata={
                "object_type": "line",
                "object_id": line_id,
            },
        )

    # ========================================================
    # TRANSFORMER
    # ========================================================

    def create_transformer(
        self,
        *,
        endpoint_from: Bus | Terminal,
        endpoint_to: Bus | Terminal,
        r: float = 0.0,
        x: float = 0.0,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str | None = None,
        rate_mva: float = 100.0,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
        """
        Create and register a Transformer between resolved
        Core endpoints.
        """

        self._require_transaction(transaction)

        self._validate_endpoint(
            endpoint_from,
            "endpoint_from",
        )
        self._validate_endpoint(
            endpoint_to,
            "endpoint_to",
        )

        if endpoint_from is endpoint_to:
            raise DomainError(
                code="INVALID_TRANSFORMER_ENDPOINTS",
                message=(
                    "Transformer endpoints must be different."
                ),
                details={},
            )

        transformer = Transformer(
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            tap=tap,
            shift=shift,
            name=name,
            rate_mva=rate_mva,
        )

        self._network.add_transformer(
            transformer
        )

        transaction.record_undo(
            lambda transformer=transformer:
                self._network.remove_transformer(
                    transformer
                )
        )

        return ApplicationResult.success_result(
            value=transformer,
            message="Transformer created.",
            metadata={
                "object_type": "transformer",
                "object_id": str(transformer.id),
            },
        )

    def delete_transformer(
        self,
        *,
        transformer_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
        """
        Delete the canonical Transformer identified by
        transformer_id.
        """

        self._require_transaction(transaction)
        self._require_id(
            transformer_id,
            "transformer_id",
        )

        transformer = self._network.get_by_id(
            transformer_id
        )

        if transformer is None:
            raise ResourceError(
                code="TRANSFORMER_NOT_FOUND",
                message=(
                    "Transformer not found: "
                    f"{transformer_id}"
                ),
                details={
                    "transformer_id": transformer_id,
                },
            )

        if not isinstance(
            transformer,
            Transformer,
        ):
            raise DomainError(
                code="INVALID_TRANSFORMER_REFERENCE",
                message=(
                    f"Object {transformer_id!r} "
                    "is not a Transformer."
                ),
                details={
                    "transformer_id": transformer_id,
                    "object_type": (
                        type(transformer).__name__
                    ),
                },
            )

        self._network.remove_transformer(
            transformer
        )

        transaction.record_undo(
            lambda transformer=transformer:
                self._network.add_transformer(
                    transformer
                )
        )

        return ApplicationResult.success_result(
            value=transformer,
            message=(
                "Transformer deleted: "
                f"{transformer_id}"
            ),
            metadata={
                "object_type": "transformer",
                "object_id": transformer_id,
            },
        )

    # ========================================================
    # ENDPOINT VALIDATION
    # ========================================================

    @staticmethod
    def _validate_endpoint(
        endpoint: object,
        parameter_name: str,
    ) -> None:
        """
        Validate an already-resolved Core endpoint.

        EndpointReference resolution belongs to the command
        handler, not this service.
        """

        if not isinstance(
            endpoint,
            (Bus, Terminal),
        ):
            raise DomainError(
                code="INVALID_ENDPOINT",
                message=(
                    f"{parameter_name} must be a "
                    "Bus or Terminal."
                ),
                details={
                    "parameter": parameter_name,
                    "object_type": (
                        type(endpoint).__name__
                    ),
                },
            )

    # ========================================================
    # VALIDATION HELPERS
    # ========================================================

    @staticmethod
    def _require_transaction(
        transaction: Transaction,
    ) -> None:
        """
        Ensure a live Transaction is supplied.
        """

        if not isinstance(
            transaction,
            Transaction,
        ):
            raise TypeError(
                "transaction must be a Transaction."
            )

        if not transaction.active:
            raise RuntimeError(
                "Transaction must be active."
            )

    @staticmethod
    def _require_id(
        value: str,
        parameter_name: str,
    ) -> None:
        """
        Validate a model identifier.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{parameter_name} must be str."
            )

        if not value.strip():
            raise ValueError(
                f"{parameter_name} must not be empty."
            )


__all__ = [
    "ModelService",
]
