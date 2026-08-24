# ============================================================
# File: core/application/commands/transformer_commands.py
# GridForge V2 — Transformer Commands
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2
============

Application commands for canonical Transformer model operations.

Architectural role
------------------
These classes represent immutable Application intent.

They do NOT:

    - mutate Core models;
    - mutate Network;
    - manipulate terminals;
    - manipulate topology;
    - build Y-bus;
    - access Qt;
    - access graphics objects;
    - execute Application services.

Execution is performed by CommandManager through registered
Application handlers.

Transformer endpoint policy
---------------------------
Transformer endpoints are represented by endpoint identifiers.

The command carries only Application-level values. It does not
contain Bus, Terminal, Transformer, or other Core model instances.

The corresponding Application handler is responsible for resolving
endpoint identifiers against the canonical Core/Network state before
invoking ModelService.

Python compatibility
---------------------
Python 3.10 / 3.11.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4

from ..command import Command


# =====================================================================
# COMMAND TYPES
# =====================================================================

CREATE_TRANSFORMER = "model.create_transformer"
DELETE_TRANSFORMER = "model.delete_transformer"


# =====================================================================
# PAYLOAD HELPER
# =====================================================================

def _payload(**values: Any) -> MappingProxyType:
    """
    Create an immutable Application command payload.

    Only transport-safe Application values are permitted.
    """

    return MappingProxyType(values)


# =====================================================================
# CREATE TRANSFORMER
# =====================================================================

class CreateTransformerCommand(Command):
    """
    Request creation of a canonical Core Transformer.

    Parameters
    ----------
    transformer_id:
        Stable identifier for the Transformer.

    endpoint_from_id:
        Identifier of the first canonical endpoint.

    endpoint_to_id:
        Identifier of the second canonical endpoint.

    r:
        Transformer series resistance.

    x:
        Transformer series reactance.

    b:
        Transformer shunt susceptance.

    tap:
        Transformer tap ratio.

    shift:
        Transformer phase-shift angle.

    name:
        Human-readable Transformer name.

    rate_mva:
        Transformer thermal rating.

    in_service:
        Whether the Transformer is initially in service.

    command_id:
        Unique command instance identifier.

    correlation_id:
        Optional workflow correlation identifier.

    causation_id:
        Optional identifier of the command/event that caused this
        command.

    Notes
    -----
    This command contains intent only.

    It does not construct a Transformer and does not mutate Core.
    """

    def __init__(
        self,
        *,
        transformer_id: str,
        endpoint_from_id: str,
        endpoint_to_id: str,
        r: float,
        x: float,
        b: float = 0.0,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:

        super().__init__(
            command_type=CREATE_TRANSFORMER,
            payload=_payload(
                transformer_id=transformer_id,
                endpoint_from_id=endpoint_from_id,
                endpoint_to_id=endpoint_to_id,
                r=r,
                x=x,
                b=b,
                tap=tap,
                shift=shift,
                name=name,
                rate_mva=rate_mva,
                in_service=in_service,
            ),
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# =====================================================================
# DELETE TRANSFORMER
# =====================================================================

class DeleteTransformerCommand(Command):
    """
    Request removal of a canonical Core Transformer.

    Parameters
    ----------
    transformer_id:
        Stable identifier of the Transformer to remove.

    Notes
    -----
    The command does not locate or remove the Transformer itself.

    Execution and Core mutation belong to the Application service
    and Core Network respectively.
    """

    def __init__(
        self,
        *,
        transformer_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:

        super().__init__(
            command_type=DELETE_TRANSFORMER,
            payload=_payload(
                transformer_id=transformer_id,
            ),
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "CREATE_TRANSFORMER",
    "DELETE_TRANSFORMER",
    "CreateTransformerCommand",
    "DeleteTransformerCommand",
]
