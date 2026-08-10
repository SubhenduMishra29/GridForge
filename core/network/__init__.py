"""
GridForge Network Package

Provides the network-level infrastructure for the GridForge
power-system model.

Public components:

```
Network
    Central electrical network model and orchestration boundary.

YBusBuilder
    Builds the network admittance matrix.

TopologyManager
    Manages electrical connectivity, switching and islands.

PerUnitSystem
    Provides system-base and multi-voltage per-unit conversions.
```

Architecture:

```
core/network/
    network.py
    ybus.py
    topology.py
    per_unit.py
```

Numerical solvers are NOT exposed from this package.

Solver implementations belong under:

```
core/solver/
```

"""

from .network import Network
from .ybus import YBusBuilder
from .topology import TopologyManager
from .per_unit import PerUnitSystem

**all** = [
"Network",
"YBusBuilder",
"TopologyManager",
"PerUnitSystem",
]
