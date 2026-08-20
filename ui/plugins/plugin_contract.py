"""
GridForge V2
============

File:
    ui/plugins/plugin_contract.py

Author:
    Subhendu Mishra

Purpose
-------
Canonical contract for GridForge UI composition plugins.

Architectural role
------------------
The plugin contract defines the minimum behavioral interface that every
GridForge UI composition plugin must satisfy.

The contract is intentionally small.

It defines:

    - plugin identity;
    - dependency declaration;
    - lifecycle entry points;
    - optional lifecycle capability hooks.

It does NOT:

    - construct plugins;
    - discover plugins;
    - resolve dependencies;
    - determine lifecycle ordering;
    - store runtime lifecycle state;
    - create PluginContext objects;
    - create Qt objects;
    - own application state;
    - own Core/domain state;
    - perform UI composition orchestration.

Lifecycle ownership
-------------------
PluginManager
    Determines WHAT happens and WHEN.

PluginRegistry
    Executes lifecycle operations against plugin instances.

PluginStateStore
    Records canonical runtime lifecycle state.

PluginContext
    Supplies already-created dependencies during initialization.

Plugin
    Implements the actual plugin lifecycle behavior.

Architectural rules
-------------------
- Plugins are explicitly constructed by PluginLoader.
- Plugins are registered by PluginRegistry.
- Plugin lifecycle is executed by PluginRegistry.
- Runtime state is recorded by PluginStateStore.
- Dependency ordering is determined by PluginManager.
- PluginContext is supplied only during initialization.
- Plugin construction must be context-free.
- Plugins must not construct their own application services.
- Plugins must not discover other plugins.
- Plugins must not manipulate PluginStateStore directly.
- Plugins must not perform dependency resolution.
- Plugins must not own application/domain state.
- Plugins must not perform electrical calculations.
- Qt access remains behind ui.core.qt.
- SLD/canvas functionality remains a first-class current capability.
"""

from __future__ import annotations

from typing import (
    Any,
    Protocol,
    runtime_checkable,
)


# ============================================================
# PLUGIN CONTRACT
# ============================================================


@runtime_checkable
class Plugin(Protocol):
    """
    Canonical behavioral contract for a GridForge UI plugin.

    A plugin instance is constructed without a PluginContext.

    The PluginContext is supplied later by PluginRegistry during
    initialization.

    Required lifecycle
    ------------------
    initialize(context)
        Start the plugin using the supplied dependency context.

    shutdown()
        Release resources created during initialization.

    Optional capability
    -------------------
    The contract deliberately does not require a separate enable()
    or disable() lifecycle method.

    Enablement is runtime state controlled by PluginRegistry and
    PluginStateStore.

    A plugin is therefore either:

        registered + enabled + initialized

    or not initialized.

    Plugin identity
    ---------------
    ``plugin_id`` is the canonical stable identifier used by:

        PluginLoader
        PluginRegistry
        PluginStateStore
        PluginManager

    The identifier must be a non-empty string.
    """

    @property
    def plugin_id(self) -> str:
        """
        Return the canonical stable plugin identifier.
        """
        ...

    def initialize(
        self,
        context: Any,
    ) -> Any:
        """
        Initialize the plugin using an already-created context.

        The plugin may create its own internal UI objects here, but
        dependencies must be obtained from the supplied PluginContext
        rather than constructed or discovered by the plugin.

        Parameters
        ----------
        context:
            PluginContext supplied by the application composition layer.

        Returns
        -------
        Any
            Plugin-specific initialization result.

        Raises
        ------
        Exception
            Any lifecycle failure is propagated to PluginRegistry.
        """
        ...

    def shutdown(
        self,
    ) -> Any:
        """
        Shut down the plugin.

        Shutdown must release resources acquired during initialization.

        It must not:

            - modify PluginStateStore directly;
            - perform dependency ordering;
            - shut down other plugins;
            - construct replacement dependencies.

        Returns
        -------
        Any
            Plugin-specific shutdown result.

        Raises
        ------
        Exception
            Any lifecycle failure is propagated to PluginRegistry.
        """
        ...


# ============================================================
# CONTRACT VALIDATION
# ============================================================


def validate_plugin(
    plugin: Any,
    *,
    plugin_id: str | None = None,
) -> None:
    """
    Validate that an object satisfies the GridForge plugin contract.

    Validation is intentionally structural rather than dependent on
    concrete plugin inheritance.

    This permits composition plugins to remain lightweight and avoids
    coupling the plugin subsystem to a common implementation base class.

    Parameters
    ----------
    plugin:
        Plugin instance to validate.

    plugin_id:
        Optional expected plugin identifier.

        When supplied, the plugin's ``plugin_id`` must exactly match it.

    Raises
    ------
    TypeError
        If the object does not satisfy the contract.

    ValueError
        If the plugin identifier is invalid or does not match the
        expected identifier.
    """

    if plugin is None:
        raise TypeError(
            "plugin cannot be None."
        )

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    if not hasattr(
        plugin,
        "plugin_id",
    ):
        raise TypeError(
            "Plugin must define a 'plugin_id' property."
        )

    try:
        actual_plugin_id = plugin.plugin_id
    except Exception as exc:
        raise TypeError(
            "Plugin 'plugin_id' could not be accessed."
        ) from exc

    if not isinstance(
        actual_plugin_id,
        str,
    ):
        raise TypeError(
            "plugin_id must be a string."
        )

    if not actual_plugin_id.strip():
        raise ValueError(
            "plugin_id must be a non-empty string."
        )

    # --------------------------------------------------------
    # Expected identity
    # --------------------------------------------------------

    if plugin_id is not None:
        if not isinstance(
            plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        if not plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if actual_plugin_id != plugin_id:
            raise ValueError(
                (
                    "Plugin identifier mismatch: "
                    f"expected {plugin_id!r}, "
                    f"got {actual_plugin_id!r}."
                )
            )

    # --------------------------------------------------------
    # Lifecycle methods
    # --------------------------------------------------------

    initialize = getattr(
        plugin,
        "initialize",
        None,
    )

    if not callable(
        initialize
    ):
        raise TypeError(
            (
                f"Plugin {actual_plugin_id!r} "
                "must define callable initialize()."
            )
        )

    shutdown = getattr(
        plugin,
        "shutdown",
        None,
    )

    if not callable(
        shutdown
    ):
        raise TypeError(
            (
                f"Plugin {actual_plugin_id!r} "
                "must define callable shutdown()."
            )
        )


# ============================================================
# OPTIONAL CONTRACT HELPERS
# ============================================================


def plugin_id_of(
    plugin: Plugin,
) -> str:
    """
    Return the validated canonical plugin identifier.
    """

    validate_plugin(
        plugin
    )

    return plugin.plugin_id


def supports_plugin_contract(
    plugin: Any,
) -> bool:
    """
    Return whether an object structurally satisfies the plugin contract.

    This helper never executes lifecycle methods.
    """

    try:
        validate_plugin(
            plugin
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    return True


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "Plugin",
    "validate_plugin",
    "plugin_id_of",
    "supports_plugin_contract",
]
