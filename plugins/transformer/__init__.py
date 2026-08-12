```python
# plugins/transformer/__init__.py

"""
GridForge Transformer Plugin Package
====================================

GridForge Plugin Layer

Provides optional transformer-specific capabilities that extend the
frozen core/model transformer without expanding the core model.

Available capabilities
----------------------

    TransformerPlugin
        Common transformer-plugin base contract.

    Winding
        Physical transformer winding representation.

    VectorGroup
        Transformer winding connection and vector-group representation.

    Grounding
        Transformer neutral and grounding configuration.

    TapChanger
        Physical transformer tap-changer representation.

    TransformerEquivalent
        Detailed transformer electrical-equivalent representation.

Architecture
------------

The authoritative transformer equipment object remains:

    core.model.transformer.Transformer

Specialized transformer capabilities live here:

    plugins.transformer

The plugin layer must not make the core model depend on these
modules.

Numerical calculations remain the responsibility of the appropriate
network, solver, analysis, protection, dynamics, and simulation
layers.

GridForge V2 Status
-------------------
ACTIVE DEVELOPMENT

The transformer plugin package is not yet frozen.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from .base import TransformerPlugin
from .winding import Winding
from .vector_group import VectorGroup
from .grounding import Grounding
from .tap_changer import TapChanger
from .equivalent import TransformerEquivalent


__all__ = [
    "TransformerPlugin",
    "Winding",
    "VectorGroup",
    "Grounding",
    "TapChanger",
    "TransformerEquivalent",
]


__version__ = "0.1.0"
```
