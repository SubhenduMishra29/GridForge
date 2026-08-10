"""
UI Plugin Registry

Purpose:
--------
Central system to register and retrieve UI plugins.

This enables a true plugin-based architecture where:
- UI components self-register
- No central file needs modification
- Features can be added/removed dynamically

How It Works:
-------------
1. Plugin class uses @register decorator
2. It gets added to the global registry
3. ui_registry.py loads and executes all plugins

Golden Rule:
------------
Plugins REGISTER themselves.
The registry NEVER imports plugins manually.
"""

from typing import List, Type


# Internal storage for plugin classes
_registry: List[Type] = []


# ------------------------------------------------------------------
# Registration Decorator
# ------------------------------------------------------------------
def register(plugin_cls):
    """
    Decorator to register a UI plugin.

    Usage:
        @register
        class MyPlugin(UIPlugin):
            ...

    Rules:
    ------
    - Must be used on classes only
    - Class must implement .build(...)
    """

    # Basic validation
    if not hasattr(plugin_cls, "build"):
        raise TypeError(
            f"{plugin_cls.__name__} must implement a 'build' method"
        )

    # Prevent duplicate registration
    if plugin_cls in _registry:
        return plugin_cls

    _registry.append(plugin_cls)
    return plugin_cls


# ------------------------------------------------------------------
# Access Registry
# ------------------------------------------------------------------
def get_plugins():
    """
    Return all registered plugin classes.

    Important:
    ----------
    - Returns classes, NOT instances
    - Instantiation happens in ui_registry.py
    """

    return list(_registry)


# ------------------------------------------------------------------
# Optional Utilities (Advanced Use)
# ------------------------------------------------------------------
def clear_registry():
    """
    Clear all registered plugins.

    Use cases:
    - Testing
    - Reloading plugins dynamically
    """
    _registry.clear()


def is_registered(plugin_cls) -> bool:
    """
    Check if a plugin is already registered.
    """
    return plugin_cls in _registry
