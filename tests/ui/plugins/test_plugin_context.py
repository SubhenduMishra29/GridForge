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
