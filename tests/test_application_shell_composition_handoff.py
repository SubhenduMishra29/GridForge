"""
GridForge V2
===========

File:
    tests/test_application_shell_composition_handoff.py

Purpose:
    Define the application-bootstrap ownership contract for the final Shell
    widget composition handoff.

Author:
    Subhendu Mishra
"""

import inspect

from main import build_application


def test_application_bootstrap_hands_widgets_to_shell_before_initialization() -> None:
    """Bootstrap must bind existing widgets before Shell initialization."""
    source = inspect.getsource(build_application)

    assert "set_composition" in source
    assert "canvas_widget" in source
    assert "toolbar_widget" in source
    assert "status_widget" in source
    assert source.index("set_composition") < source.index("initialize_all")
