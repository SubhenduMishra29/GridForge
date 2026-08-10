from ui.core.plugin_registry import register
from ui.toolbars.main_toolbar import MainToolbar


@register
class MainToolbarPlugin:
    order = 10

    def build(self, main_window, controller):
        toolbar = MainToolbar()

        main_window.addToolBar(toolbar)

        return ("toolbar", toolbar)
