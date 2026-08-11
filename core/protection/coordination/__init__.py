```python
"""
GridForge Protection Coordination Package
=========================================

Protection coordination subsystem.

Provides:
    TCCCurve
    RelayCoordination

Capabilities
------------
- IEC time-current characteristic calculations
- Relay grading
- Primary / backup coordination
- Coordination Time Interval (CTI) evaluation

The coordination layer does not:
- Detect faults
- Operate breakers
- Modify the network model
- Own authoritative relay state
"""

from core.protection.coordination.tcc_curve import (
    TCCCurve,
)

from core.protection.coordination.relay_coordination import (
    RelayCoordination,
)

__all__ = [
    "TCCCurve",
    "RelayCoordination",
]
```
