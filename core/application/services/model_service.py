# ============================================================
# File: core/application/services/model_service.py
# GridForge V2 — Application Model Service
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Model Service
========================================

Application-layer service responsible for authoritative model
mutation.

ModelService never owns authoritative state. It delegates
canonical membership to Network and records inverse operations
with the active Transaction.

Grid
----

Grid is a first-class electrical network element.

It is not a Network container.

Existing Grid electrical quantities:

    p_mw               -> MW
    q_mvar             -> MVAr
    short_circuit_mva  -> MVA

No additional Grid power-rating field is introduced here.
"""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.transaction import Transaction
from core.errors import DomainError, ResourceError
from core.model.bus import Bus
from core.model.grid import Grid
from core.model.line import Line
from core.model.load import Load
from core.model.terminal import Terminal
from core.model.transformer import Transformer
from core.network.network import Network


class ModelService:
    """
    Application-layer service for authoritative model mutation.
    """

    def __init__(
        self,
        network: Network,
    ) -> None:
        if not isinstance(network, Network):
            raise TypeError(
                "network must be a Network."
            )

        self._network = network

    # ========================================================
    # BUS
    # ========================================================

    def create_bus(
        self,
        *,
        bus_id: str,
        name: str | None = None,
        nominal_voltage_kv: float = 0.0,
        transaction: Transaction,
    ) -> ApplicationResult[Bus]:
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
            nominal_voltage_kv=nominal_voltage_kv,
        )

        self._network.add_bus(bus)

        transaction.record_undo(
            lambda bus=bus:
                self._network.remove_bus(bus)
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
            lambda bus=bus:
                self._network.add_bus(bus)
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
        line_id: str,
        endpoint_from: Bus | Terminal,
        endpoint_to: Bus | Terminal,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
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
            lambda line=line:
                self._network.remove_line(line)
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
            lambda line=line:
                self._network.add_line(line)
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
        transformer_id: str,
        endpoint_from: Bus | Terminal,
        endpoint_to: Bus | Terminal,
        r: float = 0.0,
        x: float = 0.0,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
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
                message=(
                    "Transformer endpoints must be different."
                ),
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
                self._network.remove_transformer(
                    transformer
                )
        )

        return ApplicationResult.success_result(
            value=transformer,
            message=(
                f"Transformer created: {transformer_id}"
            ),
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
                f"Transformer deleted: {transformer_id}"
            ),
            metadata={
                "object_type": "transformer",
                "object_id": transformer_id,
            },
        )

    # ========================================================
    # LOAD
    # ========================================================

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
            lambda load=load:
                self._network.remove_load(load)
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

        old_name = load.name
        old_p = load.p
        old_q = load.q
        old_in_service = load.in_service

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
            lambda load=load:
                self._network.add_load(load)
        )

        return ApplicationResult.success_result(
            value=load,
            message=f"Load deleted: {load_id}",
            metadata={
                "object_type": "load",
                "object_id": load_id,
            },
        )

    # ========================================================
    # GRID
    # ========================================================

    def create_grid(
        self,
        *,
        grid_id: str,
        endpoint: Bus | Terminal | None = None,
        name: str | None = None,
        nominal_voltage_kv: float = 0.0,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        angle_deg: float = 0.0,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        short_circuit_mva: float = 0.0,
        x_over_r: float = 0.0,
        z1_pu: complex = 0j,
        z2_pu: complex = 0j,
        z0_pu: complex = 0j,
        in_service: bool = True,
        grounded: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Grid]:
        """
        Create and register a Grid.

        Grid is a first-class network element.

        p_mw:
            Active power in MW.

        q_mvar:
            Reactive power in MVAr.

        short_circuit_mva:
            Short-circuit strength in MVA.

        Endpoint resolution is deliberately outside this service.
        If supplied, endpoint must already be a Core Bus or
        Terminal.
        """

        self._require_transaction(transaction)
        self._require_id(grid_id, "grid_id")

        if endpoint is not None:
            self._validate_endpoint(
                endpoint,
                "endpoint",
            )

        self._ensure_not_exists(
            "grid",
            grid_id,
            "Grid",
        )

        grid = Grid(
            id=grid_id,
            name="" if name is None else name,
            endpoint=endpoint,
            nominal_voltage_kv=nominal_voltage_kv,
            frequency_hz=frequency_hz,
            voltage_pu=voltage_pu,
            angle_deg=angle_deg,
            p_mw=p_mw,
            q_mvar=q_mvar,
            short_circuit_mva=short_circuit_mva,
            x_over_r=x_over_r,
            z1_pu=z1_pu,
            z2_pu=z2_pu,
            z0_pu=z0_pu,
            in_service=in_service,
            grounded=grounded,
        )

        self._network.add_grid(grid)

        transaction.record_undo(
            lambda grid=grid:
                self._network.remove_grid(grid)
        )

        return ApplicationResult.success_result(
            value=grid,
            message=f"Grid created: {grid_id}",
            metadata={
                "object_type": "grid",
                "object_id": grid_id,
            },
        )

    def update_grid(
        self,
        *,
        grid_id: str,
        name: str | None = None,
        nominal_voltage_kv: float | None = None,
        frequency_hz: float | None = None,
        voltage_pu: float | None = None,
        angle_deg: float | None = None,
        p_mw: float | None = None,
        q_mvar: float | None = None,
        short_circuit_mva: float | None = None,
        x_over_r: float | None = None,
        z1_pu: complex | None = None,
        z2_pu: complex | None = None,
        z0_pu: complex | None = None,
        in_service: bool | None = None,
        grounded: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Grid]:
        """
        Update mutable Grid state.

        Endpoint connectivity is intentionally not modified by
        this method. Connectivity changes belong to topology
        commands/services.
        """

        self._require_transaction(transaction)
        self._require_id(grid_id, "grid_id")

        grid = self._get_required(
            "grid",
            grid_id,
            "Grid",
        )

        if not isinstance(grid, Grid):
            raise DomainError(
                code="INVALID_GRID_REFERENCE",
                message=f"Object {grid_id!r} is not a Grid.",
                details={
                    "grid_id": grid_id,
                    "object_type": type(grid).__name__,
                },
            )

        if (
            name is None
            and nominal_voltage_kv is None
            and frequency_hz is None
            and voltage_pu is None
            and angle_deg is None
            and p_mw is None
            and q_mvar is None
            and short_circuit_mva is None
            and x_over_r is None
            and z1_pu is None
            and z2_pu is None
            and z0_pu is None
            and in_service is None
            and grounded is None
        ):
            raise DomainError(
                code="NO_GRID_UPDATE",
                message=(
                    "At least one mutable Grid property "
                    "must be specified."
                ),
                details={
                    "grid_id": grid_id,
                },
            )

        old_name = grid.name
        old_nominal_voltage_kv = (
            grid.nominal_voltage_kv
        )
        old_frequency_hz = grid.frequency_hz
        old_voltage_pu = grid.voltage_pu
        old_angle_deg = grid.angle_deg
        old_p_mw = grid.p_mw
        old_q_mvar = grid.q_mvar
        old_short_circuit_mva = (
            grid.short_circuit_mva
        )
        old_x_over_r = grid.x_over_r
        old_z1_pu = grid.z1_pu
        old_z2_pu = grid.z2_pu
        old_z0_pu = grid.z0_pu
        old_in_service = grid.in_service
        old_grounded = grid.grounded

        if name is not None:
            grid.name = name

        if nominal_voltage_kv is not None:
            grid.nominal_voltage_kv = (
                nominal_voltage_kv
            )

        if frequency_hz is not None:
            grid.frequency_hz = frequency_hz

        if short_circuit_mva is not None:
            grid.short_circuit_mva = (
                short_circuit_mva
            )

        if x_over_r is not None:
            grid.x_over_r = x_over_r

        if grounded is not None:
            grid.grounded = grounded

        if (
            voltage_pu is not None
            or angle_deg is not None
        ):
            grid.set_voltage(
                grid.voltage_pu
                if voltage_pu is None
                else voltage_pu,
                grid.angle_deg
                if angle_deg is None
                else angle_deg,
            )

        if (
            p_mw is not None
            or q_mvar is not None
        ):
            grid.set_power(
                grid.p_mw
                if p_mw is None
                else p_mw,
                grid.q_mvar
                if q_mvar is None
                else q_mvar,
            )

        if (
            z1_pu is not None
            or z2_pu is not None
            or z0_pu is not None
        ):
            grid.set_sequence_impedances(
                grid.z1_pu
                if z1_pu is None
                else z1_pu,
                grid.z2_pu
                if z2_pu is None
                else z2_pu,
                grid.z0_pu
                if z0_pu is None
                else z0_pu,
            )

        if in_service is not None:
            if in_service:
                grid.put_in_service()
            else:
                grid.take_out_of_service()

        def restore_previous_state() -> None:
            grid.name = old_name
            grid.nominal_voltage_kv = (
                old_nominal_voltage_kv
            )
            grid.frequency_hz = old_frequency_hz
            grid.short_circuit_mva = (
                old_short_circuit_mva
            )
            grid.x_over_r = old_x_over_r
            grid.grounded = old_grounded

            grid.set_voltage(
                old_voltage_pu,
                old_angle_deg,
            )

            grid.set_power(
                old_p_mw,
                old_q_mvar,
            )

            grid.set_sequence_impedances(
                old_z1_pu,
                old_z2_pu,
                old_z0_pu,
            )

            if old_in_service:
                grid.put_in_service()
            else:
                grid.take_out_of_service()

        transaction.record_undo(
            restore_previous_state
        )

        return ApplicationResult.success_result(
            value=grid,
            message=f"Grid updated: {grid_id}",
            metadata={
                "object_type": "grid",
                "object_id": grid_id,
            },
        )

    def delete_grid(
        self,
        *,
        grid_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Grid]:
        """
        Delete the canonical Grid identified by grid_id.
        """

        self._require_transaction(transaction)
        self._require_id(grid_id, "grid_id")

        grid = self._get_required(
            "grid",
            grid_id,
            "Grid",
        )

        if not isinstance(grid, Grid):
            raise DomainError(
                code="INVALID_GRID_REFERENCE",
                message=f"Object {grid_id!r} is not a Grid.",
                details={
                    "grid_id": grid_id,
                    "object_type": type(grid).__name__,
                },
            )

        self._network.remove_grid(grid)

        transaction.record_undo(
            lambda grid=grid:
                self._network.add_grid(grid)
        )

        return ApplicationResult.success_result(
            value=grid,
            message=f"Grid deleted: {grid_id}",
            metadata={
                "object_type": "grid",
                "object_id": grid_id,
            },
        )

    # ========================================================
    # LOOKUP
    # ========================================================

    def _get_required(
        self,
        element_type: str,
        object_id: str,
        display_type: str,
    ) -> object:
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

    # ========================================================
    # ENDPOINT VALIDATION
    # ========================================================

    @staticmethod
    def _validate_endpoint(
        endpoint: object,
        parameter_name: str,
    ) -> None:
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

    # ========================================================
    # TRANSACTION VALIDATION
    # ========================================================

    @staticmethod
    def _require_transaction(
        transaction: Transaction,
    ) -> None:
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

    # ========================================================
    # ID VALIDATION
    # ========================================================

    @staticmethod
    def _require_id(
        value: str,
        parameter_name: str,
    ) -> None:
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
