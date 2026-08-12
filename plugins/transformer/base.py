```python
# plugins/transformer/base.py

"""
GridForge Transformer Plugin Base
=================================

GridForge Plugin Layer

Defines the common base contract for transformer-specific plugins.

Architecture
------------
The GridForge core model contains the stable transformer equipment
representation:

    core/model/transformer.py

Transformer-specific engineering capabilities are implemented under:

    plugins/transformer/

The plugin layer extends the capabilities of the core Transformer
without replacing or modifying its fundamental equipment identity.

Dependency Direction
--------------------
Plugin dependencies must flow toward the core:

    plugins/transformer
            │
            ▼
    core/model/transformer

The core model must remain independent of this plugin package.

Transformer Plugin Responsibilities
------------------------------------
A transformer plugin may provide:

    - Specialized physical parameters.
    - Engineering configuration.
    - Additional transformer capabilities.
    - Capability-specific validation.
    - Capability-specific diagnostic information.
    - Interfaces consumed by network, solver, analysis,
      protection, dynamics, or simulation layers.

A transformer plugin must NOT:

    - Replace the core Transformer object.
    - Own global network topology.
    - Build Y-bus matrices.
    - Perform load-flow calculations.
    - Perform short-circuit calculations.
    - Execute protection logic.
    - Execute global control loops.
    - Own GUI state.
    - Store authoritative global network state.
    - Duplicate the identity or topology of the core Transformer.

Core Model Ownership
--------------------
The core Transformer remains authoritative for:

    - Object identity.
    - Equipment identity.
    - Terminal connectivity.
    - Core branch impedance.
    - Core branch tap interface.
    - Core branch phase-shift interface.
    - Equipment rating.
    - In-service state.

Plugins provide additional capabilities around that authoritative
equipment object.

Plugin Lifecycle
----------------
The base plugin defines a deliberately small lifecycle:

    attach()
        Validate and attach the capability.

    detach()
        Remove the plugin capability association.

    validate()
        Validate plugin-specific configuration.

    summary()
        Return plugin-specific diagnostic information.

The base class does not automatically register itself with a global
plugin registry. Registry integration belongs to the GridForge plugin
system.

Design Principle
----------------
GridForge uses capability-oriented plugin architecture:

    Core Transformer
          │
          ├── Winding capability
          ├── Vector-group capability
          ├── Grounding capability
          ├── Tap-changer capability
          └── Equivalent-model capability

rather than a monolithic Transformer model.

This allows the transformer domain to evolve without continuously
modifying the frozen core model.

GridForge V2 Status
-------------------
This module establishes the common transformer-plugin contract.

The interface is intentionally minimal.

New common lifecycle methods should only be introduced when a real
plugin requirement demonstrates the need.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


# =====================================================================
# TRANSFORMER PLUGIN BASE
# =====================================================================

class TransformerPlugin(ABC):
    """
    Base class for GridForge transformer plugins.

    A TransformerPlugin represents one specialized capability associated
    with a core GridForge Transformer.

    The plugin extends the transformer domain without becoming the
    authoritative equipment object.

    Parameters
    ----------
    transformer :
        Core GridForge Transformer instance.

    name : str, optional
        Human-readable plugin name.

    Notes
    -----
    The plugin does not replace or subclass the core Transformer.

    The core Transformer remains the authoritative equipment object.
    """

    plugin_type = "transformer"

    def __init__(
        self,
        transformer,
        name: str = "",
    ):
        if transformer is None:
            raise ValueError(
                "Transformer plugin requires a Transformer instance."
            )

        self.transformer = transformer
        self.name = str(name)

        self._attached = False

    # =================================================================
    # LIFECYCLE
    # =================================================================

    def attach(self) -> None:
        """
        Attach the plugin capability to the Transformer.

        Validation is performed before the plugin becomes attached.

        The method does not modify global network state.
        """

        if self._attached:
            return

        self.validate()
        self._attached = True

    def detach(self) -> None:
        """
        Detach the plugin capability from the Transformer.

        The core Transformer remains unchanged.
        """

        self._attached = False

    # =================================================================
    # STATUS
    # =================================================================

    @property
    def is_attached(self) -> bool:
        """
        Return True when the plugin is currently attached.
        """

        return self._attached

    # =================================================================
    # VALIDATION
    # =================================================================

    @abstractmethod
    def validate(self) -> None:
        """
        Validate plugin-specific configuration.

        Implementations must raise ``ValueError`` when their
        configuration is invalid.

        Validation should remain local to the plugin capability.
        """

        raise NotImplementedError

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return common plugin diagnostic information.

        Specialized transformer plugins may extend this dictionary.
        """

        return {
            "plugin_type": self.plugin_type,
            "plugin": self.__class__.__name__,
            "name": self.name,
            "transformer_id": self.transformer.id,
            "attached": self.is_attached,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<{self.__class__.__name__} "
            f"transformer={self.transformer.id}, "
            f"attached={self.is_attached}>"
        )
```
