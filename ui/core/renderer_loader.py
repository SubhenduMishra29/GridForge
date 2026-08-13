# ============================================================
# File: ui/core/renderer_loader.py
# GridForge Renderer Loader
# ============================================================

"""
Automatic renderer-plugin discovery and registration.

Architecture
------------

    ui.renderers/
          │
          ├── bus_renderer.py
          ├── line_renderer.py
          ├── ...
          │
          ▼
    RendererLoader
          │
          ▼
    RendererRegistry
          │
          ▼
    RenderSystem


Responsibilities
----------------
RendererLoader:

    - discovers renderer modules
    - imports renderer modules
    - identifies renderer classes
    - validates the renderer contract
    - registers renderer classes in RendererRegistry

RendererLoader does NOT:

    - create QGraphicsItems
    - create renderer instances
    - modify the Core model
    - own a QGraphicsScene
    - perform rendering
    - implement renderer behavior
    - contain individual renderer implementations


Renderer plugin contract
------------------------

Every renderer class must provide:

    model_type = <Core model class>

    create_item(element, controller)

The create_item member must be callable.

A renderer may optionally provide:

    update_item(item, element, controller)

RenderSystem is responsible for invoking that optional update
contract.

Important
---------

The loader deliberately does not import individual renderer
classes directly.

Importing the renderer module causes the class definitions to
become available, after which the loader inspects only classes
defined by that module.

Discovery is deterministic.

Registration errors are NOT silently converted into successful
loads. A duplicate renderer registration is an architectural
configuration error and must propagate to the caller.
"""

from __future__ import annotations

import importlib
import inspect
import os
from typing import List, Optional, Type, Any


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _package_directory(
    package: str,
) -> str:
    """
    Convert a Python package path into a filesystem directory.

    Example
    -------

        ui.renderers
            ↓
        ui/renderers
    """

    return package.replace(
        ".",
        os.sep,
    )


# ------------------------------------------------------------

def _discover_module_names(
    package: str,
) -> List[str]:
    """
    Discover Python modules contained directly in a package.

    Private modules and __init__.py are ignored.

    Returned module names are sorted to guarantee deterministic
    discovery order.
    """

    package_path = _package_directory(
        package
    )

    if not os.path.isdir(package_path):
        return []

    module_names = []

    for filename in os.listdir(
        package_path
    ):

        if not filename.endswith(".py"):
            continue

        if filename.startswith("_"):
            continue

        module_names.append(
            filename[:-3]
        )

    return sorted(
        module_names
    )


# ------------------------------------------------------------

def _is_renderer_class(
    obj: Any,
    module_name: str,
) -> bool:
    """
    Determine whether an inspected class satisfies the GridForge
    renderer-plugin contract.

    Only classes defined by the inspected module are accepted.

    Required:

        model_type
        create_item(...)
    """

    if not inspect.isclass(obj):
        return False

    # --------------------------------------------------------
    # Do not accidentally register imported classes.
    # --------------------------------------------------------

    if obj.__module__ != module_name:
        return False

    # --------------------------------------------------------
    # Renderer must declare the model type.
    # --------------------------------------------------------

    model_type = getattr(
        obj,
        "model_type",
        None,
    )

    if not isinstance(
        model_type,
        type,
    ):
        return False

    # --------------------------------------------------------
    # Renderer must provide a callable create_item().
    # --------------------------------------------------------

    create_item = getattr(
        obj,
        "create_item",
        None,
    )

    if not callable(
        create_item
    ):
        return False

    return True


# ------------------------------------------------------------

def _renderer_classes(
    module: Any,
    module_name: str,
) -> List[Type[Any]]:
    """
    Return renderer classes defined by a module.

    Classes are returned in deterministic name order.
    """

    classes = []

    for class_name, obj in inspect.getmembers(
        module,
        inspect.isclass,
    ):

        if _is_renderer_class(
            obj,
            module_name,
        ):
            classes.append(
                obj
            )

    return sorted(
        classes,
        key=lambda cls: cls.__name__,
    )


# ============================================================
# LOAD RENDERERS
# ============================================================

def load_renderers(
    registry,
    package: str = "ui.renderers",
) -> List[Type[Any]]:
    """
    Discover and register renderer plugins.

    Parameters
    ----------
    registry:
        RendererRegistry instance to populate.

    package:
        Python package containing renderer modules.

    Returns
    -------
    list[type]
        Renderer classes successfully discovered and registered.

    Raises
    ------
    TypeError
        If registry does not provide the required registration API.

    ImportError
        If a renderer module cannot be imported.

    ValueError
        If a renderer registration conflicts with an existing
        renderer.

    Notes
    -----
    Renderer module import failures are deliberately propagated.

    A renderer module failing to import means the renderer set is
    incomplete. Silently continuing would make the application
    appear valid while leaving the canvas unable to render a model
    element.
    """

    # --------------------------------------------------------
    # Validate registry interface.
    # --------------------------------------------------------

    register = getattr(
        registry,
        "register",
        None,
    )

    if not callable(
        register
    ):
        raise TypeError(
            "registry must provide a callable register() method."
        )

    # --------------------------------------------------------
    # Discover modules.
    # --------------------------------------------------------

    module_names = _discover_module_names(
        package
    )

    if not module_names:

        package_path = _package_directory(
            package
        )

        if not os.path.isdir(
            package_path
        ):
            raise ImportError(
                "Renderer package directory not found: "
                f"'{package_path}'."
            )

        return []

    loaded_renderers = []

    # --------------------------------------------------------
    # Import and inspect modules.
    # --------------------------------------------------------

    for module_name in module_names:

        full_module_name = (
            f"{package}.{module_name}"
        )

        # ----------------------------------------------------
        # Import module.
        #
        # Import errors are intentionally propagated.
        # ----------------------------------------------------

        module = importlib.import_module(
            full_module_name
        )

        # ----------------------------------------------------
        # Find renderer classes defined by this module.
        # ----------------------------------------------------

        renderer_classes = _renderer_classes(
            module,
            full_module_name,
        )

        # ----------------------------------------------------
        # Register every renderer.
        #
        # RendererRegistry handles duplicate protection.
        # ----------------------------------------------------

        for renderer_cls in renderer_classes:

            model_type = getattr(
                renderer_cls,
                "model_type",
            )

            register(
                model_type,
                renderer_cls,
            )

            loaded_renderers.append(
                renderer_cls
            )

    return loaded_renderers


# ============================================================
# OPTIONAL SINGLE-PACKAGE DISCOVERY
# ============================================================

def discover_renderers(
    package: str = "ui.renderers",
) -> List[Type[Any]]:
    """
    Discover renderer classes without registering them.

    This is primarily useful for diagnostics and tests.

    Unlike load_renderers(), this function does not require a
    RendererRegistry.
    """

    module_names = _discover_module_names(
        package
    )

    package_path = _package_directory(
        package
    )

    if not os.path.isdir(
        package_path
    ):
        raise ImportError(
            "Renderer package directory not found: "
            f"'{package_path}'."
        )

    discovered = []

    for module_name in module_names:

        full_module_name = (
            f"{package}.{module_name}"
        )

        module = importlib.import_module(
            full_module_name
        )

        discovered.extend(
            _renderer_classes(
                module,
                full_module_name,
            )
        )

    return discovered


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "load_renderers",
    "discover_renderers",
]
