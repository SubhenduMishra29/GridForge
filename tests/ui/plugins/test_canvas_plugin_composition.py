from ui.canvas.canvas_composition import CanvasComposition
from ui.plugins.canvas_plugin import CanvasPlugin


def test_canvas_plugin_accepts_precomposed_canvas():
    composition = object.__new__(CanvasComposition)
    plugin = CanvasPlugin()
    plugin.set_composition(composition)
    assert plugin.composition is composition
