# ============================================================
# File: core/application/services/model_service.py
# GridForge V2
# Author: Subhendu Mishra
# ============================================================

"""
Headless Application Model Service.

ModelService is the Application-layer service responsible for
creating, updating, and deleting Core model objects.

Responsibilities
----------------
- Validate Application-level model input.
- Construct Core model objects.
- Add objects through the public Network API.
- Resolve canonical objects through Network.get_by_id().
- Remove canonical Core objects through the public Network API.
- Mutate Core model objects through their existing domain APIs.
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

Load creation
-------------

A Load is a single-terminal injection model.

CreateLoadCommand carries the Load's model/value data:

    load_id
    p
    q
    name
    in_service

The Load is initially created without a resolved topology
endpoint. Connectivity is handled separately by the
appropriate Application topology workflow.

The service therefore does not resolve or construct a Terminal
from an Application command.

Load update
-----------

UpdateLoadCommand mutates only the Load's mutable equipment
state:

    load_id
    name
    p
    q
    in_service

Topology is deliberately outside this operation.

Each requested mutation is routed through the Load's existing
domain mutation contract:

    name
        -> load.name = value

    p
        -> load.p = value

    q
        -> load.q = value

    in_service
        -> load.set_in_service(value)

The service never performs generic attribute assignment.

The complete pre-update state is captured before mutation and
restored through one transaction undo operation.
"""

from __future__ import annotations

from typing import Any

from ..errors import DomainError, ResourceError
from ..results import ApplicationResult
from ..transaction import Transaction

from ...model.bus import Bus, BusType
from ...model.line import Line
from ...model.load import Load
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
        v_setpoint: float | None = None,
        q_min: float | None = float("-inf"),
        q_max: float | None = float("inf"),
        transaction: Transaction,
    ) -> ApplicationResult[Bus]:
        """
        Create and register a Bus.

        Application command terminology is translated here to the
        actual Core Bus constructor terminology:

            bus_id      -> id
            voltage     -> voltage_magnitude
            angle       -> voltage_angle
            p_spec      -> p
            q_spec      -> q
            v_setpoint  -> voltage_setpoint

        The Application command represents unbounded reactive-power
        limits using +/- infinity. The Core Bus represents an
        unspecified/unbounded limit using None.
        """

        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")

        self._ensure_not_exists(
            "bus",
            bus_id,
            "Bus",
        )

        core_voltage_setpoint = (
            1.0
            if v_setpoint is None
            else v_setpoint
        )

        core_q_min = (
            None
            if q_min is None or q_min == float("-inf")
            else q_min
        )

        core_q_max = (
            None
            if q_max is None or q_max == float("inf")
            else q_max
        )

        bus = Bus(
            id=bus_id,
            name="" if name is None else name,
            bus_type=bus_type,
            voltage_magnitude=voltage,
            voltage_angle=angle,
            p=p_spec,
            q=q_spec,
            voltage_setpoint=core_voltage_setpoint,
            q_min=core_q_min,
            q_max=core_q_max,
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
        This method accepts only already-resolved Bus/Terminal
        objects.
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

        EndpointReference resolution belongs to EndpointResolver.
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
    # LOAD
    # ============================================================

    def create_load(
        self,
        *,
        load_id: str,
        p: float = 0.0,
        q: float = 0.0,
        name: str | None = None,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Load]:
        """
        Create and register a Load.

        Load creation is intentionally independent of topology.

        The Load model owns one Terminal, but the command/service
        creation path does not resolve or attach that Terminal to
        a Bus. Topology attachment is a separate Application
        concern.
        """

        self._require_transaction(transaction)
        self._require_id(load_id, "load_id")

        self._ensure_not_exists(
            "load",
            load_id,
            "Load",
        )

        load = Load(
            id=load_id,
            p=p,
            q=q,
            name="" if name is None else name,
            in_service=in_service,
        )

        self._network.add_load(load)

        transaction.record_undo(
            lambda load=load: self._network.remove_load(load)
        )

        return ApplicationResult.success_result(
            value=load,
            message=f"Load created: {load_id}",
            metadata={
                "object_type": "load",
                "object_id": load_id,
            },
        )

    def update_load(
        self,
        *,
        load_id: str,
        name: str | None = None,
        p: float | None = None,
        q: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Load]:
        """
        Update mutable Load properties.

        This operation changes equipment state only.

        It does not:
        - resolve endpoints;
        - attach or detach terminals;
        - modify topology;
        - modify SLD state.

        Each requested property is mutated through the Load's
        existing domain API.

        Undo restores the complete pre-update state through one
        inverse transaction operation.
        """

        self._require_transaction(transaction)
        self._require_id(load_id, "load_id")

        load = self._get_required(
            "load",
            load_id,
            "Load",
        )

        if not isinstance(load, Load):
            raise DomainError(
                code="INVALID_LOAD_REFERENCE",
                message=f"Object {load_id!r} is not a Load.",
                details={
                    "load_id": load_id,
                    "object_type": type(load).__name__,
                },
            )

        if (
            name is None
            and p is None
            and q is None
            and in_service is None
        ):
            raise DomainError(
                code="NO_LOAD_UPDATE",
                message=(
                    "At least one mutable Load property "
                    "must be specified."
                ),
                details={
                    "load_id": load_id,
                },
            )

        # --------------------------------------------------------
        # Capture complete pre-update state.
        # --------------------------------------------------------

        old_name = load.name
        old_p = load.p
        old_q = load.q
        old_in_service = load.in_service

        # --------------------------------------------------------
        # Perform only requested domain mutations.
        #
        # P/Q use the Load setters, preserving the Load's existing
        # validation.
        #
        # Operational state uses the explicit domain mutation API.
        # --------------------------------------------------------

        if name is not None:
            load.name = name

        if p is not None:
            load.p = p

        if q is not None:
            load.q = q

        if in_service is not None:
            load.set_in_service(
                in_service
            )

        # --------------------------------------------------------
        # Register one complete inverse operation.
        #
        # The closure captures the pre-update state, not the
        # command values, so undo restores exactly the state that
        # existed immediately before this execution.
        # --------------------------------------------------------

        def restore_previous_state() -> None:
            load.name = old_name
            load.p = old_p
            load.q = old_q
            load.set_in_service(
                old_in_service
            )

        transaction.record_undo(
            restore_previous_state
        )

        return ApplicationResult.success_result(
            value=load,
            message=f"Load updated: {load_id}",
            metadata={
                "object_type": "load",
                "object_id": load_id,
            },
        )

    def delete_load(
        self,
        *,
        load_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Load]:
        """
        Delete the canonical Load identified by load_id.
        """

        self._require_transaction(transaction)
        self._require_id(load_id, "load_id")

        load = self._get_required(
            "load",
            load_id,
            "Load",
        )

        if not isinstance(load, Load):
            raise DomainError(
                code="INVALID_LOAD_REFERENCE",
                message=f"Object {load_id!r} is not a Load.",
                details={
                    "load_id": load_id,
                    "object_type": type(load).__name__,
                },
            )

        self._network.remove_load(load)

        transaction.record_undo(
            lambda load=load: self._network.add_load(load)
        )

        return ApplicationResult.success_result(
            value=load,
            message=f"Load deleted: {load_id}",
            metadata={
                "object_type": "load",
                "object_id": load_id,
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

        ModelService never creates, commits, or rolls back the
        transaction.
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
