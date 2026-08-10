# ============================================================
# File: ui/core/plugin_registry.py
# GridForge UI Plugin Registry
# ============================================================
#
# PURPOSE
# -------
# This module provides the central registration mechanism for
# all GridForge UI plugins.
#
# The registry itself does NOT import individual plugins.
#
# Plugins register themselves by using:
#
#     @register_plugin(...)
#
# This keeps the architecture modular and prevents the
# Controller, MainWindow, RenderSystem, or other central files
# from requiring modification whenever a new plugin is added.
#
#
# ARCHITECTURE
# ------------
#
#     Plugin Module
#          │
#          │ @register_plugin(...)
#          ▼
#     Plugin Registry
#          │
#          ▼
#     Plugin Discovery / Loader
#          │
#          ├── Tools
#          ├── Renderers
#          ├── Panels
#          ├── Commands
#          └── Other UI extensions
#
#
# IMPORTANT
# ---------
# This module contains REGISTRATION infrastructure only.
#
# It does NOT:
#     - create Qt widgets
#     - create tools
#     - create renderers
#     - modify the model
#     - import individual plugins
#     - contain application logic
#
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type


# ============================================================
# INTERNAL REGISTRY
# ============================================================
#
# Plugin classes are stored by:
#
#     plugin_type
#         ↓
#     plugin_id
#         ↓
#     plugin class
#
# Example:
#
#     {
#         "tool": {
#             "line": LineTool,
#             "bus": BusTool,
#         },
#         "renderer": {
#             "bus": BusRenderer,
#             "line": LineRenderer,
#         }
#     }
#
# This allows different plugin systems to use the same central
# registration infrastructure without sharing the same namespace.
# ============================================================

_registry: Dict[str, Dict[str, Type[Any]]] = {}


# ============================================================
# REGISTER PLUGIN
# ============================================================

def register_plugin(
    plugin_type: str,
    plugin_id: str,
):
    """
    Decorator used by GridForge plugins to register themselves.

    Parameters
    ----------
    plugin_type:
        Category of the plugin.

        Examples:
            "tool"
            "renderer"
            "panel"
            "command"

    plugin_id:
        Unique identifier within the plugin category.

        Examples:
            "select"
            "bus"
            "line"

    Returns
    -------
    decorator
        A class decorator which registers the plugin.

    Example
    -------
    @register_plugin("tool", "line")
    class LineTool:
        ...

    IMPORTANT
    ---------
    Registration happens when the Python module containing the
    plugin is imported.

    Therefore the plugin discovery system is responsible for
    importing plugin modules.

    The registry itself must NEVER manually import plugins.
    """

    # --------------------------------------------------------
    # Validate plugin type
    # --------------------------------------------------------

    if not isinstance(plugin_type, str) or not plugin_type.strip():
        raise ValueError(
            "plugin_type must be a non-empty string"
        )

    # --------------------------------------------------------
    # Validate plugin ID
    # --------------------------------------------------------

    if not isinstance(plugin_id, str) or not plugin_id.strip():
        raise ValueError(
            "plugin_id must be a non-empty string"
        )

    plugin_type = plugin_type.strip()
    plugin_id = plugin_id.strip()

    # --------------------------------------------------------
    # Actual class decorator
    # --------------------------------------------------------

    def decorator(plugin_cls: Type[Any]) -> Type[Any]:
        """
        Register the decorated plugin class.
        """

        # ----------------------------------------------------
        # Only classes may be registered.
        # ----------------------------------------------------

        if not isinstance(plugin_cls, type):
            raise TypeError(
                "Only classes can be registered as GridForge plugins"
            )

        # ----------------------------------------------------
        # Create category if it does not yet exist.
        # ----------------------------------------------------

        category = _registry.setdefault(
            plugin_type,
            {}
        )

        # ----------------------------------------------------
        # Prevent accidental duplicate IDs.
        #
        # Duplicate registration of the SAME class is harmless.
        # Duplicate registration of DIFFERENT classes is an
        # architecture/configuration error and must be detected.
        # ----------------------------------------------------

        existing = category.get(plugin_id)

        if existing is not None:

            if existing is plugin_cls:
                return plugin_cls

            raise ValueError(
                "Duplicate GridForge plugin registration: "
                f"type='{plugin_type}', "
                f"id='{plugin_id}' already belongs to "
                f"{existing.__name__}"
            )

        # ----------------------------------------------------
        # Register plugin.
        # ----------------------------------------------------

        category[plugin_id] = plugin_cls

        return plugin_cls

    return decorator


