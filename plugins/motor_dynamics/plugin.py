"""GridForge V2 lifecycle adapter for the motor-dynamics extension.

Author: Subhendu Mishra

Host command registration and topology mutations are delegated to the explicit
motor_dynamics_composition service supplied through PluginContext.
"""
from __future__ import annotations

from typing import Any

from .commands import (
    ADD_DRAFT_MOTOR_PLACEMENT,
    CONNECT_MOTOR_TO_BUS,
    MotorPlacementCommandHandler,
)
from .dashboard import MotorTelemetryDashboardWidget
from .persistence import MotorPluginPersistenceHandler
from .read_models import MotorSimulationReadModelStore


class MotorDynamicsPlugin:
    @property
    def plugin_id(self) -> str:
        return "gridforge.plugin.motor_dynamics"

    def __init__(self) -> None:
        self.application: Any = None
        self.context: Any = None
        self.read_models = MotorSimulationReadModelStore()
        self.persistence: MotorPluginPersistenceHandler | None = None
        self.dashboard: MotorTelemetryDashboardWidget | None = None
        self._unhooks: list[Any] = []
        self._initialized = False

    def initialize(self, context: Any) -> None:
        """Initialize from GridForge's canonical PluginContext."""
        if self._initialized:
            return
        if context is None or not hasattr(context, "application"):
            raise TypeError("MotorDynamicsPlugin.initialize requires a GridForge PluginContext")

        application = context.application
        if application is None:
            raise RuntimeError("PluginContext.application is required")

        services = getattr(context, "services", {})
        composition = services.get("motor_dynamics_composition")
        if composition is None:
            raise RuntimeError(
                "Motor dynamics cannot be activated until PluginContext.services "
                "provides 'motor_dynamics_composition' with transactional motor "
                "services and command registration."
            )

        register = getattr(composition, "register_motor_extension", None)
        if not callable(register):
            raise TypeError(
                "motor_dynamics_composition must expose register_motor_extension"
            )

        # Keep command registration and domain service responsibilities distinct.
        # The composition adapter owns host wiring; motor_service owns operations.
        motor_service = getattr(composition, "motor_service", None)
        if motor_service is None:
            raise RuntimeError(
                "motor_dynamics_composition must expose a separate 'motor_service'; "
                "the registration adapter itself is not a domain service."
            )

        handler = MotorPlacementCommandHandler(motor_service)
        token = None
        dashboard = None
        persistence = None
        try:
            # Do not publish partially initialized state on the plugin instance.
            # If any subsequent setup fails, undo the registration.
            token = register(
                plugin=self,
                command_handlers={
                    ADD_DRAFT_MOTOR_PLACEMENT: handler,
                    CONNECT_MOTOR_TO_BUS: handler,
                },
            )
            if not callable(token):
                raise TypeError(
                    "register_motor_extension must return a callable teardown "
                    "for the registered motor command handlers."
                )

            persistence = MotorPluginPersistenceHandler(application)
            event_bus = getattr(context, "event_bus", None) or getattr(application, "event_bus", None)
            parent = getattr(context, "parent", None) or getattr(context, "root_widget", None)
            if parent is not None and event_bus is not None:
                dashboard = MotorTelemetryDashboardWidget(
                    self.read_models,
                    event_bus=event_bus,
                    parent=parent,
                )
        except BaseException:
            if dashboard is not None:
                try:
                    dashboard.close()
                except BaseException:
                    pass
            if callable(token):
                try:
                    token()
                except BaseException:
                    pass
            raise

        self.context = context
        self.application = application
        self.persistence = persistence
        self._unhooks.append(token)
        self.dashboard = dashboard
        self._initialized = True

    def shutdown(self) -> None:
        errors: list[BaseException] = []
        for unhook in reversed(self._unhooks):
            try:
                unhook()
            except BaseException as exc:
                errors.append(exc)
        self._unhooks.clear()

        if self.dashboard is not None:
            try:
                self.dashboard.close()
            except BaseException as exc:
                errors.append(exc)
            self.dashboard = None

        self._initialized = False
        self.persistence = None
        self.application = None
        self.context = None
        if errors:
            raise ExceptionGroup("Motor Dynamics plugin shutdown encountered failures", errors)


__all__ = ["MotorDynamicsPlugin"]
