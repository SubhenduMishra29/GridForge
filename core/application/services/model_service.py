# ============================================================
# File: core/application/services/model_service.py
# GridForge V2 — Headless Model Application Service
# ============================================================
"""
GridForge V2
============

Module:
    core.application.services.model_service

Purpose
-------
Provides Application-level orchestration for creation and removal
of canonical Core model objects.

Architectural Position
----------------------

    Application Command
            |
            v
       ModelService
            |
            +----> Core Model
            |
            +----> Core Network
            |
            v
       ApplicationResult

The service coordinates Application operations.

The Core model and Network remain authoritative.

Responsibilities
----------------
ModelService is responsible for:

    * validating Application-level input;
    * resolving canonical Core model objects;
    * constructing canonical Core model objects;
    * registering objects through public Network APIs;
    * removing objects through public Network APIs;
    * returning ApplicationResult objects;
    * translating expected Core failures into Application errors.

ModelService does NOT:

    * maintain a second collection of model objects;
    * manipulate Network internals;
    * maintain topology indexes;
    * maintain topology revisions;
    * maintain Y-bus revisions;
    * directly mutate Network private state;
    * perform engineering calculations;
    * own UI state;
    * create SLD graphics objects;
    * depend on Qt.

Network Ownership
-----------------
Once a model object is created, the Network becomes responsible
for incorporating that object into the assembled network.

Removal follows the same ownership boundary.

For example:

    network.add_bus(bus)
    network.remove_bus(bus)

and:

    network.add_line(line)
    network.remove_line(line)

and:

    network.add_transformer(transformer)
    network.remove_transformer(transformer)

The service MUST NOT directly manipulate:

    network.buses
    network.lines
    network.transformers
    network.bus_index
    network._invalidate_topology()
    network._invalidate_ybus()

Bus Deletion
------------
Bus deletion is intentionally strict.

The Application service resolves the canonical Bus from the
Network and delegates the actual removal to:

    Network.remove_bus()

Network.remove_bus() owns:

    * reference checking;
    * canonical collection mutation;
    * bus-index rebuilding;
    * topology invalidation;
    * Y-bus invalidation.

Line Lifecycle
--------------
Line physical connectivity is owned by the Line model through:

    line.from_terminal
    line.to_terminal

The Application service does not manipulate those terminals
during network membership operations.

Creation:

    Line(...)
        |
        v
    network.add_line(line)

Deletion:

    network.remove_line(line)

Network.remove_line() removes Network membership and invalidates
derived topology/Y-bus state.

It does not disconnect either Line terminal.

Transformer Lifecycle
---------------------
Transformer physical connectivity is owned by the Transformer
model through:

    transformer.from_terminal
    transformer.to_terminal

The Application service does not manipulate those terminals
during network membership operations.

Creation:

    Transformer(...)
        |
        v
    network.add_transformer(transformer)

Deletion:

    network.remove_transformer(transformer)

Network removal owns Network membership and derived-state
invalidation.

It does not disconnect either Transformer terminal.

This keeps three concepts separate:

    Terminal connectivity
        model responsibility

    Network membership
        network responsibility

    Derived topology/Y-bus
        network responsibility

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.

No Python 3.12-only syntax is used.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.model import Bus, BusType
from core.model.line import Line
from core.model.transformer import Transformer

from ..context import ApplicationContext
from ..errors import (
    DomainError,
    ExecutionError,
    ResourceError,
    ValidationError,
)
from ..results import ApplicationResult


class ModelService:
    """
    Headless Application service for canonical Core model
    creation and removal.

    Parameters
    ----------
    context:
        ApplicationContext containing the canonical Core Network.

    Notes
    -----
    The service does not own the Network.

    The Network is supplied by ApplicationContext and remains
    owned by the Core/Application composition boundary.
    """

    # ================================================================
    # INITIALIZATION
    # ================================================================

    def __init__(
        self,
        context: ApplicationContext,
    ) -> None:
        """
        Initialize the ModelService.
        """

        if context is None:
            raise ValueError(
                "ModelService context must not be None."
            )

        self._context = context

    # ================================================================
    # CONTEXT
    # ================================================================

    @property
    def context(self) -> ApplicationContext:
        """
        Return the Application dependency context.
        """

        return self._context

    # ================================================================
    # BUS CREATION
    # ================================================================

    def create_bus(
        self,
        *,
        bus_id: str,
        name: str = "",
        bus_type: BusType = BusType.PQ,
        voltage: float = 1.0,
        angle: float = 0.0,
        p_spec: float = 0.0,
        q_spec: float = 0.0,
        v_setpoint: float | None = None,
        q_min: float = float("-inf"),
        q_max: float = float("inf"),
    ) -> ApplicationResult[Bus]:
        """
        Create and register a canonical Core Bus.
        """

        self._validate_bus_input(
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

        try:
            bus = Bus(
                id=bus_id,
                name=name,
                type=bus_type,
                V=voltage,
                theta=angle,
                P_spec=p_spec,
                Q_spec=q_spec,
                V_setpoint=v_setpoint,
                Q_min=q_min,
                Q_max=q_max,
            )

        except Exception as exc:
            raise ExecutionError(
                code="BUS_CREATION_FAILED",
                message=(
                    f"Failed to construct Core Bus '{bus_id}'."
                ),
                details={
                    "bus_id": bus_id,
                    "operation": "create_bus",
                },
                cause=exc,
            ) from exc

        try:
            self._context.network.add_bus(bus)

        except ValueError as exc:
            raise DomainError(
                code="BUS_REGISTRATION_FAILED",
                message=(
                    f"Failed to register Bus '{bus_id}' "
                    "with the Core Network."
                ),
                details={
                    "bus_id": bus_id,
                    "operation": "register_bus",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="BUS_REGISTRATION_EXECUTION_FAILED",
                message=(
                    f"Unexpected failure while registering "
                    f"Bus '{bus_id}'."
                ),
                details={
                    "bus_id": bus_id,
                    "operation": "register_bus",
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success(
            value=bus,
            message=(
                f"Bus '{bus_id}' created successfully."
            ),
            metadata={
                "operation": "create_bus",
                "element_id": bus_id,
                "element_type": "bus",
            },
        )

    # ================================================================
    # BUS DELETION
    # ================================================================

    def delete_bus(
        self,
        *,
        bus_id: str,
    ) -> ApplicationResult[Bus]:
        """
        Remove a canonical Core Bus from the Network.
        """

        if not isinstance(bus_id, str) or not bus_id.strip():
            raise ValidationError(
                code="INVALID_BUS_ID",
                message=(
                    "Bus id must be a non-empty string."
                ),
                details={
                    "field": "bus_id",
                },
            )

        bus_id = bus_id.strip()

        network = self._context.network

        bus = None

        for candidate in network.buses:
            if getattr(candidate, "id", None) == bus_id:
                bus = candidate
                break

        if bus is None:
            raise ResourceError(
                code="BUS_NOT_FOUND",
                message=(
                    f"Bus '{bus_id}' is not registered "
                    "on the Core Network."
                ),
                details={
                    "bus_id": bus_id,
                    "operation": "delete_bus",
                },
            )

        try:
            network.remove_bus(bus)

        except ValueError as exc:
            raise DomainError(
                code="BUS_DELETION_REJECTED",
                message=(
                    f"Bus '{bus_id}' could not be removed."
                ),
                details={
                    "bus_id": bus_id,
                    "operation": "delete_bus",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="BUS_DELETION_FAILED",
                message=(
                    f"Unexpected failure while deleting "
                    f"Bus '{bus_id}'."
                ),
                details={
                    "bus_id": bus_id,
                    "operation": "delete_bus",
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success(
            value=bus,
            message=(
                f"Bus '{bus_id}' deleted successfully."
            ),
            metadata={
                "operation": "delete_bus",
                "element_id": bus_id,
                "element_type": "bus",
            },
        )

    # ================================================================
    # LINE CREATION
    # ================================================================

    def create_line(
        self,
        *,
        line_id: str,
        endpoint_from: Any,
        endpoint_to: Any,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
    ) -> ApplicationResult[Line]:
        """
        Create and register a canonical Core Line.

        Parameters
        ----------
        line_id:
            Persistent GridForge Line identifier.

        endpoint_from:
            Initial from-side physical endpoint.

        endpoint_to:
            Initial to-side physical endpoint.

        r:
            Series resistance in per-unit.

        x:
            Series reactance in per-unit.

        b:
            Total line shunt susceptance in per-unit.

        name:
            Human-readable engineering name.

        rate_mva:
            Thermal/equipment rating in MVA.

        Returns
        -------
        ApplicationResult[Line]
            Result containing the canonical Line.

        Notes
        -----
        The Line constructor owns creation of the Line's physical
        terminals.

        The Application service therefore does NOT call:

            line.connect_from(...)
            line.connect_to(...)

        after construction.
        """

        self._validate_line_input(
            line_id=line_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
        )

        try:
            line = Line(
                id=line_id,
                endpoint_from=endpoint_from,
                endpoint_to=endpoint_to,
                r=r,
                x=x,
                b=b,
                name=name,
                rate_mva=rate_mva,
            )

        except ValueError as exc:
            raise DomainError(
                code="LINE_CREATION_REJECTED",
                message=(
                    f"Line '{line_id}' could not be created."
                ),
                details={
                    "line_id": line_id,
                    "operation": "create_line",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="LINE_CREATION_FAILED",
                message=(
                    f"Unexpected failure while constructing "
                    f"Line '{line_id}'."
                ),
                details={
                    "line_id": line_id,
                    "operation": "create_line",
                },
                cause=exc,
            ) from exc

        try:
            self._context.network.add_line(line)

        except ValueError as exc:
            raise DomainError(
                code="LINE_REGISTRATION_FAILED",
                message=(
                    f"Failed to register Line '{line_id}' "
                    "with the Core Network."
                ),
                details={
                    "line_id": line_id,
                    "operation": "register_line",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="LINE_REGISTRATION_EXECUTION_FAILED",
                message=(
                    f"Unexpected failure while registering "
                    f"Line '{line_id}'."
                ),
                details={
                    "line_id": line_id,
                    "operation": "register_line",
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success(
            value=line,
            message=(
                f"Line '{line_id}' created successfully."
            ),
            metadata={
                "operation": "create_line",
                "element_id": line_id,
                "element_type": "line",
            },
        )

    # ================================================================
    # LINE DELETION
    # ================================================================

    def delete_line(
        self,
        *,
        line_id: str,
    ) -> ApplicationResult[Line]:
        """
        Remove a canonical Core Line from the Network.

        Network.remove_line() owns actual Network membership
        mutation and derived-state invalidation.

        This service does not disconnect Line terminals.
        """

        if not isinstance(line_id, str) or not line_id.strip():
            raise ValidationError(
                code="INVALID_LINE_ID",
                message=(
                    "Line id must be a non-empty string."
                ),
                details={
                    "field": "line_id",
                },
            )

        line_id = line_id.strip()

        network = self._context.network

        line = None

        for candidate in network.lines:
            if getattr(candidate, "id", None) == line_id:
                line = candidate
                break

        if line is None:
            raise ResourceError(
                code="LINE_NOT_FOUND",
                message=(
                    f"Line '{line_id}' is not registered "
                    "on the Core Network."
                ),
                details={
                    "line_id": line_id,
                    "operation": "delete_line",
                },
            )

        try:
            network.remove_line(line)

        except ValueError as exc:
            raise DomainError(
                code="LINE_DELETION_REJECTED",
                message=(
                    f"Line '{line_id}' could not be removed."
                ),
                details={
                    "line_id": line_id,
                    "operation": "delete_line",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="LINE_DELETION_FAILED",
                message=(
                    f"Unexpected failure while deleting "
                    f"Line '{line_id}'."
                ),
                details={
                    "line_id": line_id,
                    "operation": "delete_line",
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success(
            value=line,
            message=(
                f"Line '{line_id}' deleted successfully."
            ),
            metadata={
                "operation": "delete_line",
                "element_id": line_id,
                "element_type": "line",
            },
        )

    # ================================================================
    # TRANSFORMER CREATION
    # ================================================================

    def create_transformer(
        self,
        *,
        transformer_id: str,
        endpoint_from: Any,
        endpoint_to: Any,
        r: float,
        x: float,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
    ) -> ApplicationResult[Transformer]:
        """
        Create and register a canonical Core Transformer.

        Parameters
        ----------
        transformer_id:
            Persistent GridForge Transformer identifier.

        endpoint_from:
            Initial high-side/from-side physical endpoint.

        endpoint_to:
            Initial low-side/to-side physical endpoint.

        r:
            Series resistance in per-unit.

        x:
            Series reactance in per-unit.

        tap:
            Off-nominal transformer tap ratio.

        shift:
            Phase-shift angle in degrees.

        name:
            Human-readable engineering name.

        rate_mva:
            Transformer MVA rating.

        Returns
        -------
        ApplicationResult[Transformer]
            Result containing the canonical Transformer.

        Notes
        -----
        Transformer owns its physical terminal objects.

        The service therefore does not subsequently manipulate
        Transformer terminals.

        Network ownership is established exclusively through:

            network.add_transformer(transformer)
        """

        self._validate_transformer_input(
            transformer_id=transformer_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            tap=tap,
            shift=shift,
            name=name,
            rate_mva=rate_mva,
        )

        try:
            transformer = Transformer(
                id=transformer_id,
                endpoint_from=endpoint_from,
                endpoint_to=endpoint_to,
                r=r,
                x=x,
                tap=tap,
                shift=shift,
                name=name,
                rate_mva=rate_mva,
            )

        except ValueError as exc:
            raise DomainError(
                code="TRANSFORMER_CREATION_REJECTED",
                message=(
                    f"Transformer '{transformer_id}' "
                    "could not be created."
                ),
                details={
                    "transformer_id": transformer_id,
                    "operation": "create_transformer",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="TRANSFORMER_CREATION_FAILED",
                message=(
                    f"Unexpected failure while constructing "
                    f"Transformer '{transformer_id}'."
                ),
                details={
                    "transformer_id": transformer_id,
                    "operation": "create_transformer",
                },
                cause=exc,
            ) from exc

        try:
            self._context.network.add_transformer(
                transformer
            )

        except ValueError as exc:
            raise DomainError(
                code="TRANSFORMER_REGISTRATION_FAILED",
                message=(
                    f"Failed to register Transformer "
                    f"'{transformer_id}' with the Core Network."
                ),
                details={
                    "transformer_id": transformer_id,
                    "operation": "register_transformer",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="TRANSFORMER_REGISTRATION_EXECUTION_FAILED",
                message=(
                    f"Unexpected failure while registering "
                    f"Transformer '{transformer_id}'."
                ),
                details={
                    "transformer_id": transformer_id,
                    "operation": "register_transformer",
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success(
            value=transformer,
            message=(
                f"Transformer '{transformer_id}' "
                "created successfully."
            ),
            metadata={
                "operation": "create_transformer",
                "element_id": transformer_id,
                "element_type": "transformer",
            },
        )

    # ================================================================
    # TRANSFORMER DELETION
    # ================================================================

    def delete_transformer(
        self,
        *,
        transformer_id: str,
    ) -> ApplicationResult[Transformer]:
        """
        Remove a canonical Core Transformer from the Network.

        The service resolves the canonical registered Transformer
        and delegates Network membership removal to:

            Network.remove_transformer()

        The Transformer terminals are not disconnected here.
        """

        if (
            not isinstance(
                transformer_id,
                str,
            )
            or not transformer_id.strip()
        ):
            raise ValidationError(
                code="INVALID_TRANSFORMER_ID",
                message=(
                    "Transformer id must be a non-empty string."
                ),
                details={
                    "field": "transformer_id",
                },
            )

        transformer_id = transformer_id.strip()

        network = self._context.network

        transformer = None

        for candidate in network.transformers:
            if (
                getattr(candidate, "id", None)
                == transformer_id
            ):
                transformer = candidate
                break

        if transformer is None:
            raise ResourceError(
                code="TRANSFORMER_NOT_FOUND",
                message=(
                    f"Transformer '{transformer_id}' "
                    "is not registered on the Core Network."
                ),
                details={
                    "transformer_id": transformer_id,
                    "operation": "delete_transformer",
                },
            )

        try:
            network.remove_transformer(
                transformer
            )

        except ValueError as exc:
            raise DomainError(
                code="TRANSFORMER_DELETION_REJECTED",
                message=(
                    f"Transformer '{transformer_id}' "
                    "could not be removed."
                ),
                details={
                    "transformer_id": transformer_id,
                    "operation": "delete_transformer",
                    "reason": str(exc),
                },
            ) from exc

        except Exception as exc:
            raise ExecutionError(
                code="TRANSFORMER_DELETION_FAILED",
                message=(
                    f"Unexpected failure while deleting "
                    f"Transformer '{transformer_id}'."
                ),
                details={
                    "transformer_id": transformer_id,
                    "operation": "delete_transformer",
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success(
            value=transformer,
            message=(
                f"Transformer '{transformer_id}' "
                "deleted successfully."
            ),
            metadata={
                "operation": "delete_transformer",
                "element_id": transformer_id,
                "element_type": "transformer",
            },
        )

    # ================================================================
    # BUS INPUT VALIDATION
    # ================================================================

    @staticmethod
    def _validate_bus_input(
        *,
        bus_id: str,
        name: str,
        bus_type: BusType,
        voltage: float,
        angle: float,
        p_spec: float,
        q_spec: float,
        v_setpoint: float | None,
        q_min: float,
        q_max: float,
    ) -> None:
        """
        Validate Application-level Bus input.

        Engineering/domain validation remains owned by the
        canonical Core model.
        """

        if not isinstance(
            bus_id,
            str,
        ) or not bus_id.strip():
            raise ValidationError(
                code="INVALID_BUS_ID",
                message=(
                    "Bus id must be a non-empty string."
                ),
                details={
                    "field": "bus_id",
                },
            )

        if not isinstance(name, str):
            raise ValidationError(
                code="INVALID_BUS_NAME",
                message=(
                    "Bus name must be a string."
                ),
                details={
                    "field": "name",
                },
            )

        if not isinstance(bus_type, BusType):
            raise ValidationError(
                code="INVALID_BUS_TYPE",
                message=(
                    "bus_type must be a BusType."
                ),
                details={
                    "field": "bus_type",
                },
            )

        numeric_fields: Mapping[str, Any] = {
            "voltage": voltage,
            "angle": angle,
            "p_spec": p_spec,
            "q_spec": q_spec,
            "q_min": q_min,
            "q_max": q_max,
        }

        for field_name, value in numeric_fields.items():
            if not isinstance(
                value,
                (int, float),
            ):
                raise ValidationError(
                    code="INVALID_BUS_PARAMETER",
                    message=(
                        f"Bus parameter '{field_name}' "
                        "must be numeric."
                    ),
                    details={
                        "field": field_name,
                    },
                )

        if (
            v_setpoint is not None
            and not isinstance(
                v_setpoint,
                (int, float),
            )
        ):
            raise ValidationError(
                code="INVALID_BUS_SETPOINT",
                message=(
                    "v_setpoint must be numeric or None."
                ),
                details={
                    "field": "v_setpoint",
                },
            )

        if q_min > q_max:
            raise ValidationError(
                code="INVALID_REACTIVE_LIMITS",
                message=(
                    "q_min must not be greater than q_max."
                ),
                details={
                    "q_min": q_min,
                    "q_max": q_max,
                },
            )

    # ================================================================
    # LINE INPUT VALIDATION
    # ================================================================

    @staticmethod
    def _validate_line_input(
        *,
        line_id: str,
        endpoint_from: Any,
        endpoint_to: Any,
        r: float,
        x: float,
        b: float,
        name: str,
        rate_mva: float,
    ) -> None:
        """
        Validate Application-level Line request integrity.

        Detailed engineering validation remains owned by the
        canonical Line model.
        """

        if not isinstance(
            line_id,
            str,
        ) or not line_id.strip():
            raise ValidationError(
                code="INVALID_LINE_ID",
                message=(
                    "Line id must be a non-empty string."
                ),
                details={
                    "field": "line_id",
                },
            )

        if endpoint_from is None:
            raise ValidationError(
                code="INVALID_LINE_FROM_ENDPOINT",
                message=(
                    "Line from endpoint must not be None."
                ),
                details={
                    "field": "endpoint_from",
                },
            )

        if endpoint_to is None:
            raise ValidationError(
                code="INVALID_LINE_TO_ENDPOINT",
                message=(
                    "Line to endpoint must not be None."
                ),
                details={
                    "field": "endpoint_to",
                },
            )

        if endpoint_from is endpoint_to:
            raise ValidationError(
                code="INVALID_LINE_ENDPOINTS",
                message=(
                    "Line from and to endpoints must be distinct."
                ),
                details={
                    "field": "endpoint_from/endpoint_to",
                },
            )

        if not isinstance(r, (int, float)):
            raise ValidationError(
                code="INVALID_LINE_RESISTANCE",
                message=(
                    "Line resistance r must be numeric."
                ),
                details={
                    "field": "r",
                },
            )

        if not isinstance(x, (int, float)):
            raise ValidationError(
                code="INVALID_LINE_REACTANCE",
                message=(
                    "Line reactance x must be numeric."
                ),
                details={
                    "field": "x",
                },
            )

        if not isinstance(b, (int, float)):
            raise ValidationError(
                code="INVALID_LINE_SUSCEPTANCE",
                message=(
                    "Line shunt susceptance b must be numeric."
                ),
                details={
                    "field": "b",
                },
            )

        if not isinstance(name, str):
            raise ValidationError(
                code="INVALID_LINE_NAME",
                message=(
                    "Line name must be a string."
                ),
                details={
                    "field": "name",
                },
            )

        if not isinstance(
            rate_mva,
            (int, float),
        ):
            raise ValidationError(
                code="INVALID_LINE_RATING",
                message=(
                    "Line rate_mva must be numeric."
                ),
                details={
                    "field": "rate_mva",
                },
            )

    # ================================================================
    # TRANSFORMER INPUT VALIDATION
    # ================================================================

    @staticmethod
    def _validate_transformer_input(
        *,
        transformer_id: str,
        endpoint_from: Any,
        endpoint_to: Any,
        r: float,
        x: float,
        tap: float,
        shift: float,
        name: str,
        rate_mva: float,
    ) -> None:
        """
        Validate Application-level Transformer request integrity.

        Detailed engineering/domain validation remains owned by
        the canonical Transformer model.
        """

        if not isinstance(
            transformer_id,
            str,
        ) or not transformer_id.strip():
            raise ValidationError(
                code="INVALID_TRANSFORMER_ID",
                message=(
                    "Transformer id must be a non-empty string."
                ),
                details={
                    "field": "transformer_id",
                },
            )

        if endpoint_from is None:
            raise ValidationError(
                code="INVALID_TRANSFORMER_FROM_ENDPOINT",
                message=(
                    "Transformer from endpoint must not be None."
                ),
                details={
                    "field": "endpoint_from",
                },
            )

        if endpoint_to is None:
            raise ValidationError(
                code="INVALID_TRANSFORMER_TO_ENDPOINT",
                message=(
                    "Transformer to endpoint must not be None."
                ),
                details={
                    "field": "endpoint_to",
                },
            )

        if endpoint_from is endpoint_to:
            raise ValidationError(
                code="INVALID_TRANSFORMER_ENDPOINTS",
                message=(
                    "Transformer from and to endpoints "
                    "must be distinct."
                ),
                details={
                    "field": "endpoint_from/endpoint_to",
                },
            )

        numeric_fields: Mapping[str, Any] = {
            "r": r,
            "x": x,
            "tap": tap,
            "shift": shift,
            "rate_mva": rate_mva,
        }

        for field_name, value in numeric_fields.items():
            if not isinstance(
                value,
                (int, float),
            ):
                raise ValidationError(
                    code="INVALID_TRANSFORMER_PARAMETER",
                    message=(
                        f"Transformer parameter "
                        f"'{field_name}' must be numeric."
                    ),
                    details={
                        "field": field_name,
                    },
                )

        if not isinstance(name, str):
            raise ValidationError(
                code="INVALID_TRANSFORMER_NAME",
                message=(
                    "Transformer name must be a string."
                ),
                details={
                    "field": "name",
                },
            )


__all__ = [
    "ModelService",
]
