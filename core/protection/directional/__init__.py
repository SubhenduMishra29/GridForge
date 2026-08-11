```python
"""
GridForge Directional Protection
================================

Directional protection plugin.

Provides:
    DirectionalRelay

Capabilities
------------
- Directional current pickup
- Forward/reverse fault discrimination
- Voltage-current angle supervision

Detailed protection logic is implemented in:

    core.protection.directional.directional_relay
"""

from core.protection.directional.directional_relay import (
    DirectionalRelay,
)

__all__ = [
    "DirectionalRelay",
]
```
