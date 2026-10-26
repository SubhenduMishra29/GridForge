"""GridForge plugin lifecycle adapter; integrations are capability-checked, not guessed."""
from __future__ import annotations
from typing import Any
from .commands import MotorPlacementCommandHandler
from .dashboard import MotorTelemetryDashboardWidget
from .persistence import MotorPluginPersistenceHandler
from .read_models import MotorSimulationReadModelStore

class MotorDynamicsPlugin:
    plugin_id = "gridforge.plugin.motor_dynamics"
    def __init__(self): self.application = None; self.read_models = MotorSimulationReadModelStore(); self._unhooks = []; self._registered = False
    def initialize(self, application: Any, ui_registry: Any = None) -> None:
        if self._registered: return
        self.application = application; self.command_handler = MotorPlacementCommandHandler(application); self.persistence = MotorPluginPersistenceHandler(application)
        # The host owns command registration and lifecycle/event buses; fail clearly if required capabilities are absent.
        register = getattr(application, "register_command_handler", None)
        if not callable(register): raise RuntimeError("GridForge Application must expose register_command_handler")
        for command_type, method in (( __import__(__package__ + ".commands", fromlist=["AddDraftMotorPlacementCommand"]).AddDraftMotorPlacementCommand, self.command_handler.execute), (__import__(__package__ + ".commands", fromlist=["CommitMotorToNetworkCommand"]).CommitMotorToNetworkCommand, self.command_handler.commit)):
            token = register(command_type, method); self._remember_unhook(token, application)
        factory_registry = getattr(ui_registry, "register_graphics_factory", None)
        if callable(factory_registry):
            from .graphics import SLDMotorGraphicsItem
            self._remember_unhook(factory_registry("motor", lambda spec: SLDMotorGraphicsItem(spec["motor_id"], self.read_models)), ui_registry)
        panel_registry = getattr(ui_registry, "mount_panel", None)
        if callable(panel_registry):
            widget = MotorTelemetryDashboardWidget(self.read_models, getattr(application, "event_bus", None))
            self._remember_unhook(panel_registry("BottomDockArea", "Motor Telemetry", widget), ui_registry)
        bus = getattr(application, "lifecycle_bus", None)
        if bus is not None and callable(getattr(bus, "subscribe", None)):
            for name, callback in (("ProjectSaving", self._on_save), ("ProjectLoading", self._on_load)):
                self._remember_unhook(bus.subscribe(name, callback), bus)
        self._registered = True
    def _on_save(self, event: Any) -> None:
        payload = getattr(event, "payload", None)
        if isinstance(payload, dict): payload["motor_dynamics"] = self.persistence.serialize_plugin_data()
    def _on_load(self, event: Any) -> None:
        payload = getattr(event, "payload", None)
        if isinstance(payload, dict) and "motor_dynamics" in payload: self.persistence.deserialize_plugin_data(payload["motor_dynamics"])
    def _remember_unhook(self, token: Any, owner: Any) -> None:
        if callable(token): self._unhooks.append(token)
        elif token is not None and callable(getattr(owner, "unsubscribe", None)): self._unhooks.append(lambda t=token, o=owner: o.unsubscribe(t))
        elif token is not None and callable(getattr(owner, "unregister", None)): self._unhooks.append(lambda t=token, o=owner: o.unregister(t))
    def shutdown(self) -> None:
        errors = []
        for unhook in reversed(self._unhooks):
            try: unhook()
            except Exception as exc: errors.append(exc)
        self._unhooks.clear(); self._registered = False; self.application = None
        if errors: raise ExceptionGroup("motor plugin shutdown encountered unhook failures", errors)
