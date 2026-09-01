# ============================================================
# File: application/application_context.py
# GridForge V2 — Application Composition Context
# Author: Subhendu Mishra
# ============================================================
"""Composition root for application command and presentation boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from application.commands.add_network_element import AddNetworkElementHandler
from application.commands.command_dispatcher import CommandDispatcher
from application.commands.register_network_element import register_network_element_handler
from ui.events.application_update_bridge import ApplicationUpdateBridge
from ui.events.ui_update_bus import UIUpdateBus


@dataclass
class ApplicationContext:
    """Own application-scoped orchestration infrastructure."""

    command_dispatcher: CommandDispatcher
    ui_update_bus: UIUpdateBus
    update_bridge: ApplicationUpdateBridge
    add_network_element_handler: AddNetworkElementHandler

    @classmethod
    def create(cls, network: Any) -> "ApplicationContext":
        ui_update_bus = UIUpdateBus()
        update_bridge = ApplicationUpdateBridge(ui_update_bus)
        dispatcher = CommandDispatcher(on_complete=update_bridge.callback())
        handler = register_network_element_handler(dispatcher, network)
        return cls(
            command_dispatcher=dispatcher,
            ui_update_bus=ui_update_bus,
            update_bridge=update_bridge,
            add_network_element_handler=handler,
        )


__all__ = ["ApplicationContext"]
