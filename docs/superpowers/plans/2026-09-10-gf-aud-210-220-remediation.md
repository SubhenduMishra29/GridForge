# GF-AUD-210–220 Remediation Execution Plan

**Author:** Subhendu Mishra

Implementation order is frozen as:

1. Contract
2. Line
3. Cable
4. Transformer
5. Prepared numerical snapshot
6. YBus
7. Power Flow integration
8. Persistence
9. Compatibility sweep
10. Final static audit

The single authoritative numerical boundary is:

```text
Engineering models
       ↓
PowerFlowPreparation
       ↓
Immutable prepared PU branch state
       ↓
YBusBuilder
       ↓
Solver
```

The implementation must reuse `PerUnitSystem`, preserve canonical terminal resolution and BusIndex ordering, preserve GF-AUD-207/208 Power Flow contracts, avoid changes to GF-AUD-204, and introduce no UI mutation path. Tests may be added/updated but are not to be executed during this remediation cycle unless separately authorized.
