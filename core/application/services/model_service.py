# ============================================================
# File: core/application/services/model_service.py
# GridForge V2 — Model Application Service
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Model Application Service
=========================================

Application service responsible for model-level mutations.

Responsibilities
----------------

    * validate Application-level model input;
    * construct Core model objects;
    * delegate registration/removal to the canonical Core
      Network API;
    * register inverse operations with the active transaction;
    * return ApplicationResult for successful operations.

This service does NOT:

    * know about Qt;
    * know about SLD/canvas state;
    * manipulate UI state;
    * perform power-system calculations;
    * mutate Network private collections;
    * maintain a second model registry;
    * resolve EndpointReference values.

Endpoint resolution is performed by command handlers before
the service is called.

Architectural flow
------------------

    Application Command
            |
            v
    Command Handler
            |
            | EndpointReference resolution
            v
    ModelService
            |
            v
    Core Network public API
            |
            v
    Core Model
"""

from __future__ import annotations

from typing import Any

from ..errors import (
    DomainError,
    ExecutionError,
    ResourceError,
    ValidationError,
)
from ..results import ApplicationResult


# Core model imports.
#
# These imports intentionally refer to the domain model rather
# than UI or plugin implementations.
from core.model.bus import Bus
from core.model.line import Line
from core.model.transformer import Transformer
from core.model.terminal import Terminal


class ModelService:
    """
    Application service for Core model mutations.

    Parameters
    ----------
    network:
        Canonical Core Network instance.

    The service owns no model state of its own.
    """

    def __init__(
        self,
        network: Any,
    ) -> None:
        if network is None:
            raise ValueError(
                "network is required."
            )

        self._network = network

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _validate_id(
        value: str,
        field_name: str,
    ) -> str:
        """
        Validate a model identifier.
        """

        if not isinstance(value, str):
            raise ValidationError(
                code="INVALID_IDENTIFIER",
                message=(
                    f"{field_name} must be a string."
                ),
                details={
                    "field": field_name,
                    "value_type": type(value).__name__,
                },
            )

        value = value.strip()

        if not value:
            raise ValidationError(
                code="EMPTY_IDENTIFIER",
                message=(
                    f"{field_name} must not be empty."
                ),
                details={
                    "field": field_name,
                },
            )

        return value

    @staticmethod
    def _validate_endpoint(
        endpoint: Any,
        field_name: str,
    ) -> None:
        """
        Validate a resolved Core electrical endpoint.

        Valid endpoint objects at this Application boundary are:

            Bus
            Terminal

        EndpointReference resolution itself belongs to the
        command-handler layer.
        """

        if not isinstance(
            endpoint,
            (Bus, Terminal),
        ):
            raise ValidationError(
                code="INVALID_ENDPOINT",
                message=(
                    f"{field_name} must resolve to a "
                    "Core Bus or Terminal."
                ),
                details={
                    "field": field_name,
                    "received_type": type(
                        endpoint
                    ).__name__,
                },
            )

    @staticmethod
    def _validate_distinct_endpoints(
        endpoint_from: Any,
        endpoint_to: Any,
    ) -> None:
        """
        Reject identical canonical endpoint objects.
        """

        if endpoint_from is endpoint_to:
            raise ValidationError(
                code="IDENTICAL_ENDPOINTS",
                message=(
                    "Source and destination endpoints "
                    "must be different."
                ),
                details={},
            )

    @staticmethod
    def _validate_numeric(
        value: Any,
        field_name: str,
    ) -> None:
        """
        Validate a numeric Application input.
        """

        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise ValidationError(
                code="INVALID_NUMERIC_VALUE",
                message=(
                    f"{field_name} must be numeric."
                ),
                details={
                    "field": field_name,
                    "value_type": type(value).__name__,
                },
            )

    @classmethod
    def _validate_line_input(
        cls,
        *,
        line_id: str,
        endpoint_from: Any,
        endpoint_to: Any,
        r: float,
        x: float,
        b: float,
        name: str,
        rate_mva: float | None,
    ) -> str:
        """
        Validate Line creation input.
        """

        line_id = cls._validate_id(
            line_id,
            "line_id",
        )

        cls._validate_endpoint(
            endpoint_from,
            "endpoint_from",
        )

        cls._validate_endpoint(
            endpoint_to,
            "endpoint_to",
        )

        cls._validate_distinct_endpoints(
            endpoint_from,
            endpoint_to,
        )

        cls._validate_numeric(r, "r")
        cls._validate_numeric(x, "x")
        cls._validate_numeric(b, "b")

        if rate_mva is not None:
            cls._validate_numeric(
                rate_mva,
                "rate_mva",
            )

        if not isinstance(name, str):
            raise ValidationError(
                code="INVALID_NAME",
                message="name must be a string.",
                details={
                    "field": "name",
                },
            )

        return line_id

    @classmethod
    def _validate_transformer_input(
        cls,
        *,
        transformer_id: str,
        endpoint_from: Any,
        endpoint_to: Any,
        r: float,
        x: float,
        tap: float,
        shift: float,
        name: str,
        rate_mva: float | None,
    ) -> str:
        """
        Validate Transformer creation input.
        """

        transformer_id = cls._validate_id(
            transformer_id,
            "transformer_id",
        )

        cls._validate_endpoint(
            endpoint_from,
            "endpoint_from",
        )

        cls._validate_endpoint(
            endpoint_to,
            "endpoint_to",
        )

        cls._validate_distinct_endpoints(
            endpoint_from,
            endpoint_to,
        )

        cls._validate_numeric(r, "r")
        cls._validate_numeric(x, "x")
        cls._validate_numeric(tap, "tap")
        cls._validate_numeric(shift, "shift")

        if rate_mva is not None:
            cls._validate_numeric(
                rate_mva,
                "rate_mva",
            )

        if not isinstance(name, str):
            raise ValidationError(
                code="INVALID_NAME",
                message="name must be a string.",
                details={
                    "field": "name",
                },
            )

        return transformer_id

    # ========================================================
    # BUS
    # ========================================================

    def create_bus(
        self,
        *,
        bus_id: str,
        name: str = "",
        bus_type: Any = None,
        voltage: float = 1.0,
        angle: float = 0.0,
        p_spec: float = 0.0,
        q_spec: float = 0.0,
        v_setpoint: float | None = None,
        q_min: float = float("-inf"),
        q_max: float = float("inf"),
        transaction: Any = None,
    ) -> ApplicationResult[Any]:
        """
        Create and register a Core Bus.
        """

        bus_id = self._validate_id(
            bus_id,
            "bus_id",
        )

        self._validate_numeric(
            voltage,
            "voltage",
        )
        self._validate_numeric(
            angle,
            "angle",
        )
        self._validate_numeric(
            p_spec,
            "p_spec",
        )
        self._validate_numeric(
            q_spec,
            "q_spec",
        )
        self._validate_numeric(
            q_min,
            "q_min",
        )
        self._validate_numeric(
            q_max,
            "q_max",
        )

        if v_setpoint is not None:
            self._validate_numeric(
                v_setpoint,
                "v_setpoint",
            )

        if not isinstance(name, str):
            raise ValidationError(
                code="INVALID_NAME",
                message="name must be a string.",
                details={
                    "field": "name",
                },
            )

        try:
            bus = Bus(
                id=bus_id,
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

        except ValidationError:
            raise

        except DomainError:
            raise

        except Exception as exc:
            raise ExecutionError(
                code="BUS_CREATION_FAILED",
                message=(
                    f"Failed to create Bus "
                    f"'{bus_id}'."
                ),
                details={
                    "bus_id": bus_id,
                },
                cause=exc,
            ) from exc

        if transaction is not None:
            transaction.add_undo(
                lambda: self.delete_bus(
                    bus_id=bus_id,
                    transaction=None,
                )
            )

        return ApplicationResult.success_result(
            value=bus,
            message=(
                f"Bus '{bus_id}' created successfully."
            ),
        )

    def delete_bus(
        self,
        *,
        bus_id: str,
        transaction: Any = None,
    ) -> ApplicationResult[Any]:
        """
        Remove a Core Bus through the canonical Network API.
        """

        bus_id = self._validate_id(
            bus_id,
            "bus_id",
        )

        buses = getattr(
            self._network,
            "buses",
            None,
        )

        if buses is None:
            raise ResourceError(
                code="BUS_COLLECTION_MISSING",
                message=(
                    "Canonical Network does not "
                    "expose its Bus collection."
                ),
                details={},
            )

        bus = None

        for candidate in buses:
            if getattr(candidate, "id", None) == bus_id:
                bus = candidate
                break

        if bus is None:
            raise ResourceError(
                code="BUS_NOT_FOUND",
                message=(
                    f"Bus '{bus_id}' was not found."
                ),
                details={
                    "bus_id": bus_id,
                },
            )

        try:
            self._network.remove_bus(
                bus_id
            )

        except Exception as exc:
            raise ExecutionError(
                code="BUS_DELETION_FAILED",
                message=(
                    f"Failed to delete Bus "
                    f"'{bus_id}'."
                ),
                details={
                    "bus_id": bus_id,
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success_result(
            value=bus,
            message=(
                f"Bus '{bus_id}' deleted successfully."
            ),
        )

    # ========================================================
    # LINE
    # ========================================================

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
        rate_mva: float | None = None,
        transaction: Any = None,
    ) -> ApplicationResult[Any]:
        """
        Create and register a Core Line.
        """

        line_id = self._validate_line_input(
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

            self._network.add_line(line)

        except ValidationError:
            raise

        except DomainError:
            raise

        except Exception as exc:
            raise ExecutionError(
                code="LINE_CREATION_FAILED",
                message=(
                    f"Failed to create Line "
                    f"'{line_id}'."
                ),
                details={
                    "line_id": line_id,
                },
                cause=exc,
            ) from exc

        if transaction is not None:
            transaction.add_undo(
                lambda: self.delete_line(
                    line_id=line_id,
                    transaction=None,
                )
            )

        return ApplicationResult.success_result(
            value=line,
            message=(
                f"Line '{line_id}' created successfully."
            ),
        )

    def delete_line(
        self,
        *,
        line_id: str,
        transaction: Any = None,
    ) -> ApplicationResult[Any]:
        """
        Remove a Core Line through the canonical Network API.
        """

        line_id = self._validate_id(
            line_id,
            "line_id",
        )

        lines = getattr(
            self._network,
            "lines",
            None,
        )

        if lines is None:
            raise ResourceError(
                code="LINE_COLLECTION_MISSING",
                message=(
                    "Canonical Network does not "
                    "expose its Line collection."
                ),
                details={},
            )

        line = None

        for candidate in lines:
            if getattr(candidate, "id", None) == line_id:
                line = candidate
                break

        if line is None:
            raise ResourceError(
                code="LINE_NOT_FOUND",
                message=(
                    f"Line '{line_id}' was not found."
                ),
                details={
                    "line_id": line_id,
                },
            )

        try:
            self._network.remove_line(
                line_id
            )

        except Exception as exc:
            raise ExecutionError(
                code="LINE_DELETION_FAILED",
                message=(
                    f"Failed to delete Line "
                    f"'{line_id}'."
                ),
                details={
                    "line_id": line_id,
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success_result(
            value=line,
            message=(
                f"Line '{line_id}' deleted successfully."
            ),
        )

    # ========================================================
    # TRANSFORMER
    # ========================================================

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
        rate_mva: float | None = None,
        transaction: Any = None,
    ) -> ApplicationResult[Any]:
        """
        Create and register a Core Transformer.
        """

        transformer_id = (
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

            self._network.add_transformer(
                transformer
            )

        except ValidationError:
            raise

        except DomainError:
            raise

        except Exception as exc:
            raise ExecutionError(
                code="TRANSFORMER_CREATION_FAILED",
                message=(
                    f"Failed to create Transformer "
                    f"'{transformer_id}'."
                ),
                details={
                    "transformer_id": transformer_id,
                },
                cause=exc,
            ) from exc

        if transaction is not None:
            transaction.add_undo(
                lambda: self.delete_transformer(
                    transformer_id=transformer_id,
                    transaction=None,
                )
            )

        return ApplicationResult.success_result(
            value=transformer,
            message=(
                "Transformer "
                f"'{transformer_id}' created successfully."
            ),
        )

    def delete_transformer(
        self,
        *,
        transformer_id: str,
        transaction: Any = None,
    ) -> ApplicationResult[Any]:
        """
        Remove a Core Transformer through the canonical
        Network API.
        """

        transformer_id = self._validate_id(
            transformer_id,
            "transformer_id",
        )

        transformers = getattr(
            self._network,
            "transformers",
            None,
        )

        if transformers is None:
            raise ResourceError(
                code="TRANSFORMER_COLLECTION_MISSING",
                message=(
                    "Canonical Network does not "
                    "expose its Transformer collection."
                ),
                details={},
            )

        transformer = None

        for candidate in transformers:
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
                    f"Transformer "
                    f"'{transformer_id}' was not found."
                ),
                details={
                    "transformer_id": transformer_id,
                },
            )

        try:
            self._network.remove_transformer(
                transformer_id
            )

        except Exception as exc:
            raise ExecutionError(
                code="TRANSFORMER_DELETION_FAILED",
                message=(
                    f"Failed to delete Transformer "
                    f"'{transformer_id}'."
                ),
                details={
                    "transformer_id": transformer_id,
                },
                cause=exc,
            ) from exc

        return ApplicationResult.success_result(
            value=transformer,
            message=(
                "Transformer "
                f"'{transformer_id}' deleted successfully."
            ),
        )


__all__ = [
    "ModelService",
]
