"""
GridForge V2 — UI Registry
==========================

File:
    ui/ui_registry.py

Purpose
-------
Composes the GridForge UI from registered UI plugins.

The UI Registry is responsible for:

    - obtaining registered UI plugins;
    - ordering plugins;
    - constructing plugin instances;
    - invoking their build contract;
    - collecting created UI components.

MainWindow should delegate UI composition to:

    build_ui(main_window, controller)

Architectural Contract
----------------------
1. UI composition is plugin-driven.
2. The registry does not contain concrete UI component logic.
3. The registry does not create the application Controller.
4. The existing Controller is injected into plugins.
5. Plugin construction failures are fatal and must propagate.
6. Duplicate component names are rejected.
7. Component names must be non-empty strings.
8. Plugin ordering is controlled by the optional `order`
   attribute.
9. The registry does not own the lifetime of the MainWindow.
10. The registry returns the constructed component instances
    to the MainWindow/application layer.

Plugin Contract
---------------
A registered UI plugin must provide:

    build(main_window, controller)

The build method may return:

    None

or:

    (component_name, component_instance)

or:

    {
        "component_name": component_instance,
        ...
    }
"""

from __future__ import annotations

from typing import Any, Dict

from ui.core.plugin_registry import get_plugins


def _validate_component_name(name: Any) -> str:
    """
    Validate and normalize a UI component name.
    """

    if not isinstance(name, str):
        raise TypeError(
            "UI component name must be a string"
        )

    name = name.strip()

    if not name:
        raise ValueError(
            "UI component name must be non-empty"
        )

    return name


def _register_component(
    components: Dict[str, Any],
    name: Any,
    instance: Any,
    plugin_name: str,
) -> None:
    """
    Register one UI component.

    Duplicate component names are rejected because component
    names form the UI composition namespace.
    """

    name = _validate_component_name(name)

    if name in components:
        raise RuntimeError(
            f"Duplicate UI component name '{name}' "
            f"registered by plugin '{plugin_name}'"
        )

    components[name] = instance


def build_ui(
    main_window: Any,
    controller: Any,
) -> Dict[str, Any]:
    """
    Build the GridForge UI from registered UI plugins.

    Parameters
    ----------
    main_window:
        MainWindow instance receiving the UI components.

    controller:
        Existing GridForge UI Controller.

    Returns
    -------
    dict[str, Any]
        Mapping of component names to constructed instances.

    Raises
    ------
    TypeError
        If a registered plugin does not implement the expected
        build contract or returns an invalid result.

    RuntimeError
        If multiple plugins register the same component name.

    Exception
        Any exception raised during plugin construction or
        plugin.build() is propagated with plugin context.
    """

    components: Dict[str, Any] = {}

    plugins = sorted(
        get_plugins(),
        key=lambda plugin_cls: getattr(
            plugin_cls,
            "order",
            100,
        ),
    )

    for plugin_cls in plugins:
        plugin_name = getattr(
            plugin_cls,
            "__name__",
            plugin_cls.__class__.__name__,
        )

        # ----------------------------------------------------
        # Construct plugin
        # ----------------------------------------------------

        try:
            plugin = plugin_cls()
        except Exception as exc:
            raise RuntimeError(
                f"Failed to instantiate UI plugin "
                f"'{plugin_name}'"
            ) from exc

        # ----------------------------------------------------
        # Validate build contract
        # ----------------------------------------------------

        build = getattr(
            plugin,
            "build",
            None,
        )

        if not callable(build):
            raise TypeError(
                f"UI plugin '{plugin_name}' must provide "
                "a callable build(main_window, controller) method"
            )

        # ----------------------------------------------------
        # Build plugin UI
        # ----------------------------------------------------

        try:
            result = build(
                main_window,
                controller,
            )
        except Exception as exc:
            raise RuntimeError(
                f"UI plugin '{plugin_name}' failed during build()"
            ) from exc

        # ----------------------------------------------------
        # No component
        # ----------------------------------------------------

        if result is None:
            continue

        # ----------------------------------------------------
        # Single component
        # ----------------------------------------------------

        if isinstance(result, tuple):
            if len(result) != 2:
                raise TypeError(
                    f"UI plugin '{plugin_name}' returned a tuple "
                    "that must contain exactly "
                    "(component_name, instance)"
                )

            name, instance = result

            _register_component(
                components,
                name,
                instance,
                plugin_name,
            )

            continue

        # ----------------------------------------------------
        # Multiple components
        # ----------------------------------------------------

        if isinstance(result, dict):
            for name, instance in result.items():
                _register_component(
                    components,
                    name,
                    instance,
                    plugin_name,
                )

            continue

        # ----------------------------------------------------
        # Invalid result
        # ----------------------------------------------------

        raise TypeError(
            f"UI plugin '{plugin_name}'.build() must return "
            "None, (name, instance), or dict"
        )

    return components


__all__ = [
    "build_ui",
]
