"""
GridForge V2 — Plugin Registry
==============================

File:
    ui/core/plugin_registry.py

Purpose
-------
Central registration infrastructure for GridForge plugins.

The registry maintains independent namespaces for different
plugin categories, for example:

    "ui"
    "tool"
    "renderer"
    "panel"
    "command"

Plugins register themselves using:

    @register_plugin("tool", "line")

The registry does not import plugin modules. Plugin discovery
and loading are responsible for importing modules, after which
decorators register the discovered classes.

Architectural Contract
----------------------
1. The registry contains registration infrastructure only.
2. The registry does not import concrete plugins.
3. The registry does not create plugin instances.
4. The registry does not create Qt objects.
5. The registry does not modify the GridForge model.
6. Each plugin category has an independent identifier
   namespace.
7. Duplicate identifiers within a category are prohibited.
8. Registering the same class under the same category and ID
   is idempotent.
9. Plugin discovery/loading is separate from registration.
10. Registry mutation functions are primarily intended for
    application initialization, testing, and development
    reload scenarios.

Example
-------
    @register_plugin("tool", "line")
    class LineTool:
        ...
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type


# ============================================================================
# INTERNAL REGISTRY
# ============================================================================

_registry: Dict[str, Dict[str, Type[Any]]] = {}


# ============================================================================
# VALIDATION
# ============================================================================

def _validate_identifier(
    value: str,
    name: str,
) -> str:
    """
    Validate and normalize a registry identifier.
    """

    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be a string"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{name} must be a non-empty string"
        )

    return value


# ============================================================================
# REGISTER PLUGIN
# ============================================================================

def register_plugin(
    plugin_type: str,
    plugin_id: str,
):
    """
    Register a plugin class using a decorator.

    Parameters
    ----------
    plugin_type:
        Plugin category, such as "ui", "tool", or "renderer".

    plugin_id:
        Unique identifier within that category.

    Returns
    -------
    callable
        Class decorator.

    Raises
    ------
    TypeError
        If the decorated object is not a class.

    ValueError
        If the plugin type or ID is invalid, or if a different
        class is already registered under the same category and
        ID.
    """

    plugin_type = _validate_identifier(
        plugin_type,
        "plugin_type",
    )

    plugin_id = _validate_identifier(
        plugin_id,
        "plugin_id",
    )

    def decorator(
        plugin_cls: Type[Any],
    ) -> Type[Any]:
        """
        Register the decorated plugin class.
        """

        if not isinstance(plugin_cls, type):
            raise TypeError(
                "Only classes can be registered as "
                "GridForge plugins"
            )

        category = _registry.setdefault(
            plugin_type,
            {},
        )

        existing = category.get(plugin_id)

        if existing is not None:

            # Re-importing/re-registering the same class is
            # harmless and therefore idempotent.
            if existing is plugin_cls:
                return plugin_cls

            raise ValueError(
                "Duplicate GridForge plugin registration: "
                f"type='{plugin_type}', "
                f"id='{plugin_id}' already belongs to "
                f"{existing.__name__}"
            )

        category[plugin_id] = plugin_cls

        return plugin_cls

    return decorator


# ============================================================================
# GET PLUGIN
# ============================================================================

def get_plugin(
    plugin_type: str,
    plugin_id: str,
) -> Optional[Type[Any]]:
    """
    Retrieve a registered plugin class.

    Returns None when the requested plugin is not registered.
    """

    plugin_type = _validate_identifier(
        plugin_type,
        "plugin_type",
    )

    plugin_id = _validate_identifier(
        plugin_id,
        "plugin_id",
    )

    return _registry.get(
        plugin_type,
        {},
    ).get(plugin_id)


# ============================================================================
# GET PLUGINS
# ============================================================================

def get_plugins(
    plugin_type: str,
) -> List[Type[Any]]:
    """
    Return all registered plugin classes for a category.

    The returned list is a snapshot and does not expose the
    internal registry.
    """

    plugin_type = _validate_identifier(
        plugin_type,
        "plugin_type",
    )

    return list(
        _registry.get(
            plugin_type,
            {},
        ).values()
    )


# ============================================================================
# GET PLUGIN IDS
# ============================================================================

def get_plugin_ids(
    plugin_type: str,
) -> List[str]:
    """
    Return all registered plugin IDs for a category.
    """

    plugin_type = _validate_identifier(
        plugin_type,
        "plugin_type",
    )

    return list(
        _registry.get(
            plugin_type,
            {},
        ).keys()
    )


# ============================================================================
# CHECK REGISTRATION
# ============================================================================

def is_registered(
    plugin_type: str,
    plugin_id: str,
) -> bool:
    """
    Return True if a plugin is registered under the given
    category and identifier.
    """

    plugin_type = _validate_identifier(
        plugin_type,
        "plugin_type",
    )

    plugin_id = _validate_identifier(
        plugin_id,
        "plugin_id",
    )

    return plugin_id in _registry.get(
        plugin_type,
        {},
    )


# ============================================================================
# UNREGISTER PLUGIN
# ============================================================================

def unregister_plugin(
    plugin_type: str,
    plugin_id: str,
) -> bool:
    """
    Remove a plugin from the registry.

    Returns
    -------
    bool
        True if a plugin was removed, otherwise False.

    Notes
    -----
    Intended primarily for testing and development reload
    scenarios.
    """

    plugin_type = _validate_identifier(
        plugin_type,
        "plugin_type",
    )

    plugin_id = _validate_identifier(
        plugin_id,
        "plugin_id",
    )

    category = _registry.get(plugin_type)

    if category is None:
        return False

    if plugin_id not in category:
        return False

    del category[plugin_id]

    if not category:
        del _registry[plugin_type]

    return True


# ============================================================================
# CLEAR REGISTRY
# ============================================================================

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

    Notes
    -----
    Primarily intended for testing and development reload
    scenarios.
    """

    if plugin_type is None:
        _registry.clear()
        return

    plugin_type = _validate_identifier(
        plugin_type,
        "plugin_type",
    )

    _registry.pop(
        plugin_type,
        None,
    )


# ============================================================================
# REGISTRY SNAPSHOT
# ============================================================================

def get_registry_snapshot() -> Dict[
    str,
    Dict[str, Type[Any]],
]:
    """
    Return a detached snapshot of the complete registry.

    Mutating the returned dictionaries does not modify the
    internal registry.
    """

    return {
        plugin_type: dict(plugins)
        for plugin_type, plugins in _registry.items()
    }


# ============================================================================
# PUBLIC API
# ============================================================================

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
