from ui.canvas.canvas_composition import CanvasComposer
from ui.canvas.grid_scene import GridScene
from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.tools.default_tool_registry import create_default_tool_factories
from core.application.bootstrap import create_application
from core.network.network import Network


def test_canvas_composer_uses_one_shared_scene_and_service_instances(qapp):
    application = create_application(Network())
    controller = Controller(application=application)
    composer = CanvasComposer()
    preparation = composer.prepare(controller=controller)

    equipment_registry = EquipmentRegistry.create_default()
    symbol_registry = SymbolRegistry()
    register_builtin_symbols(symbol_registry)
    factory = SLDGraphicsItemFactory(equipment_registry, symbol_registry, application)
    realization = SemanticPresentationRealization(equipment_registry, symbol_registry)
    render_system = SLDCanvasRenderSystem(preparation.scene, factory, realization)
    tool_registry = create_default_tool_factories(
        controller=controller,
        application=application,
        selection_manager=preparation.selection_manager,
        snap_system=preparation.snap_system,
        preview_layer=preparation.preview_layer,
        symbol_registry=symbol_registry,
    )
    tool_manager = ToolManager(
        controller=controller,
        application=application,
        selection_manager=preparation.selection_manager,
        snap_system=preparation.snap_system,
        tool_registry=tool_registry,
        preview_layer=preparation.preview_layer,
        equipment_registry=equipment_registry,
    )
    composition = composer.compose(
        controller=controller,
        tool_manager=tool_manager,
        preparation=preparation,
        sld_canvas_projection=SLDCanvasProjection(),
        sld_canvas_render_system=render_system,
    )

    assert isinstance(composition.scene, GridScene)
    assert composition.view.scene() is composition.scene
    assert composition.sld_canvas_render_system.scene is composition.scene
    assert composition.selection_manager is preparation.selection_manager
    assert composition.interaction_manager.view is composition.view
    assert composition.navigation_controller.view is composition.view
    assert composition.coordinate_system.view is composition.view
    assert composition.snap_system.scene is composition.scene
