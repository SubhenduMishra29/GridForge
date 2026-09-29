"""
GridForge V2 shell composition handoff contract.
"""

import inspect

from main import _build_application_impl


def test_application_bootstrap_hands_composed_surfaces_to_shell_before_workspace_activation():
    source = inspect.getsource(_build_application_impl)
    assert "set_composition" in source
    assert "set_workspace_surface" in source
    assert "ControlSurfaceHost" in source
    assert source.index("set_composition") < source.index("workspace_controller")
