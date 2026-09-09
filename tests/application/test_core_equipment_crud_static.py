"""Static/source-level coverage for the four remaining Core equipment lifecycles.

Runtime execution is intentionally deferred for this remediation. These tests
therefore inspect source structure and contracts without importing the
Application runtime.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).parents[2]
APPLICATION = ROOT / "core" / "application"
SERVICES = APPLICATION / "services"
COMMANDS = APPLICATION / "commands"

EQUIPMENT = {
    "synchronous_machine": {
        "service_class": "SynchronousMachineModelService",
        "service_file": SERVICES / "synchronous_machine_model_service.py",
        "command_file": COMMANDS / "synchronous_machine_commands.py",
        "commands": (
            "CREATE_SYNCHRONOUS_MACHINE",
            "UPDATE_SYNCHRONOUS_MACHINE",
            "DELETE_SYNCHRONOUS_MACHINE",
        ),
        "command_classes": (
            "CreateSynchronousMachineCommand",
            "UpdateSynchronousMachineCommand",
            "DeleteSynchronousMachineCommand",
        ),
        "handlers": (
            "create_synchronous_machine",
            "update_synchronous_machine",
            "delete_synchronous_machine",
        ),
        "network_add": "add_synchronous_machine",
        "network_remove": "remove_synchronous_machine",
    },
    "motor": {
        "service_class": "MotorModelService",
        "service_file": SERVICES / "motor_model_service.py",
        "command_file": COMMANDS / "motor_commands.py",
        "commands": ("CREATE_MOTOR", "UPDATE_MOTOR", "DELETE_MOTOR"),
        "command_classes": ("CreateMotorCommand", "UpdateMotorCommand", "DeleteMotorCommand"),
        "handlers": ("create_motor", "update_motor", "delete_motor"),
        "network_add": "add_motor",
        "network_remove": "remove_motor",
    },
    "reactor": {
        "service_class": "ReactorModelService",
        "service_file": SERVICES / "reactor_model_service.py",
        "command_file": COMMANDS / "reactor_commands.py",
        "commands": ("CREATE_REACTOR", "UPDATE_REACTOR", "DELETE_REACTOR"),
        "command_classes": ("CreateReactorCommand", "UpdateReactorCommand", "DeleteReactorCommand"),
        "handlers": ("create_reactor", "update_reactor", "delete_reactor"),
        "network_add": "add_reactor",
        "network_remove": "remove_reactor",
    },
    "solar": {
        "service_class": "SolarModelService",
        "service_file": SERVICES / "solar_model_service.py",
        "command_file": COMMANDS / "solar_commands.py",
        "commands": ("CREATE_SOLAR", "UPDATE_SOLAR", "DELETE_SOLAR"),
        "command_classes": ("CreateSolarCommand", "UpdateSolarCommand", "DeleteSolarCommand"),
        "handlers": ("create_solar", "update_solar", "delete_solar"),
        "network_add": "add_solar",
        "network_remove": "remove_solar",
    },
}


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _class_names(path: Path) -> set[str]:
    return {node.name for node in ast.walk(_tree(path)) if isinstance(node, ast.ClassDef)}


def _function_names(path: Path) -> set[str]:
    return {node.name for node in ast.walk(_tree(path)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_four_dedicated_services_exist_with_canonical_crud_methods():
    for spec in EQUIPMENT.values():
        assert spec["service_file"].is_file()
        assert spec["service_class"] in _class_names(spec["service_file"])
        functions = _function_names(spec["service_file"])
        assert set(spec["handlers"]) <= functions


def test_canonical_crud_commands_exist_and_are_application_value_contracts():
    for spec in EQUIPMENT.values():
        source = _source(spec["command_file"])
        classes = _class_names(spec["command_file"])
        assert set(spec["commands"]) <= set(ast_names(source))
        assert set(spec["command_classes"]) <= classes
        assert "from ..command import Command" in source
        assert "from core.model" not in source


def test_endpoint_bearing_create_commands_use_endpoint_reference():
    for name in ("synchronous_machine", "motor", "reactor", "solar"):
        source = _source(EQUIPMENT[name]["command_file"])
        assert "from ..endpoint_reference import EndpointReference" in source
        assert "endpoint: EndpointReference | None" in source


def test_all_four_command_families_are_registered_with_matching_handlers():
    source = _source(APPLICATION / "command_handlers.py")
    functions = _function_names(APPLICATION / "command_handlers.py")
    for spec in EQUIPMENT.values():
        assert set(spec["handlers"]) <= functions
        for command_constant in spec["commands"]:
            assert command_constant in source
        for handler in spec["handlers"]:
            assert f"def {handler}(" in source


def test_endpoint_bearing_handlers_delegate_through_canonical_resolver():
    source = _source(APPLICATION / "command_handlers.py")
    for name in EQUIPMENT:
        handler = f"create_{name}"
        assert f"def {handler}(" in source
        start = source.index(f"def {handler}(")
        end = source.find("\n    def ", start + 1)
        section = source[start:] if end == -1 else source[start:end]
        assert "self._resolve(dict(command.payload), context, \"endpoint\")" in section
        assert f"self._model_service.create_{name}" in section


def test_services_use_existing_network_add_remove_and_registry_lookup_boundaries():
    for name, spec in EQUIPMENT.items():
        source = _source(spec["service_file"])
        assert f"self._network.{spec['network_add']}" in source
        assert f"self._network.{spec['network_remove']}" in source
        assert f'"{name}"' in source
        assert "self._get_required" in source


def test_model_service_is_a_delegating_compatibility_facade():
    source = _source(SERVICES / "model_service.py")
    classes = _class_names(SERVICES / "model_service.py")
    assert classes == {"ModelService"}
    for name in EQUIPMENT:
        assert f"self._{name}_service" in source
        assert f"def create_{name}(" in source
        assert f"def update_{name}(" in source
        assert f"def delete_{name}(" in source
        assert f"self._{name}_service.create_{name}" in source
        assert f"self._{name}_service.update_{name}" in source
        assert f"self._{name}_service.delete_{name}" in source


def test_no_generic_branch_lifecycle_or_duplicate_model_service_exists():
    model_commands = _source(COMMANDS / "model_commands.py")
    handlers = _source(APPLICATION / "command_handlers.py")
    application = _source(APPLICATION / "application.py")
    assert "CREATE_BRANCH" not in model_commands
    assert "UPDATE_BRANCH" not in model_commands
    assert "DELETE_BRANCH" not in model_commands
    assert "def create_branch(" not in handlers
    assert "def update_branch(" not in handlers
    assert "def delete_branch(" not in handlers
    assert "model.create_branch" not in application
    assert "model.update_branch" not in application
    assert "model.delete_branch" not in application

    model_service_classes = []
    for path in SERVICES.glob("*_service.py"):
        model_service_classes.extend(
            node.name
            for node in ast.walk(_tree(path))
            if isinstance(node, ast.ClassDef) and node.name == "ModelService"
        )
    assert model_service_classes == ["ModelService"]


def ast_names(source: str) -> set[str]:
    """Return names assigned by top-level/import/class/function definitions."""
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names
