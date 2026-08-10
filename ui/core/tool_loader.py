"""
Tool Loader (Auto-Discovery System)

Location:
---------
ui/core/tool_loader.py

Purpose:
--------
Automatically discovers and registers all tool plugins.

Each tool must define:
    tool_id = "unique_name"
    class ToolName:
        def mouse_press(...)
        def mouse_move(...)
        def mouse_release(...)
"""

import os
import importlib
import inspect


def load_tools(registry, controller, scene, package="ui.tools"):
    """
    Discover and register all tool plugins.

    Parameters:
    -----------
    registry : ToolRegistry
    controller : Controller
    scene : QGraphicsScene
    """

    package_path = package.replace(".", "/")

    if not os.path.isdir(package_path):
        print(f"[ToolLoader] Package not found: {package_path}")
        return

    for filename in os.listdir(package_path):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        module_name = filename[:-3]
        full_module = f"{package}.{module_name}"

        try:
            module = importlib.import_module(full_module)
        except Exception as e:
            print(f"[ToolLoader] Failed to import {full_module}: {e}")
            continue

        for _, obj in inspect.getmembers(module, inspect.isclass):

            if obj.__module__ != full_module:
                continue

            tool_id = getattr(obj, "tool_id", None)

            if not tool_id:
                continue

            try:
                # Instantiate tool with dependencies
                tool_instance = obj(controller, scene)

                registry.register(tool_id, tool_instance)

                print(f"[ToolLoader] Loaded: {tool_id}")

            except Exception as e:
                print(f"[ToolLoader] Failed to init {obj.__name__}: {e}")
