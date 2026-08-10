"""
Dynamic UI registry using plugin architecture.

Responsibilities:
- Discover registered UI plugins
- Build and attach them to the MainWindow
- Return a dictionary of created components

MainWindow MUST only call: build_ui(...)
"""

from ui.core.plugin_registry import get_plugins


def build_ui(main_window, controller):
    """
    Build the UI dynamically using registered plugins.

    Args:
        main_window: QMainWindow instance
        controller: Application controller

    Returns:
        dict: {component_name: instance}
    """

    components = {}

    # Load plugins (optionally sorted by order if defined)
    plugins = sorted(
        get_plugins(),
        key=lambda p: getattr(p, "order", 100)
    )

    for plugin_cls in plugins:
        plugin = plugin_cls()

        try:
            result = plugin.build(main_window, controller)

            # Allow flexible return formats
            if result is None:
                continue

            if isinstance(result, tuple):
                name, instance = result
                components[name] = instance

            elif isinstance(result, dict):
                components.update(result)

            else:
                raise TypeError(
                    f"{plugin_cls.__name__}.build() must return "
                    "None, (name, instance), or dict"
                )

        except Exception as e:
            print(f"[UI Registry] Failed to load plugin: {plugin_cls.__name__}")
            print(f"Error: {e}")

    return components
