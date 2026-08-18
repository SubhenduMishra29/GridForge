"""
GridForge V2
============

File:
    tests/ui/plugins/test_plugin_loader.py

Purpose
-------
Comprehensive tests for ui.plugins.plugin_loader.

Coverage
--------
- PluginImplementation validation
- LoadedPlugin validation
- canonical default definitions
- compatibility mappings
- loader definition management
- explicit loading and resolution
- load idempotency
- load_many / load_all ordering
- class construction
- factory construction
- contract validation
- PluginContext rejection
- create_many argument separation
- query methods
- forget / clear semantics
- validation and failure paths

Architectural constraints tested
---------------------------------
PluginLoader:
    - does explicit loading only;
    - performs no discovery;
    - does not perform lifecycle operations;
    - does not create PluginContext;
    - does not register plugins;
    - does not perform dependency ordering.
"""

from __future__ import annotations

import sys
import types

import pytest

from ui.plugins.plugin_loader import (
    DEFAULT_PLUGIN_CLASSES,
    DEFAULT_PLUGIN_FACTORIES,
    DEFAULT_PLUGIN_IMPLEMENTATIONS,
    DEFAULT_PLUGIN_MODULES,
    LoadedPlugin,
    PluginImplementation,
    PluginLoader,
    create_default_plugin_loader,
    load_default_plugins,
)


# ============================================================
# TEST HELPERS
# ============================================================


def make_class_module(
    monkeypatch,
    module_name: str,
    class_name: str = "TestPlugin",
):
    module = types.ModuleType(module_name)

    class TestPlugin:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def initialize(self, context):
            return None

        def shutdown(self):
            return None

    TestPlugin.__name__ = class_name

    setattr(
        module,
        class_name,
        TestPlugin,
    )

    monkeypatch.setitem(
        sys.modules,
        module_name,
        module,
    )

    return module, TestPlugin


def make_factory_module(
    monkeypatch,
    module_name: str,
    factory_name: str = "create_plugin",
):
    module = types.ModuleType(module_name)

    class TestPlugin:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def initialize(self, context):
            return None

        def shutdown(self):
            return None

    def factory(*args, **kwargs):
        return TestPlugin(
            *args,
            **kwargs,
        )

    setattr(
        module,
        factory_name,
        factory,
    )

    monkeypatch.setitem(
        sys.modules,
        module_name,
        module,
    )

    return module, factory, TestPlugin


def class_definition(
    plugin_id: str = "test",
    module_name: str = "test_plugin_module",
    class_name: str = "TestPlugin",
):
    return PluginImplementation(
        plugin_id=plugin_id,
        module_name=module_name,
        class_name=class_name,
    )


def factory_definition(
    plugin_id: str = "test",
    module_name: str = "test_plugin_module",
    factory_name: str = "create_plugin",
):
    return PluginImplementation(
        plugin_id=plugin_id,
        module_name=module_name,
        factory_name=factory_name,
    )


# ============================================================
# PluginImplementation
# ============================================================


def test_plugin_implementation_accepts_class():
    definition = class_definition()

    assert definition.plugin_id == "test"
    assert definition.module_name == "test_plugin_module"
    assert definition.class_name == "TestPlugin"
    assert definition.factory_name is None


def test_plugin_implementation_accepts_factory():
    definition = factory_definition()

    assert definition.class_name is None
    assert definition.factory_name == "create_plugin"


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "plugin_id": "",
            "module_name": "test.module",
            "class_name": "TestPlugin",
        },
        {
            "plugin_id": "   ",
            "module_name": "test.module",
            "class_name": "TestPlugin",
        },
    ],
)
def test_plugin_implementation_rejects_empty_plugin_id(
    kwargs,
):
    with pytest.raises(ValueError):
        PluginImplementation(**kwargs)


def test_plugin_implementation_rejects_non_string_plugin_id():
    with pytest.raises(ValueError):
        PluginImplementation(
            plugin_id=123,
            module_name="test.module",
            class_name="TestPlugin",
        )


def test_plugin_implementation_rejects_non_string_module_name():
    with pytest.raises(TypeError):
        PluginImplementation(
            plugin_id="test",
            module_name=123,
            class_name="TestPlugin",
        )


