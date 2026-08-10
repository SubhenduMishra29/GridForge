from ui.core.plugin_registry import register


@register
class BasicToolsPlugin:
    order = 20  # after toolbar

    def build(self, main_window, controller):
        toolbar = main_window.get_component("toolbar")

        # Inject tools dynamically
        toolbar.add_tool(
            "Select",
            lambda: controller.set_tool("select"),
            "select"
        )

        toolbar.add_tool(
            "Bus",
            lambda: controller.set_tool("bus"),
            "bus"
        )

        toolbar.add_tool(
            "Line",
            lambda: controller.set_tool("line"),
            "line"
        )

        return None
