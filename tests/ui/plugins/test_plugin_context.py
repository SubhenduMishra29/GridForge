"""
GridForge V2
============

File:
    tests/ui/plugins/test_plugin_context.py

Purpose
-------
Contract tests for:
    ui.plugins.plugin_context.PluginContext

Architectural contract
----------------------
- PC-001: PluginContext is dependency-only.
- PC-002: project_controller is the authoritative controller boundary.
- PC-003: PluginContext does not expose plugin lifecycle infrastructure.
"""

from dataclasses import fields

from ui.plugins.plugin_context import PluginContext


def test_plugin_context_has_no_legacy_command_manager_dependency() -> None:
    field_names = {item.name for item in fields(PluginContext)}

    assert "command_manager" not in field_names
