# Command-handler registration contract

The Application handler map registers only command families backed by canonical
Core lifecycle APIs.

Required supported families include Generator, Shunt, Line, Cable, Transformer,
Switch, Breaker, Disconnector, Fuse, Capacitor, CT, CVT, Battery, and PT.

`Branch` is a common Core abstraction, not an independently registered equipment
family; there is no generic Branch command or handler lifecycle.
