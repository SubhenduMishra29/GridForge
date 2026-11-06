from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.application.project import ProjectContext


def test_project_context_is_immutable_and_preserves_identity():
    context = ProjectContext(
        project_id="project-001",
        name="Test Project",
        path=Path("/tmp/test-project.gridforge"),
    )

    assert context.project_id == "project-001"
    assert context.name == "Test Project"
    assert context.path == Path("/tmp/test-project.gridforge")

    with pytest.raises(FrozenInstanceError):
        context.name = "Changed"  # type: ignore[misc]


def test_project_context_rejects_invalid_values():
    with pytest.raises(ValueError):
        ProjectContext(project_id="", name="Test", path=None)

    with pytest.raises(ValueError):
        ProjectContext(project_id="project-001", name="", path=None)


def test_project_context_identity_is_stable_when_values_are_equal():
    first = ProjectContext(project_id="project-001", name="Test", path=None)
    second = ProjectContext(project_id="project-001", name="Test", path=None)

    assert first == second
    assert first.project_id == second.project_id == "project-001"
