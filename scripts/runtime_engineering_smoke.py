# ============================================================
# GridForge V2 — Runtime Engineering Workflow Smoke Verification
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

import main
from ui.core.qt import QListWidget, QPointF


TARGET_TOOL_IDS = (
    "bus",
    "breaker",
    "transformer",
    "generator",
    "load",
    "current_transformer",
    "relay",
)


def _event(x: float, y: float) -> SimpleNamespace:
    return SimpleNamespace(scene_position=QPointF(x, y))


def main_smoke() -> None:
    app, window, plugin_manager, workspace_controller, ui_update_boundary, ui_lifecycle = main.build_application()
    try:
        controller = window.controller
        if controller is None:
            raise SystemExit("Runtime smoke: MainWindow controller missing.")
        tool_manager = controller._tool_manager
        if tool_manager is None:
            raise SystemExit("Runtime smoke: ToolManager is not bound.")

        panels = plugin_manager.get("panels")
        if panels is None:
            raise SystemExit("Runtime smoke: Panels plugin missing.")
        equipment_dock = panels.get_dock("equipment")
        if equipment_dock is None:
            raise SystemExit("Runtime smoke: equipment dock missing.")
        palette = equipment_dock.widget().findChild(QListWidget, "EquipmentPalette")
        if palette is None:
            raise SystemExit("Runtime smoke: equipment palette widget missing.")

        if palette.count() < len(TARGET_TOOL_IDS):
            raise SystemExit(
                f"Runtime smoke: equipment palette unexpectedly small ({palette.count()})."
            )

        for tool_id in TARGET_TOOL_IDS:
            definition = tool_manager.equipment_registry.require(tool_id)
            if definition is None:
                raise SystemExit(f"Runtime smoke: no equipment definition for {tool_id!r}.")
            tool_manager.activate(tool_id, cancel_active_creation=True)
            tool_manager.mouse_move(_event(120.0, 120.0))
            app.processEvents()
            if not tool_manager.preview_layer.scene.items():
                raise SystemExit(f"Runtime smoke: no preview graphics for {tool_id!r}.")
            tool_manager.cancel()
            app.processEvents()

        tool_manager.activate("bus", cancel_active_creation=True)
        tool_manager.mouse_move(_event(200.0, 160.0))
        if not tool_manager.mouse_release(_event(200.0, 160.0)):
            raise SystemExit("Runtime smoke: Bus placement did not commit.")
        app.processEvents()

        network = controller.application.read_network()
        buses = tuple(
            element for element in network.elements
            if str(getattr(element, "element_type", "")).lower() == "bus"
        )
        if not buses:
            raise SystemExit("Runtime smoke: committed Bus is absent from Application read model.")

        selected_ids = tuple(tool_manager.selection_manager.get_selected_ids())
        if str(buses[-1].object_id) not in selected_ids:
            raise SystemExit("Runtime smoke: committed Bus was not selected through SelectionManager.")

        print("RUNTIME VERIFIED: palette icons, tool activation, live previews, Bus placement, read-model visibility, and selection.")
    finally:
        main._shutdown_components(
            ui_lifecycle=ui_lifecycle,
            workspace_controller=workspace_controller,
            ui_update_boundary=ui_update_boundary,
            plugin_manager=plugin_manager,
        )


if __name__ == "__main__":
    main_smoke()
