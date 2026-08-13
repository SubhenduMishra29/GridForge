"""
GridForge V2 — Renderer Loader
==============================

File:
    ui/core/renderer_loader.py

Purpose
-------
Discovers renderer implementations from a Python package and
registers them with a RendererRegistry.

The loader is responsible for:

    1. importing the renderer package;
    2. discovering its Python modules;
    3. importing those modules;
    4. identifying valid renderer classes;
    5. registering those classes with RendererRegistry.

The loader does not:

    - instantiate renderers;
    - create QGraphicsItems;
    - modify the Core model;
    - perform rendering;
    - depend on Qt.

Renderer Contract
-----------------
A renderer class discovered by this loader must provide:

    model_type = <Core model class>

and:

    create_item(...)

The renderer registry stores the renderer class. Renderer
lifecycle and invocation belong to RenderSystem.

Architectural Contract
----------------------
    Renderer Package
          |
          v
    RendererLoader
          |
          v
    RendererRegistry
          |
          v
    RenderSystem
          |
          v
    Renderer
          |
          v
    QGraphicsItem
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import Any, List


DEFAULT_RENDERER_PACKAGE = "ui.renderers"


def _discover_modules(
    package: str,
) -> List[str]:
    """
    Discover Python modules contained by a renderer package.

    The returned module names are deterministic.
    """

    try:
        package_module = importlib.import_module(package)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to import renderer package '{package}'"
        ) from exc

    package_path = getattr(
        package_module,
        "__path__",
        None,
    )

    if package_path is None:
        raise TypeError(
            f"Renderer package '{package}' is not a package"
        )

    module_names = [
        module_info.name
        for module_info in pkgutil.iter_modules(
            package_path
        )
        if not module_info.name.startswith("_")
    ]

    module_names.sort()

    return module_names


def _import_renderer_modules(
    package: str,
) -> List[ModuleType]:
    """
    Import all renderer modules from a package.

    Import failures are propagated because a renderer module
    failure represents an invalid UI configuration.
    """

    modules: List[ModuleType] = []

    for module_name in _discover_modules(package):

        full_module_name = (
            f"{package}.{module_name}"
        )

        try:
            module = importlib.import_module(
                full_module_name
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to import renderer module "
                f"'{full_module_name}'"
            ) from exc

        modules.append(module)

    return modules


def _find_renderers(
    module: ModuleType,
) -> List[type]:
    """
    Find valid renderer classes defined directly in a module.

    A valid renderer must:

        - be a class;
        - be defined by the inspected module;
        - expose a model_type class attribute;
        - expose a callable create_item attribute.
    """

    renderers: List[type] = []

    for _, obj in inspect.getmembers(
        module,
        inspect.isclass,
    ):

        if obj.__module__ != module.__name__:
            continue

        model_type = getattr(
            obj,
            "model_type",
            None,
        )

        create_item = getattr(
            obj,
            "create_item",
            None,
        )

        if not isinstance(
            model_type,
            type,
        ):
            continue

        if not callable(create_item):
            continue

        renderers.append(obj)

    return renderers


def load_renderers(
    registry: Any,
    package: str = DEFAULT_RENDERER_PACKAGE,
) -> int:
    """
    Discover and register renderer classes.

    Parameters
    ----------
    registry:
        RendererRegistry instance to populate.

    package:
        Python package containing renderer modules.

    Returns
    -------
    int
        Number of renderer classes registered.

    Raises
    ------
    TypeError
        If registry does not provide the required register()
        operation.

    RuntimeError
        If a renderer package or renderer module cannot be
        imported.

    ValueError
        If RendererRegistry detects duplicate/conflicting
        renderer registration.
    """

    register = getattr(
        registry,
        "register",
        None,
    )

    if not callable(register):
        raise TypeError(
            "registry must provide a callable register() method"
        )

    registered_count = 0

    modules = _import_renderer_modules(package)

    for module in modules:

        renderers = _find_renderers(module)

        for renderer in renderers:

            model_type = renderer.model_type

            registry.register(
                model_type,
                renderer,
            )

            registered_count += 1

    return registered_count


__all__ = [
    "DEFAULT_RENDERER_PACKAGE",
    "load_renderers",
]
