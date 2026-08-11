```python
"""
GridForge Base Layer
====================

GridForge V2 Base Layer

This package contains the foundational engineering utilities shared
across the GridForge platform.

Public API
----------
PerUnitSystem
    System-wide per-unit conversion and base-calculation utility.

Architecture Rule
-----------------
All GridForge layers that require per-unit calculations should import
PerUnitSystem from this package rather than importing implementation
modules directly.

Example
-------
    from core.base import PerUnitSystem

    pu = PerUnitSystem(base_mva=100.0)
"""

from .per_unit import PerUnitSystem

__all__ = [
    "PerUnitSystem",
]
```
