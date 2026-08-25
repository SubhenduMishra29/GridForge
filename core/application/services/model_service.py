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
- Construct Core model objects.
- Add objects through the public Network API.
- Resolve canonical objects through Network.get_by_id().
- Remove canonical Core objects through the public Network API.
- Register inverse operations with the active Transaction.
- Return ApplicationResult objects.

ModelService does NOT:
- resolve EndpointReference objects;
- access UI/Qt/SLD state;
- access Network internal collections;
- access NetworkRegistry directly;
- perform direct registry manipulation;
- own transactions;
- commit or rollback transactions.

Endpoint resolution is performed by EndpointResolver in the
Application command-handler layer before create_line() or
create_transformer() is called.
"""

from __future__ import annotations

from typing import Any

from ..errors import DomainError, ResourceError
from ..results import ApplicationResult
from ..transaction import Transaction

from ...model.base import ElectricalObject
from ...model.bus import Bus, BusType
from ...model.line import Line
from ...model.terminal import Terminal
from ...model.transformer import Transformer


class ModelService:
    """
    Application service for Core model mutation.

    Network remains the authoritative owner of model objects.

    The service accepts already-resolved Core endpoints for
    branch-based equipment. It never resolves EndpointReference
    values itself.
    """

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError("network is required.")

        self._network = network

    # ============================================================
    # BUS
    # ============================================================

    def create_bus(
        self,
        *,
        bus_id: str,
        name: str | None = None,
        bus_type: str | BusType = "PQ",
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

        Application command terminology is translated here to the
        actual Core Bus constructor terminology:

            voltage   -> voltage_magnitude
            angle     -> voltage_angle
            p_spec    -> p
            q_spec    -> q
            v_setpoint -> voltage_setpoint
        """

        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")

        self._ensure_not_exists(
            "bus",
            bus_id,
            "Bus",
        )

        bus = Bus(
            id=bus_id,
            name="" if name is None else name,
            bus_type=bus_type,
            voltage_magnitude=voltage,
            voltage_angle=angle,
            p=p_spec,
            q=q_spec,
            voltage_setpoint=v_setpoint,
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
        """

        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")

        bus = self._get_required(
            "bus",
            bus_id,
            "Bus",
        )

        if not isinstance(bus, Bus):
            raise DomainError(
                code="INVALID_BUS_REFERENCE",
                message=f"Object {bus_id!r} is not a Bus.",
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

    # ============================================================
    # LINE
    # ============================================================

    def create_line(
        self,
        *,
        line_id: str,
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

        EndpointReference resolution belongs to EndpointResolver.
        This method accepts only canonical Bus/Terminal objects.
        """

        self._require_transaction(transaction)
        self._require_id(line_id, "line_id")

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
                message="Line endpoints must be different.",
                details={
                    "line_id": line_id,
                },
            )

        self._ensure_not_exists(
            "line",
            line_id,
            "Line",
        )

        line = Line(
            id=line_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name="" if name is None else name,
            rate_mva=rate_mva,
        )

        self._network.add_line(line)

        transaction.record_undo(
            lambda line=line: self._network.remove_line(line)
        )

        return ApplicationResult.success_result(
            value=line,
            message=f"Line created: {line_id}",
            metadata={
                "object_type": "line",
                "object_id": line_id,
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

        line = self._get_required(
            "line",
            line_id,
            "Line",
        )

        if not isinstance(line, Line):
            raise DomainError(
                code="INVALID_LINE_REFERENCE",
                message=f"Object {line_id!r} is not a Line.",
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

    # ============================================================
    # TRANSFORMER
    # ============================================================

    def create_transformer(
        self,
        *,
        transformer_id: str,
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

        The current Application command contract does not expose
        transformer b, while the Core Transformer constructor
        provides b with a default of 0.0. Therefore the Core
        default is intentionally retained.
        """

        self._require_transaction(transaction)
        self._require_id(
            transformer_id,
            "transformer_id",
        )

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
                message="Transformer endpoints must be different.",
                details={
                    "transformer_id": transformer_id,
                },
            )

        self._ensure_not_exists(
            "transformer",
            transformer_id,
            "Transformer",
        )

        transformer = Transformer(
            id=transformer_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            tap=tap,
            shift=shift,
            name="" if name is None else name,
            rate_mva=rate_mva,
        )

        self._network.add_transformer(transformer)

        transaction.record_undo(
            lambda transformer=transformer:
                self._network.remove_transformer(transformer)
        )

        return ApplicationResult.success_result(
            value=transformer,
            message=f"Transformer created: {transformer_id}",
            metadata={
                "object_type": "transformer",
                "object_id": transformer_id,
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

        transformer = self._get_required(
            "transformer",
            transformer_id,
            "Transformer",
        )

        if not isinstance(transformer, Transformer):
            raise DomainError(
                code="INVALID_TRANSFORMER_REFERENCE",
                message=(
                    f"Object {transformer_id!r} "
                    "is not a Transformer."
                ),
                details={
                    "transformer_id": transformer_id,
                    "object_type": type(transformer).__name__,
                },
            )

        self._network.remove_transformer(transformer)

        transaction.record_undo(
            lambda transformer=transformer:
                self._network.add_transformer(transformer)
        )

        return ApplicationResult.success_result(
            value=transformer,
            message=f"Transformer deleted: {transformer_id}",
            metadata={
                "object_type": "transformer",
                "object_id": transformer_id,
            },
        )

    # ============================================================
    # CANONICAL NETWORK LOOKUP
    # ============================================================

    def _get_required(
        self,
        element_type: str,
        object_id: str,
        display_type: str,
    ) -> Any:
        """
        Resolve a canonical Core object through Network.get_by_id().

        Network remains the only Application-visible lookup façade.
        """

        try:
            return self._network.get_by_id(
                element_type,
                object_id,
            )
        except KeyError as exc:
            raise ResourceError(
                code=f"{element_type.upper()}_NOT_FOUND",
                message=(
                    f"{display_type} not found: "
                    f"{object_id}"
                ),
                details={
                    "object_type": element_type,
                    "object_id": object_id,
                },
            ) from exc

    def _ensure_not_exists(
        self,
        element_type: str,
        object_id: str,
        display_type: str,
    ) -> None:
        """
        Ensure an object ID is not already registered.

        Lookup goes through Network.get_by_id(); the registry
        remains completely hidden from this service.
        """

        try:
            self._network.get_by_id(
                element_type,
                object_id,
            )
        except KeyError:
            return

        raise DomainError(
            code=f"{element_type.upper()}_ALREADY_EXISTS",
            message=(
                f"{display_type} already exists: "
                f"{object_id}"
            ),
            details={
                "object_type": element_type,
                "object_id": object_id,
            },
        )

    # ============================================================
    # ENDPOINT VALIDATION
    # ============================================================

    @staticmethod
    def _validate_endpoint(
        endpoint: object,
        parameter_name: str,
    ) -> None:
        """
        Validate an already-resolved Core endpoint.

        This deliberately does not perform endpoint resolution.
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
                    "object_type": type(endpoint).__name__,
                },
            )

    # ============================================================
    # TRANSACTION VALIDATION
    # ============================================================

    @staticmethod
    def _require_transaction(
        transaction: Transaction,
    ) -> None:
        """
        Ensure an active Application Transaction is supplied.
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

    # ============================================================
    # ID VALIDATION
    # ============================================================

    @staticmethod
    def _require_id(
        value: str,
        parameter_name: str,
    ) -> None:
        """
        Validate a GridForge object identifier.
        """

        if not isinstance(value, str):
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
