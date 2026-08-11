```python
"""
GridForge Overcurrent Protection
================================

Overcurrent protection plugin package.

Provides:
    IECOvercurrentRelay

IEC protection algorithms are implemented in:

    core.protection.overcurrent.iec_relay
"""

from core.protection.overcurrent.iec_relay import (
    IECOvercurrentRelay,
)

__all__ = [
    "IECOvercurrentRelay",
]
```
