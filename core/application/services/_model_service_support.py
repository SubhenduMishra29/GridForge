from __future__ import annotations

from typing import Any

from core.application.results import ApplicationResult
from core.application.transaction import Transaction
from core.errors import DomainError, ResourceError
from core.model.bus import Bus
from core.model.terminal import Terminal
from core.network.network import Network


class ModelServiceSupport:
    """Small stateless support boundary shared by model mutation services."""

    def _get_required(self, element_type: str, object_id: str, display_type: str) -> Any:
        try:
            value = self._network.get_by_id(element_type, object_id)
        except KeyError as exc:
            raise ResourceError(
                code=f"{element_type.upper()}_NOT_FOUND",
                message=f"{display_type} not found: {object_id}",
                details={"object_type": element_type, "object_id": object_id},
            ) from exc
        if value is None:
            raise ResourceError(
                code=f"{element_type.upper()}_NOT_FOUND",
                message=f"{display_type} not found: {object_id}",
                details={"object_type": element_type, "object_id": object_id},
            )
        return value

    def _ensure_not_exists(self, element_type: str, object_id: str, display_type: str) -> None:
        try:
            value = self._network.get_by_id(element_type, object_id)
        except KeyError:
            return
        if value is not None:
            raise DomainError(
                code=f"{element_type.upper()}_ALREADY_EXISTS",
                message=f"{display_type} already exists: {object_id}",
                details={"object_type": element_type, "object_id": object_id},
            )

    @staticmethod
    def _require_type(value: Any, expected_type: type, object_id: str, display_type: str) -> None:
        if not isinstance(value, expected_type):
            raise DomainError(
                code=f"INVALID_{display_type.upper()}_REFERENCE",
                message=f"Object {object_id!r} is not a {display_type}.",
                details={"object_id": object_id, "object_type": type(value).__name__},
            )

    @staticmethod
    def _validate_endpoint(endpoint: object, parameter_name: str) -> None:
        if not isinstance(endpoint, (Bus, Terminal)):
            raise DomainError(
                code="INVALID_ENDPOINT",
                message=f"{parameter_name} must be a Bus or Terminal.",
                details={"parameter": parameter_name, "object_type": type(endpoint).__name__},
            )

    @staticmethod
    def _require_distinct_endpoints(endpoint_from: object, endpoint_to: object, code: str, display_type: str, object_id: str) -> None:
        if endpoint_from is endpoint_to:
            raise DomainError(
                code=code,
                message=f"{display_type} endpoints must be different.",
                details={"object_id": object_id},
            )

    @staticmethod
    def _require_transaction(transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction.")
        if not transaction.active:
            raise RuntimeError("Transaction must be active.")

    @staticmethod
    def _require_id(value: str, parameter_name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{parameter_name} must be str.")
        if not value.strip():
            raise ValueError(f"{parameter_name} must not be empty.")

    @staticmethod
    def _success(value: Any, object_type: str, object_id: str, message: str) -> ApplicationResult:
        return ApplicationResult.success_result(
            value=value,
            message=message,
            metadata={"object_type": object_type, "object_id": object_id},
        )