# ============================================================
# GET PLUGIN
# ============================================================

def get_plugin(
    plugin_type: str,
    plugin_id: str,
) -> Optional[Type[Any]]:
    """
    Retrieve a registered plugin class.

    Parameters
    ----------
    plugin_type:
        Plugin category.

    plugin_id:
        Plugin identifier.

    Returns
    -------
    Type | None
        Registered plugin class, or None if it does not exist.

    Example
    -------
    LineTool = get_plugin("tool", "line")
    """

    return _registry.get(
        plugin_type,
        {}
    ).get(plugin_id)


# ============================================================
# GET ALL PLUGINS OF A TYPE
# ============================================================

def get_plugins(
    plugin_type: str,
) -> List[Type[Any]]:
    """
    Return all registered plugin classes belonging to a
    particular plugin category.

    Example
    -------
    tools = get_plugins("tool")
    """

    return list(
        _registry.get(plugin_type, {}).values()
    )


# ============================================================
# GET PLUGIN IDs
# ============================================================

def get_plugin_ids(
    plugin_type: str,
) -> List[str]:
    """
    Return all registered plugin IDs for a plugin category.

    Example
    -------
    get_plugin_ids("tool")

    might return:

        ["select", "bus", "line"]
    """

    return list(
        _registry.get(plugin_type, {}).keys()
    )


# ============================================================
# CHECK REGISTRATION
# ============================================================

def is_registered(
    plugin_type: str,
    plugin_id: str,
) -> bool:
    """
    Check whether a plugin ID is registered.
    """

    return plugin_id in _registry.get(
        plugin_type,
        {}
    )


# ============================================================
# UNREGISTER PLUGIN
# ============================================================

def unregister_plugin(
    plugin_type: str,
    plugin_id: str,
) -> bool:
    """
    Remove a plugin from the registry.

    Returns
    -------
    bool
        True if a plugin was removed.
        False if the plugin did not exist.

    Notes
    -----
    This is primarily useful for:

        - testing
        - development reload
        - optional plugin systems

    Normal application execution should generally not
    unregister plugins.
    """

    category = _registry.get(plugin_type)

    if not category:
        return False

    if plugin_id not in category:
        return False

    del category[plugin_id]

    # Remove empty category to keep registry clean.
    if not category:
        del _registry[plugin_type]

    return True


# ============================================================
# CLEAR REGISTRY
# ============================================================

def clear_registry(
    plugin_type: Optional[str] = None,
) -> None:
    """
    Clear registered plugins.

    Parameters
    ----------
    plugin_type:
        If supplied, only that plugin category is cleared.

        If None, the entire registry is cleared.

    IMPORTANT
    ---------
    This function is primarily intended for testing and
    development reload scenarios.
    """

    if plugin_type is None:
        _registry.clear()
        return

    _registry.pop(plugin_type, None)


# ============================================================
# REGISTRY SNAPSHOT
# ============================================================

def get_registry_snapshot() -> Dict[str, Dict[str, Type[Any]]]:
    """
    Return a copy of the current registry.

    This is useful for:

        - diagnostics
        - debugging
        - plugin inspection
        - development tools

    The returned dictionary is a copy and therefore cannot
    directly modify the internal registry.
    """

    return {
        plugin_type: dict(plugins)
        for plugin_type, plugins in _registry.items()
    }


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "register_plugin",
    "get_plugin",
    "get_plugins",
    "get_plugin_ids",
    "is_registered",
    "unregister_plugin",
    "clear_registry",
    "get_registry_snapshot",
]