@pytest.mark.parametrize(
    "module_name",
    [
        "",
        " ",
        ".test",
        "test.",
        "test..module",
        "test-module",
        "test.module-name",
        "123module",
    ],
)
def test_plugin_implementation_rejects_invalid_module_name(
    module_name,
):
    with pytest.raises((TypeError, ValueError)):
        PluginImplementation(
            plugin_id="test",
            module_name=module_name,
            class_name="TestPlugin",
        )


def test_plugin_implementation_rejects_non_string_class_name():
    with pytest.raises(TypeError):
        PluginImplementation(
            plugin_id="test",
            module_name="test.module",
            class_name=123,
        )


@pytest.mark.parametrize(
    "class_name",
    [
        "",
        " ",
    ],
)
def test_plugin_implementation_rejects_empty_class_name(
    class_name,
):
    with pytest.raises(ValueError):
        PluginImplementation(
            plugin_id="test",
            module_name="test.module",
            class_name=class_name,
        )


def test_plugin_implementation_rejects_non_string_factory_name():
    with pytest.raises(TypeError):
        PluginImplementation(
            plugin_id="test",
            module_name="test.module",
            factory_name=123,
        )


@pytest.mark.parametrize(
    "factory_name",
    [
        "",
        " ",
    ],
)
def test_plugin_implementation_rejects_empty_factory_name(
    factory_name,
):
    with pytest.raises(ValueError):
        PluginImplementation(
            plugin_id="test",
            module_name="test.module",
            factory_name=factory_name,
        )


def test_plugin_implementation_requires_construction_mechanism():
    with pytest.raises(ValueError):
        PluginImplementation(
            plugin_id="test",
            module_name="test.module",
        )


def test_plugin_implementation_rejects_both_class_and_factory():
    with pytest.raises(ValueError):
        PluginImplementation(
            plugin_id="test",
            module_name="test.module",
            class_name="TestPlugin",
            factory_name="create_plugin",
        )


# ============================================================
# LoadedPlugin
# ============================================================


def test_loaded_plugin_accepts_class_descriptor():
    descriptor = LoadedPlugin(
        plugin_id="test",
        module_name="test.module",
        plugin_class=dict,
    )

    assert descriptor.plugin_id == "test"
    assert descriptor.plugin_class is dict
    assert descriptor.factory is None


def test_loaded_plugin_accepts_factory_descriptor():
    def factory():
        return object()

    descriptor = LoadedPlugin(
        plugin_id="test",
        module_name="test.module",
        factory=factory,
    )

    assert descriptor.factory is factory
    assert descriptor.plugin_class is None


def test_loaded_plugin_rejects_empty_plugin_id():
    with pytest.raises(ValueError):
        LoadedPlugin(
            plugin_id="",
            module_name="test.module",
            plugin_class=dict,
        )


def test_loaded_plugin_rejects_invalid_module_name():
    with pytest.raises(ValueError):
        LoadedPlugin(
            plugin_id="test",
            module_name="bad-module",
            plugin_class=dict,
        )


def test_loaded_plugin_rejects_non_class_plugin_class():
    with pytest.raises(TypeError):
        LoadedPlugin(
            plugin_id="test",
            module_name="test.module",
            plugin_class="not-a-class",
        )


def test_loaded_plugin_rejects_non_callable_factory():
    with pytest.raises(TypeError):
        LoadedPlugin(
            plugin_id="test",
            module_name="test.module",
            factory="not-callable",
        )


def test_loaded_plugin_requires_class_or_factory():
    with pytest.raises(ValueError):
        LoadedPlugin(
            plugin_id="test",
            module_name="test.module",
        )


def test_loaded_plugin_rejects_class_and_factory_together():
    with pytest.raises(ValueError):
        LoadedPlugin(
            plugin_id="test",
            module_name="test.module",
            plugin_class=dict,
            factory=dict,
        )


# ============================================================
# DEFAULT DEFINITIONS
# ============================================================


def test_default_plugin_implementations_are_canonical():
    assert tuple(
        DEFAULT_PLUGIN_IMPLEMENTATIONS.keys()
    ) == (
        "canvas",
        "panels",
        "toolbar",
        "status",
        "shell",
    )


def test_default_plugin_modules_match_definitions():
    assert DEFAULT_PLUGIN_MODULES == {
        plugin_id: definition.module_name
        for plugin_id, definition
        in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
    }


def test_default_plugin_classes_match_definitions():
    assert DEFAULT_PLUGIN_CLASSES == {
        plugin_id: definition.class_name
        for plugin_id, definition
        in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
        if definition.class_name is not None
    }


