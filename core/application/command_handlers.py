# ============================================================
# File: core/application/command_handlers.py
# GridForge V2 — Application Command Handlers
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Application command handlers.

Handlers are the translation boundary between immutable
Application Commands and Application Services.

Handlers:

    * read Command payloads;
    * validate required payload fields;
    * invoke Application Services;
    * return ApplicationResult.

Handlers do NOT:

    * mutate Core directly;
    * contain electrical topology logic;
    * perform engineering calculations;
    * manipulate SLD/UI objects;
    * access Qt;
    * maintain application state.

Domain meaning belongs to Application Services/Core.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .errors import ValidationError
from .results import ApplicationResult
from .transaction import Transaction


# ============================================================
# TYPE DEFINITIONS
# ============================================================

ServiceResolver = Callable[
    [str],
    Any,
]


# ============================================================
# PAYLOAD HELPERS
# ============================================================

def _require_payload(
    command: Command,
    key: str,
) -> Any:
    """
    Return a required command payload value.

    Raises ValidationError when the field is absent.
    """

    if key not in command.payload:
        raise ValidationError(
            code="MISSING_COMMAND_PAYLOAD",
            message=(
                f"Command '{command.command_type}' "
                f"is missing required payload field "
                f"'{key}'."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
                "field": key,
            },
        )

    value = command.payload[key]

    if value is None:
        raise ValidationError(
            code="NULL_COMMAND_PAYLOAD",
            message=(
                f"Command '{command.command_type}' "
                f"contains null value for required "
                f"payload field '{key}'."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
                "field": key,
            },
        )

    return value


def _optional_payload(
    command: Command,
    key: str,
    default: Any = None,
) -> Any:
    """
    Return an optional payload value.
    """

    return command.payload.get(
        key,
        default,
    )


# ============================================================
# MODEL COMMAND HANDLER FACTORY
# ============================================================

class ModelCommandHandlers:
    """
    Factory/registry for Core model command handlers.

    The object receives Application Services and exposes pure
    Application-layer handlers to CommandManager.
    """

    def __init__(
        self,
        model_service: Any,
    ) -> None:
        if model_service is None:
            raise ValueError(
                "model_service is required."
            )

        self._model_service = model_service

    # ========================================================
    # REGISTRATION
    # ========================================================

    def handlers(
        self,
    ) -> Mapping[str, Callable]:
        """
        Return command-type → handler mapping.
        """

        return {
            "model.create": self.create_model,
            "model.update": self.update_model,
            "model.delete": self.delete_model,

            "network.connect": self.connect,
            "network.disconnect": self.disconnect,

            "network.create_connection": (
                self.create_connection
            ),
            "network.delete_connection": (
                self.delete_connection
            ),
        }

    # ========================================================
    # MODEL
    # ========================================================

    def create_model(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Create a Core model object through ModelService.
        """

        model_type = _require_payload(
            command,
            "model_type",
        )

        properties = _optional_payload(
            command,
            "properties",
            {},
        )

        return self._model_service.create_model(
            model_type=model_type,
            properties=properties,
            transaction=transaction,
        )

    def update_model(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Update a Core model object through ModelService.
        """

        model_id = _require_payload(
            command,
            "model_id",
        )

        changes = _require_payload(
            command,
            "changes",
        )

        return self._model_service.update_model(
            model_id=model_id,
            changes=changes,
            transaction=transaction,
        )

    def delete_model(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Delete a Core model object through ModelService.
        """

        model_id = _require_payload(
            command,
            "model_id",
        )

        return self._model_service.delete_model(
            model_id=model_id,
            transaction=transaction,
        )

    # ========================================================
    # CONNECTION
    # ========================================================

    def connect(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Create an electrical connection.

        Canonical payload:

            endpoint_from_id
            endpoint_to_id
        """

        endpoint_from_id = _require_payload(
            command,
            "endpoint_from_id",
        )

        endpoint_to_id = _require_payload(
            command,
            "endpoint_to_id",
        )

        return self._model_service.connect(
            endpoint_from_id=endpoint_from_id,
            endpoint_to_id=endpoint_to_id,
            transaction=transaction,
        )

    def disconnect(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Remove an electrical connection.

        Canonical payload:

            endpoint_from_id
            endpoint_to_id
        """

        endpoint_from_id = _require_payload(
            command,
            "endpoint_from_id",
        )

        endpoint_to_id = _require_payload(
            command,
            "endpoint_to_id",
        )

        return self._model_service.disconnect(
            endpoint_from_id=endpoint_from_id,
            endpoint_to_id=endpoint_to_id,
            transaction=transaction,
        )

    # ========================================================
    # EXPLICIT CONNECTION COMMANDS
    # ========================================================

    def create_connection(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Create a network connection.

        This delegates completely to ModelService.
        """

        endpoint_from_id = _require_payload(
            command,
            "endpoint_from_id",
        )

        endpoint_to_id = _require_payload(
            command,
            "endpoint_to_id",
        )

        connection_type = _optional_payload(
            command,
            "connection_type",
        )

        return self._model_service.create_connection(
            endpoint_from_id=endpoint_from_id,
            endpoint_to_id=endpoint_to_id,
            connection_type=connection_type,
            transaction=transaction,
        )

    def delete_connection(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        """
        Delete a network connection.
        """

        connection_id = _require_payload(
            command,
            "connection_id",
        )

        return self._model_service.delete_connection(
            connection_id=connection_id,
            transaction=transaction,
        )


# ============================================================
# FUNCTIONAL REGISTRATION API
# ============================================================

def build_model_command_handlers(
    model_service: Any,
) -> Mapping[str, Callable]:
    """
    Build the standard model command handler registry.
    """

    factory = ModelCommandHandlers(
        model_service
    )

    return factory.handlers()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ModelCommandHandlers",
    "build_model_command_handlers",
]
