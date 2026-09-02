# ============================================================
# File: core/application/application.py
# GridForge V2 — Headless Application Facade
# Author: Subhendu Mishra
# ============================================================

"""Stable public Application facade for commands, reads, and events."""

from __future__ import annotations

from .command import Command
from .command_manager import CommandManager
from .event_bus import ApplicationEventBus
from .events import NetworkChanged
from .read_models import ElementReadModel, NetworkReadModel
from .read_service import ReadService
from .results import ApplicationResult


class Application:
    """Public headless GridForge Application facade.

    Mutation remains exclusively command-driven. Optional read access exposes
    immutable Application snapshots and never returns Core model objects.
    Successful mutations publish a headless Application event after the
    command transaction has completed.
    """

    def __init__(
        self,
        command_manager: CommandManager,
        read_service: ReadService | None = None,
        event_bus: ApplicationEventBus | None = None,
    ) -> None:
        if not isinstance(command_manager, CommandManager):
            raise TypeError("Application command_manager must be a CommandManager.")
        if read_service is not None and not isinstance(read_service, ReadService):
            raise TypeError("Application read_service must implement ReadService.")
        if event_bus is not None and not isinstance(event_bus, ApplicationEventBus):
            raise TypeError("Application event_bus must be an ApplicationEventBus.")

        self._command_manager = command_manager
        self._read_service = read_service
        self._event_bus = event_bus if event_bus is not None else ApplicationEventBus()

    @property
    def event_bus(self) -> ApplicationEventBus:
        """Return the Application-owned headless event bus."""
        return self._event_bus

    def execute(self, command: Command) -> ApplicationResult:
        """Execute a command, then publish its committed network change."""
        if not isinstance(command, Command):
            raise TypeError("Application.execute requires a Command.")
        result = self._command_manager.execute(command)
        self._publish_network_changed(command, result)
        return result

    def supports(self, command_type: str) -> bool:
        """Return whether a command type is currently supported."""
        if not isinstance(command_type, str):
            return False
        return self._command_manager.is_registered(command_type)

    def command_types(self) -> tuple[str, ...]:
        """Return the immutable list of registered command types."""
        return self._command_manager.registered_commands

    def read_network(self) -> NetworkReadModel:
        """Return an immutable authoritative network snapshot for projections."""
        self._require_read_service()
        return self._read_service.network()  # type: ignore[union-attr]

    def read_element(
        self,
        element_type: str,
        object_id: str,
    ) -> ElementReadModel:
        """Return one immutable element snapshot for a projection."""
        self._require_read_service()
        return self._read_service.element(element_type, object_id)  # type: ignore[union-attr]

    def _publish_network_changed(
        self,
        command: Command,
        result: ApplicationResult,
    ) -> None:
        """Publish a read-side invalidation fact without exposing Core state."""
        self._event_bus.publish(
            NetworkChanged(
                operation=command.command_type,
                metadata={
                    "command_id": str(command.command_id),
                    "message": result.message,
                },
            )
        )

    def _require_read_service(self) -> None:
        if self._read_service is None:
            raise RuntimeError("Application read service is not configured.")


__all__ = ["Application"]
