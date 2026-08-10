"""
Renderer Loader (Auto-Registration System)

Location:
---------
ui/core/renderer_loader.py

Purpose:
--------
Automatically discovers and registers all renderer plugins.

This removes the need for manual registration like:
    registry.register(Bus, BusRenderer)

How It Works:
-------------
1. Scans the ui/renderers/ directory
2. Imports each module
3. Finds classes with:
       - model_type attribute
       - create_item(...) method
4. Registers them into RendererRegistry

Usage:
------
from ui.core.renderer_loader import load_renderers
load_renderers(registry)

Requirements for Renderer Plugins:
---------------------------------
Each renderer MUST define:

    model_type = <ModelClass>

    @staticmethod
    def create_item(element, controller)

Example:
--------
class BusRenderer:
    model_type = Bus

    @staticmethod
    def create_item(bus, controller):
        return BusItem(bus)
"""

import os
import importlib
import inspect


def load_renderers(registry, package="ui.renderers"):
    """
    Discover and register all renderer plugins.

    Parameters:
    -----------
    registry : RendererRegistry
        The registry instance to populate

    package : str
        Python package path to scan
    """

    package_path = package.replace(".", "/")

    if not os.path.isdir(package_path):
        print(f"[RendererLoader] Package path not found: {package_path}")
        return

    # ----------------------------------------------------------
    # Scan all Python files in renderers directory
    # ----------------------------------------------------------
    for filename in os.listdir(package_path):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        module_name = filename[:-3]
        full_module = f"{package}.{module_name}"

        try:
            module = importlib.import_module(full_module)
        except Exception as e:
            print(f"[RendererLoader] Failed to import {full_module}: {e}")
            continue

        # ------------------------------------------------------
        # Inspect module for renderer classes
        # ------------------------------------------------------
        for _, obj in inspect.getmembers(module, inspect.isclass):

            # Ensure class is defined in this module
            if obj.__module__ != full_module:
                continue

            # Must have model_type attribute
            model_type = getattr(obj, "model_type", None)

            # Must implement create_item
            has_method = hasattr(obj, "create_item")

            if model_type and has_method:
                registry.register(model_type, obj)
                print(f"[RendererLoader] Loaded: {obj.__name__}")