def test_default_plugin_factories_match_definitions():
    assert DEFAULT_PLUGIN_FACTORIES == {
        plugin_id: definition.factory_name
        for plugin_id, definition
        in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
        if definition.factory_name is not None
    }


def test_default_plugins_use_explicit_class_resolution():
    for definition in DEFAULT_PLUGIN_IMPLEMENTATIONS.values():
        assert definition.class_name is not None
        assert definition.factory_name is None


# ============================================================
# PluginLoader INITIALIZATION
# ============================================================


def test_loader_uses_default_definitions():
    loader = PluginLoader()

    assert tuple(
        loader.definitions.keys()
    ) == (
        "canvas",
        "panels",
        "toolbar",
        "status",
        "shell",
    )


def test_loader_accepts_custom_definitions():
    definition = class_definition()

    loader = PluginLoader(
        definitions={
            "test": definition,
        }
    )

    assert loader.definitions == {
        "test": definition,
    }


def test_loader_rejects_non_mapping_definitions():
    with pytest.raises(TypeError):
        PluginLoader(
            definitions=[],
        )


def test_loader_rejects_non_string_definition_key():
    definition = class_definition()

    with pytest.raises(TypeError):
        PluginLoader(
            definitions={
                123: definition,
            }
        )


def test_loader_rejects_non_definition_value():
    with pytest.raises(TypeError):
        PluginLoader(
            definitions={
                "test": object(),
            }
        )


def test_loader_rejects_mismatched_definition_key():
    definition = class_definition(
        plugin_id="actual",
    )

    with pytest.raises(ValueError):
        PluginLoader(
            definitions={
                "different": definition,
            }
        )


# ============================================================
# DEFINE / REMOVE
# ============================================================


def test_define_adds_explicit_definition():
    loader = PluginLoader(
        definitions={}
    )

    definition = class_definition()

    loader.define(
        definition
    )

    assert loader.definitions["test"] is definition


def test_define_rejects_duplicate_definition():
    loader = PluginLoader(
        definitions={}
    )

    definition = class_definition()

    loader.define(
        definition
    )

    with pytest.raises(ValueError):
        loader.define(
            definition
        )


def test_define_rejects_invalid_definition():
    loader = PluginLoader(
        definitions={}
    )

    with pytest.raises(TypeError):
        loader.define(
            object()
        )


def test_remove_definition():
    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    loader.remove_definition(
        "test"
    )

    assert "test" not in loader.definitions


def test_remove_definition_is_idempotent():
    loader = PluginLoader(
        definitions={}
    )

    loader.remove_definition(
        "test"
    )


