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

    - resolves the renderer Python package;
    - discovers renderer modules;
    - imports renderer modules;
    - identifies renderer classes;
    - validates the renderer contract;
    - registers renderer classes in RendererRegistry.

RendererLoader does NOT:

    - create QGraphicsItems;
    - create renderer instances;
    - modify the Core model;
    - own a QGraphicsScene;
    - perform rendering;
    - implement renderer behavior;
    - contain individual renderer implementations.


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


Discovery
---------

Renderer modules are discovered through Python's package
machinery rather than by assuming that the current working
directory is the project root.

Discovery is deterministic:

    1. renderer modules are sorted by module name;
    2. renderer classes within each module are sorted by class
       name.

Only classes defined directly by the inspected module are
accepted. Imported classes are ignored.


Registration
------------

Renderer classes are fully discovered and validated before
registration begins.

Existing conflicting registrations are detected before the
registry is modified.

The RendererRegistry remains the authoritative owner of
registration rules, including duplicate protection.

Registration errors are not silently swallowed.


RendererLoader does NOT own:

    - renderer instances;
    - renderer lifecycle;
    - graphics items;
    - rendering orchestration.

Those responsibilities belong respectively to the renderer
implementation layer and RenderSystem.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any, List, Type


# ============================================================
# PACKAGE DISCOVERY
# ============================================================


def _discover_module_names(
    package: str,
) -> List[str]:
    """
    Discover Python modules contained directly in a package.

    Parameters
    ----------
    package:
        Fully-qualified Python package name.

    Returns
    -------
    list[str]
        Deterministically sorted fully-qualified module names.

    Raises
    ------
    ImportError
        If the package cannot be imported or does not expose a
        package path.

    Notes
    -----
    Discovery uses Python's import machinery rather than
    constructing a filesystem path from the package name.

    This allows GridForge to work correctly regardless of the
    current working directory, provided the package is available
    through Python's import path.
    """

    package_module = importlib.import_module(
        package
    )

    package_path = getattr(
        package_module,
        "__path__",
        None,
    )

    if package_path is None:
        raise ImportError(
            f"Renderer package '{package}' is not a package."
        )

    module_names: List[str] = []

    for module_info in pkgutil.iter_modules(
        package_path
    ):

        # ----------------------------------------------------
        # Ignore private modules.
        # ----------------------------------------------------

        if module_info.name.startswith("_"):
            continue

        # ----------------------------------------------------
        # Renderer discovery currently operates on direct
        # Python modules only.
        #
        # Nested packages can be introduced later if the
        # plugin architecture explicitly requires them.
        # ----------------------------------------------------

        if module_info.ispkg:
            continue

        module_names.append(
            f"{package}.{module_info.name}"
        )

    return sorted(
        module_names
    )


# ============================================================
# RENDERER CONTRACT VALIDATION
# ============================================================


def _is_renderer_class(
    obj: Any,
    module_name: str,
) -> bool:
    """
    Determine whether an inspected class satisfies the GridForge
    renderer-plugin contract.

    Required
    --------
    model_type:
        Must be a class.

    create_item:
        Must be callable.

    Only classes defined directly by the inspected module are
    accepted.

    Imported classes are deliberately ignored.
    """

    # --------------------------------------------------------
    # Object must be a class.
    # --------------------------------------------------------

    if not inspect.isclass(obj):
        return False

    # --------------------------------------------------------
    # Do not accidentally register imported classes.
    # --------------------------------------------------------

    if obj.__module__ != module_name:
        return False

    # --------------------------------------------------------
    # Renderer must declare a Core model type.
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
    # Renderer must provide create_item().
    #
    # Exact callable signature validation intentionally does
    # not occur here. RenderSystem owns invocation semantics.
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


# ============================================================
# MODULE RENDERER INSPECTION
# ============================================================


