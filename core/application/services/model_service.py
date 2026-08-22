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

For example:

    bus = Bus(...)
    network.add_bus(bus)

Removal follows the same ownership boundary:

    network.remove_bus(bus)

The service MUST NOT replace this with:

    network.buses.append(bus)

or:

    network.buses.remove(bus)

or:

    network.bus_index[...]

or:

    network._invalidate_topology()

The public Network API is the Application/Core mutation boundary.

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

The Application service therefore does not duplicate any of these
operations.

Current Scope
-------------
Current concrete operations:

    * Bus creation.
    * Bus deletion.

Additional equipment operations will be added only after their
actual Core constructors, ownership rules, and Network APIs have
been reconciled against the repository.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.

No Python 3.12-only syntax is used.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.model import Bus, BusType

from ..context import ApplicationContext
from ..errors import (
    DomainError,
    ExecutionError,
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

        Parameters
        ----------
        bus_id:
            Persistent identifier of the new bus.

        name:
            Human-readable engineering name.

        bus_type:
            Canonical Core BusType.

        voltage:
            Initial per-unit voltage magnitude.

        angle:
            Initial voltage angle.

        p_spec:
            Specified active power.

        q_spec:
            Specified reactive power.

        v_setpoint:
            Optional voltage setpoint.

        q_min:
            Minimum reactive-power limit.

        q_max:
            Maximum reactive-power limit.

        Returns
        -------
        ApplicationResult[Bus]
            Result containing the newly created canonical Bus.

        Raises
        ------
        ValidationError
            If Application-level input is invalid.

        DomainError
            If the Core rejects the requested operation.

        ExecutionError
            If an unexpected failure occurs while constructing
            or registering the Bus.
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

        # ------------------------------------------------------------
        # CONSTRUCT CANONICAL CORE MODEL
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # REGISTER THROUGH PUBLIC NETWORK API
        # ------------------------------------------------------------

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

        Parameters
        ----------
        bus_id:
            Stable identifier of the registered Bus.

        Returns
        -------
        ApplicationResult[Bus]
            Result containing the removed canonical Bus.

        Raises
        ------
        ValidationError
            If bus_id is invalid.

        DomainError
            If the Bus does not exist or Core Network rules reject
            its removal.

        ExecutionError
            If an unexpected failure occurs during deletion.

        Notes
        -----
        The service does not manipulate Network collections.

        It resolves the canonical Bus and delegates removal to:

            Network.remove_bus(bus)
        """

        # ------------------------------------------------------------
        # APPLICATION INPUT VALIDATION
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # RESOLVE CANONICAL BUS
        # ------------------------------------------------------------

        bus = None

        for candidate in network.buses:

            if getattr(candidate, "id", None) == bus_id:
                bus = candidate
                break

        if bus is None:
            raise DomainError(
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

        # ------------------------------------------------------------
        # DELEGATE ACTUAL CORE MUTATION
        # ------------------------------------------------------------

        try:
            network.remove_bus(bus)

        except ValueError as exc:
            # Network.remove_bus() uses ValueError for expected
            # Core-level rejection such as:
            #
            #   * unregistered Bus;
            #   * connected Line;
            #   * connected Transformer;
            #   * connected Generator;
            #   * connected Load;
            #   * connected Shunt.
            #
            # Translate that expected Core rejection into the
            # Application error taxonomy.

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

        # ------------------------------------------------------------
        # RETURN THE SAME CANONICAL OBJECT
        # ------------------------------------------------------------

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

        This validation is intentionally limited to request
        integrity.

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

        if not isinstance(
            name,
            str,
        ):
            raise ValidationError(
                code="INVALID_BUS_NAME",
                message=(
                    "Bus name must be a string."
                ),
                details={
                    "field": "name",
                },
            )

        if not isinstance(
            bus_type,
            BusType,
        ):
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


__all__ = [
    "ModelService",
]
