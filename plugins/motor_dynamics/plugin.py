"""GridForge V2 plugin lifecycle adapter for the motor-dynamics extension.

Author: Subhendu Mishra

The plugin follows the canonical PluginContext lifecycle. Motor topology
commands are deliberately not registered until a GridForge composition
adapter supplies the transactional motor services and command registration
boundary; Application does not expose a public register_command_handler API.
"""
from __future__ import annotations

from typing import Any

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
        """Initialize from the canonical immutable PluginContext."""
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
                "Motor dynamics cannot be activated: PluginContext.services must "
                "provide the explicit 'motor_dynamics_composition' adapter. The "
                "current Application has no public motor command-registration or "
                "motor topology service contract."
            )

        register = getattr(composition, "register_motor_extension", None)
        if not callable(register):
            raise TypeError(
                "motor_dynamics_composition must expose register_motor_extension(plugin)"
            )

        self.context = context
        self.application = application
        self.persistence = MotorPluginPersistenceHandler(application)

        # The adapter is the composition boundary and owns the concrete command
        # manager, topology service, graphics registration, and persistence hooks.
        token = register(self)
        if callable(token):
            self._unhooks.append(token)
        elif token is not None:
            unregister = getattr(composition, "unregister_motor_extension", None)
            if callable(unregister):
                self._unhooks.append(lambda t=token: unregister(t))

        event_bus = getattr(context, "event_bus", None) or getattr(application, "event_bus", None)
        parent = getattr(context, "parent", None) or getattr(context, "root_widget", None)
        if parent is not None and event_bus is not None:
            self.dashboard = MotorTelemetryDashboardWidget(
                self.read_models,
                event_bus=event_bus,
                parent=parent,
            )
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