def _renderer_classes(
    module: Any,
    module_name: str,
) -> List[Type[Any]]:
    """
    Return renderer classes defined directly by a module.

    Classes are returned in deterministic class-name order.
    """

    classes: List[Type[Any]] = []

    for _class_name, obj in inspect.getmembers(
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
# DISCOVER RENDERERS
# ============================================================


def discover_renderers(
    package: str = "ui.renderers",
) -> List[Type[Any]]:
    """
    Discover renderer classes without registering them.

    Parameters
    ----------
    package:
        Python package containing renderer modules.

    Returns
    -------
    list[type]
        Renderer classes discovered from the package.

    Raises
    ------
    ImportError
        If the package or one of its renderer modules cannot be
        imported.

    Notes
    -----
    No RendererRegistry is required.

    The function performs discovery and contract validation only.
    It does not create renderer instances or modify application
    state.
    """

    module_names = _discover_module_names(
        package
    )

    discovered: List[Type[Any]] = []

    # --------------------------------------------------------
    # Import and inspect every module before returning.
    # --------------------------------------------------------

    for full_module_name in module_names:

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
# REGISTRATION PREFLIGHT
# ============================================================


def _validate_registration_plan(
    registry: Any,
    renderer_classes: List[Type[Any]],
) -> None:
    """
    Validate the renderer registration plan before modifying the
    registry.

    The GridForge RendererRegistry provides:

        contains(model_type)
        get_renderer(model_type)

    These APIs allow the loader to detect conflicting existing
    registrations before any new registration is performed.

    This also detects duplicate model_type declarations among the
    newly discovered renderer classes.

    Raises
    ------
    ValueError
        If multiple discovered renderer classes claim the same
        model type, or an existing renderer conflicts with a
        discovered renderer.

    TypeError
        If the supplied registry does not provide the expected
        RendererRegistry lookup interface.
    """

    contains = getattr(
        registry,
        "contains",
        None,
    )

    get_renderer = getattr(
        registry,
        "get_renderer",
        None,
    )

    if not callable(contains):
        raise TypeError(
            "registry must provide a callable contains() method."
        )

    if not callable(get_renderer):
        raise TypeError(
            "registry must provide a callable get_renderer() method."
        )

    # --------------------------------------------------------
    # Track model types discovered during this load.
    # --------------------------------------------------------

    planned: dict[
        Type[Any],
        Type[Any],
    ] = {}

    for renderer_cls in renderer_classes:

        model_type = getattr(
            renderer_cls,
            "model_type",
        )

        # ----------------------------------------------------
        # Detect duplicate renderer claims within the same
        # discovery operation.
        # ----------------------------------------------------

        existing_planned = planned.get(
            model_type
        )

        if existing_planned is not None:

            if existing_planned is renderer_cls:
                continue

            raise ValueError(
                "Multiple renderer classes discovered for "
                f"model type '{model_type.__name__}': "
                f"'{existing_planned.__name__}' and "
                f"'{renderer_cls.__name__}'."
            )

        planned[
            model_type
        ] = renderer_cls

        # ----------------------------------------------------
        # Detect conflict with an existing direct registry
        # registration.
        #
        # RendererRegistry.register() permits the same class
        # to be registered idempotently, so that case is valid.
        # ----------------------------------------------------

        if contains(model_type):

            existing_renderer = get_renderer(
                model_type
            )

            if existing_renderer is renderer_cls:
                continue

            raise ValueError(
                "Renderer already registered for model type "
                f"'{model_type.__name__}': "
                f"'{existing_renderer.__name__}'."
            )


# ============================================================
# LOAD RENDERERS
# ============================================================


def load_renderers(
    registry: Any,
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
        If registry does not provide the required RendererRegistry
        interface.

    ImportError
        If the renderer package or one of its modules cannot be
        imported.

    ValueError
        If renderer registration conflicts with an existing
        renderer or if multiple discovered renderers claim the
        same model type.

    Notes
    -----
    Discovery and validation occur before registration.

    This prevents normal configuration conflicts from leaving the
    registry partially populated.

    The RendererRegistry remains responsible for final
    registration enforcement.
    """

    # --------------------------------------------------------
    # Validate required registration interface.
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
    # Discover ALL renderer classes first.
    #
    # No registry mutation occurs during discovery.
    # --------------------------------------------------------

    renderer_classes = discover_renderers(
        package
    )

    # --------------------------------------------------------
    # Preflight the complete registration plan.
    #
    # Conflicts are detected before registration begins.
    # --------------------------------------------------------

    _validate_registration_plan(
        registry,
        renderer_classes,
    )

    # --------------------------------------------------------
    # Register only after discovery and preflight succeed.
    #
    # RendererRegistry remains the authoritative registration
    # boundary.
    # --------------------------------------------------------

    for renderer_cls in renderer_classes:

        model_type = getattr(
            renderer_cls,
            "model_type",
        )

        register(
            model_type,
            renderer_cls,
        )

    return list(
        renderer_classes
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "load_renderers",
    "discover_renderers",
]