def test_remove_definition_rejects_loaded_plugin(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    loader.load(
        "test"
    )

    with pytest.raises(RuntimeError):
        loader.remove_definition(
            "test"
        )


# ============================================================
# LOAD
# ============================================================


def test_load_imports_and_resolves_explicit_class(
    monkeypatch,
):
    _, plugin_class = make_class_module(
        monkeypatch,
        "test_plugin_module",
        "TestPlugin",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    descriptor = loader.load(
        "test"
    )

    assert descriptor.plugin_id == "test"
    assert descriptor.module_name == "test_plugin_module"
    assert descriptor.plugin_class is plugin_class
    assert descriptor.factory is None


def test_load_does_not_construct_plugin(
    monkeypatch,
):
    _, plugin_class = make_class_module(
        monkeypatch,
        "test_plugin_module",
        "TestPlugin",
    )

    class TrackingPlugin(plugin_class):
        constructed = False

        def __init__(self, *args, **kwargs):
            type(self).constructed = True
            super().__init__(
                *args,
                **kwargs,
            )

    module = sys.modules[
        "test_plugin_module"
    ]

    module.TestPlugin = TrackingPlugin

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    loader.load(
        "test"
    )

    assert TrackingPlugin.constructed is False


def test_load_is_idempotent(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    first = loader.load(
        "test"
    )

    second = loader.load(
        "test"
    )

    assert second is first
    assert loader.loaded_ids == ("test",)


def test_load_unknown_plugin_raises_key_error():
    loader = PluginLoader(
        definitions={}
    )

    with pytest.raises(KeyError):
        loader.load(
            "missing"
        )


def test_load_missing_class_raises_import_error(
    monkeypatch,
):
    module = types.ModuleType(
        "test_plugin_module"
    )

    monkeypatch.setitem(
        sys.modules,
        "test_plugin_module",
        module,
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    with pytest.raises(ImportError):
        loader.load(
            "test"
        )


def test_load_rejects_resolved_non_class(
    monkeypatch,
):
    module = types.ModuleType(
        "test_plugin_module"
    )

    module.TestPlugin = "not-a-class"

    monkeypatch.setitem(
        sys.modules,
        "test_plugin_module",
        module,
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    with pytest.raises(TypeError):
        loader.load(
            "test"
        )


# ============================================================
# FACTORY RESOLUTION
# ============================================================


def test_load_resolves_explicit_factory(
    monkeypatch,
):
    _, factory, _ = make_factory_module(
        monkeypatch,
        "factory_plugin_module",
        "create_plugin",
    )

    loader = PluginLoader(
        definitions={
            "test": factory_definition(
                module_name="factory_plugin_module",
            ),
        }
    )

    descriptor = loader.load(
        "test"
    )

    assert descriptor.factory is factory
    assert descriptor.plugin_class is None


def test_load_missing_factory_raises_import_error(
    monkeypatch,
):
    module = types.ModuleType(
        "factory_plugin_module"
    )

    monkeypatch.setitem(
        sys.modules,
        "factory_plugin_module",
        module,
    )

    loader = PluginLoader(
        definitions={
            "test": factory_definition(
                module_name="factory_plugin_module",
            ),
        }
    )

    with pytest.raises(ImportError):
        loader.load(
            "test"
        )


def test_load_rejects_non_callable_factory(
    monkeypatch,
):
    module = types.ModuleType(
        "factory_plugin_module"
    )

    module.create_plugin = "not-callable"

    monkeypatch.setitem(
        sys.modules,
        "factory_plugin_module",
        module,
    )

    loader = PluginLoader(
        definitions={
            "test": factory_definition(
                module_name="factory_plugin_module",
            ),
        }
    )

    with pytest.raises(TypeError):
        loader.load(
            "test"
        )


# ============================================================
# LOAD MANY / LOAD ALL
# ============================================================


def test_load_many_preserves_input_order(
    monkeypatch,
):
    for module_name in (
        "a_module",
        "b_module",
        "c_module",
    ):
        make_class_module(
            monkeypatch,
            module_name,
        )

    definitions = {
        "a": class_definition(
            plugin_id="a",
            module_name="a_module",
        ),
        "b": class_definition(
            plugin_id="b",
            module_name="b_module",
        ),
        "c": class_definition(
            plugin_id="c",
            module_name="c_module",
        ),
    }

    loader = PluginLoader(
        definitions=definitions
    )

    result = loader.load_many(
        ["c", "a", "b"]
    )

    assert tuple(
        descriptor.plugin_id
        for descriptor in result
    ) == (
        "c",
        "a",
        "b",
    )


def test_load_all_preserves_definition_order(
    monkeypatch,
):
    for module_name in (
        "a_module",
        "b_module",
        "c_module",
    ):
        make_class_module(
            monkeypatch,
            module_name,
        )

    definitions = {
        "a": class_definition(
            plugin_id="a",
            module_name="a_module",
        ),
        "b": class_definition(
            plugin_id="b",
            module_name="b_module",
        ),
        "c": class_definition(
            plugin_id="c",
            module_name="c_module",
        ),
    }

    loader = PluginLoader(
        definitions=definitions
    )

    result = loader.load_all()

    assert tuple(
        descriptor.plugin_id
        for descriptor in result
    ) == (
        "a",
        "b",
        "c",
    )


# ============================================================
# CREATE
# ============================================================


def test_create_constructs_class_plugin(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    plugin = loader.create(
        "test",
        1,
        2,
        mode="test",
    )

    assert plugin.args == (1, 2)
    assert plugin.kwargs == {
        "mode": "test",
    }


def test_create_constructs_factory_plugin(
    monkeypatch,
):
    make_factory_module(
        monkeypatch,
        "factory_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": factory_definition(
                module_name="factory_plugin_module",
            ),
        }
    )

    plugin = loader.create(
        "test",
        10,
        enabled=True,
    )

    assert plugin.args == (10,)
    assert plugin.kwargs == {
        "enabled": True,
    }


def test_create_rejects_context_keyword(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    with pytest.raises(TypeError):
        loader.create(
            "test",
            context=object(),
        )


def test_create_validates_plugin_contract(
    monkeypatch,
):
    module = types.ModuleType(
        "test_plugin_module"
    )

    class InvalidPlugin:
        pass

    module.TestPlugin = InvalidPlugin

    monkeypatch.setitem(
        sys.modules,
        "test_plugin_module",
        module,
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    with pytest.raises(
        (TypeError, ValueError, AttributeError)
    ):
        loader.create(
            "test"
        )


def test_create_loads_before_constructing(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    assert loader.is_loaded(
        "test"
    ) is False

    loader.create(
        "test"
    )

    assert loader.is_loaded(
        "test"
    ) is True


# ============================================================
# CREATE MANY
# ============================================================


def test_create_many_uses_per_plugin_constructor_args(
    monkeypatch,
):
    for module_name in (
        "a_module",
        "b_module",
    ):
        make_class_module(
            monkeypatch,
            module_name,
        )

    loader = PluginLoader(
        definitions={
            "a": class_definition(
                plugin_id="a",
                module_name="a_module",
            ),
            "b": class_definition(
                plugin_id="b",
                module_name="b_module",
            ),
        }
    )

    plugins = loader.create_many(
        ["a", "b"],
        constructor_args={
            "a": (1,),
            "b": (2, 3),
        },
    )

    assert plugins[0].args == (1,)
    assert plugins[1].args == (2, 3)


def test_create_many_uses_per_plugin_constructor_kwargs(
    monkeypatch,
):
    for module_name in (
        "a_module",
        "b_module",
    ):
        make_class_module(
            monkeypatch,
            module_name,
        )

    loader = PluginLoader(
        definitions={
            "a": class_definition(
                plugin_id="a",
                module_name="a_module",
            ),
            "b": class_definition(
                plugin_id="b",
                module_name="b_module",
            ),
        }
    )

    plugins = loader.create_many(
        ["a", "b"],
        constructor_kwargs={
            "a": {"value": 1},
            "b": {"value": 2},
        },
    )

    assert plugins[0].kwargs == {
        "value": 1,
    }

    assert plugins[1].kwargs == {
        "value": 2,
    }


def test_create_many_preserves_plugin_order(
    monkeypatch,
):
    for module_name in (
        "a_module",
        "b_module",
        "c_module",
    ):
        make_class_module(
            monkeypatch,
            module_name,
        )

    loader = PluginLoader(
        definitions={
            "a": class_definition(
                plugin_id="a",
                module_name="a_module",
            ),
            "b": class_definition(
                plugin_id="b",
                module_name="b_module",
            ),
            "c": class_definition(
                plugin_id="c",
                module_name="c_module",
            ),
        }
    )

    plugins = loader.create_many(
        ["c", "a", "b"]
    )

    assert len(plugins) == 3


def test_create_many_rejects_non_mapping_constructor_args(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    with pytest.raises(TypeError):
        loader.create_many(
            ["test"],
            constructor_args=[],
        )


def test_create_many_rejects_non_mapping_constructor_kwargs(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    with pytest.raises(TypeError):
        loader.create_many(
            ["test"],
            constructor_kwargs=[],
        )


# ============================================================
# QUERY
# ============================================================


def test_is_loaded(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    assert loader.is_loaded(
        "test"
    ) is False

    loader.load(
        "test"
    )

    assert loader.is_loaded(
        "test"
    ) is True


def test_get_returns_descriptor(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    assert loader.get(
        "test"
    ) is None

    descriptor = loader.load(
        "test"
    )

    assert loader.get(
        "test"
    ) is descriptor


def test_require_returns_descriptor(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    descriptor = loader.load(
        "test"
    )

    assert loader.require(
        "test"
    ) is descriptor


def test_require_unknown_plugin_raises_key_error():
    loader = PluginLoader(
        definitions={}
    )

    with pytest.raises(KeyError):
        loader.require(
            "missing"
        )


def test_loaded_ids_preserve_load_order(
    monkeypatch,
):
    for module_name in (
        "a_module",
        "b_module",
    ):
        make_class_module(
            monkeypatch,
            module_name,
        )

    loader = PluginLoader(
        definitions={
            "a": class_definition(
                plugin_id="a",
                module_name="a_module",
            ),
            "b": class_definition(
                plugin_id="b",
                module_name="b_module",
            ),
        }
    )

    loader.load("b")
    loader.load("a")

    assert loader.loaded_ids == (
        "b",
        "a",
    )


# ============================================================
# FORGET / CLEAR
# ============================================================


def test_forget_removes_loaded_descriptor(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    descriptor = loader.load(
        "test"
    )

    forgotten = loader.forget(
        "test"
    )

    assert forgotten is descriptor
    assert loader.is_loaded(
        "test"
    ) is False


def test_forget_unknown_plugin_returns_none():
    loader = PluginLoader(
        definitions={}
    )

    assert loader.forget(
        "missing"
    ) is None


def test_forget_does_not_remove_definition(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    definition = class_definition()

    loader = PluginLoader(
        definitions={
            "test": definition,
        }
    )

    loader.load(
        "test"
    )

    loader.forget(
        "test"
    )

    assert loader.definitions[
        "test"
    ] is definition


def test_clear_forgets_all_loaded_descriptors(
    monkeypatch,
):
    for module_name in (
        "a_module",
        "b_module",
    ):
        make_class_module(
            monkeypatch,
            module_name,
        )

    loader = PluginLoader(
        definitions={
            "a": class_definition(
                plugin_id="a",
                module_name="a_module",
            ),
            "b": class_definition(
                plugin_id="b",
                module_name="b_module",
            ),
        }
    )

    loader.load_all()

    assert loader.loaded_ids == (
        "a",
        "b",
    )

    loader.clear()

    assert loader.loaded_ids == ()
    assert tuple(
        loader.definitions.keys()
    ) == (
        "a",
        "b",
    )


def test_clear_is_idempotent():
    loader = PluginLoader(
        definitions={}
    )

    loader.clear()
    loader.clear()

    assert loader.loaded_ids == ()


# ============================================================
# VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_loader_plugin_id_validation_rejects_non_string(
    value,
):
    loader = PluginLoader(
        definitions={}
    )

    with pytest.raises(TypeError):
        loader.is_loaded(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
    ],
)
def test_loader_plugin_id_validation_rejects_empty(
    value,
):
    loader = PluginLoader(
        definitions={}
    )

    with pytest.raises(ValueError):
        loader.is_loaded(value)


# ============================================================
# DEFAULT FACTORIES
# ============================================================


def test_create_default_plugin_loader_returns_loader():
    loader = create_default_plugin_loader()

    assert isinstance(
        loader,
        PluginLoader,
    )

    assert tuple(
        loader.definitions.keys()
    ) == (
        "canvas",
        "panels",
        "toolbar",
        "status",
        "shell",
    )


def test_load_default_plugins_resolves_all_canonical_plugins():
    loaded = load_default_plugins()

    assert tuple(
        descriptor.plugin_id
        for descriptor in loaded
    ) == (
        "canvas",
        "panels",
        "toolbar",
        "status",
        "shell",
    )

    assert all(
        descriptor.plugin_class is not None
        for descriptor in loaded
    )

    assert all(
        descriptor.factory is None
        for descriptor in loaded
    )


# ============================================================
# ARCHITECTURAL BOUNDARY TESTS
# ============================================================


def test_loader_does_not_create_context():
    loader = PluginLoader(
        definitions={}
    )

    assert not hasattr(
        loader,
        "context",
    )


def test_loader_does_not_expose_plugin_instances():
    loader = PluginLoader(
        definitions={}
    )

    assert not hasattr(
        loader,
        "instances",
    )


def test_loader_does_not_expose_registry():
    loader = PluginLoader(
        definitions={}
    )

    assert not hasattr(
        loader,
        "registry",
    )


def test_loader_does_not_expose_manager():
    loader = PluginLoader(
        definitions={}
    )

    assert not hasattr(
        loader,
        "manager",
    )


def test_loaded_descriptor_is_immutable(
    monkeypatch,
):
    make_class_module(
        monkeypatch,
        "test_plugin_module",
    )

    loader = PluginLoader(
        definitions={
            "test": class_definition(),
        }
    )

    descriptor = loader.load(
        "test"
    )

    with pytest.raises(
        AttributeError
    ):
        descriptor.plugin_id = "changed"


def test_plugin_implementation_is_immutable():
    definition = class_definition()

    with pytest.raises(
        AttributeError
    ):
        definition.plugin_id = "changed"


# ============================================================
# END
# ============================================================
