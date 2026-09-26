# GridForge V2 — Redundancy / Parallel Architecture Register

Baseline: `main` `4edcfd511300c868a30f2813ea1951fdc279374a`

This is an audit register, not a deletion plan. A parallel-looking implementation is not called redundant without consumer/authority evidence.

| Parallel System | Intended Authority | Current / Historical Authority Evidence | Consumers / Surface | Migration Status | Finding IDs |
|---|---|---|---|---|---|
| Core Terminal vs UI equipment-terminal abstractions | Core Terminal + EndpointReference | Frozen architecture rejects an independent authoritative UI terminal model; historical SLD audit requires consumer sweep | SLD snap/connection/equipment interaction | UNVERIFIED | GF-MASTER-0003, 0038 |
| Core equipment vs UI `EquipmentBase`/equipment identity | Core equipment model | SLD must reference stable Core identity; UI objects are projections | Canvas/items/equipment UI | UNVERIFIED | GF-MASTER-0038, 0040 |
| SLDNode / SLDModel vs Core equipment | Core equipment; SLD is projection | SLD architecture permits presentation descriptors but forbids second engineering database | SLD document/projection/canvas | UNVERIFIED | GF-MASTER-0038, 0040 |
| Application topology classification vs revision/topology services | Core/network topology | Frozen architecture assigns global connectivity to Core/network | Application study/read consumers | UNVERIFIED | GF-MASTER-0036, 0039, 0041 |
| Application revision vs Core topology revision | Explicit coordinated revision contract | Historical study provenance audit identified inconsistent revision capture | Studies/results/dirty state | OPEN | GF-MASTER-0021, 0026, 0036 |
| Application dirty state vs `SLDDocument.modified` | Application/project lifecycle state | Historical UI audit explicitly treats dirty authority as an Application/project concern | SLD/project lifecycle | UNVERIFIED | GF-MASTER-0016, 0036 |
| Application SLD mutation vs `SLDReadSynchronizer` | Application read/projection boundary | C9 says synchronizer obtains snapshots through Application facade | SLD synchronization | UNVERIFIED | GF-MASTER-0016, 0012-like historical UI findings |
| UI Connection vs Application/Core connection/topology | Core/network topology | Contract says topology owns global connectivity; UI connection is interaction/projection | SLD connection workflow | OPEN | GF-MASTER-0039 |
| Legacy connection subsystem vs active SLD path | Current canonical Application/Core path | Batch 1E retired stale ui.topology and reconciled ui.connections documentation/tool preview state to the EndpointIdentityAdapter → EndpointReference → Application command boundary | UI connection code | REMEDIATED — VERIFICATION DEFERRED | GF-MASTER-0043 |
| Legacy equipment factory vs active SLD realization | Canonical SLDGraphicsItemFactory / projection | Current audit documents factory as construction boundary only | Canvas/item construction | UNVERIFIED | GF-MASTER-0040, 0043 |
| Multiple event consumers doing full synchronization | Semantic event producer + projection-specific consumers | Event vocabulary was narrowed historically; full consumer behavior remains unexecuted | UI projections | UNVERIFIED | GF-MASTER-0035 |
| PanelArea in Workspace vs panel metadata | Workspace `PanelArea` | Modification register locks `ui.workspace.PanelArea` as canonical | PanelDescriptor/PanelState/Workspace | UNVERIFIED | GF-MASTER-0018 |
| PanelsPlugin docking vs WorkspaceRealizer/MainWindow | WorkspaceRealizer + MainWindow | Historical finding confirms direct docking in PanelsPlugin | Plugin/panel startup | UNVERIFIED | GF-MASTER-0019 |
| Panel lifecycle vs Workspace placement | PanelManager/Instance/State for lifecycle; Workspace for placement | Modification register explicitly separates these responsibilities | Panel subsystem | UNVERIFIED | GF-MASTER-0018, 0020 |
| PluginManager vs Workspace layout | PluginManager lifecycle/composition; Workspace layout | Historical plugin audit says PluginManager does not appear to own layout | Plugin startup | UNVERIFIED | GF-MASTER-0020 |
| Per-unit systems | `core/base/per_unit.py` `PerUnitSystem` | Current-head audit identifies one active canonical PU system | Study preparation/YBus | UNVERIFIED | GF-MASTER-0025 |
| Engineering-unit conversion in models vs study preparation | Study preparation | Current-head audit places engineering→PU conversion in preparation | Power Flow/YBus/flow | UNVERIFIED | GF-MASTER-0021, 0023 |
| YBus vs live Network numerical construction | Prepared YBus | Current-head/static audit says YBus consumes prepared data only | Numerical solver | UNVERIFIED | GF-MASTER-0025 |
| Power Flow live-network state vs prepared snapshot | PreparedPowerFlow | Preparation still accesses live Network and calls `ensure_bus_index()` | PF preparation | UNVERIFIED | GF-MASTER-0021 |
| Short Circuit live-network construction vs detached preparation | ShortCircuitPreparation / detached input | Historical remediation introduced detached boundary | Short Circuit solver | UNVERIFIED | GF-MASTER-0026 |
| Protection measurement vs relay-local measurement models | CT/PT/CVT/MeasurementPoint/MeasurementChannel | Historical audit says existing measurement architecture is canonical | Relay/protection | UNVERIFIED | GF-MASTER-0028 |
| Protection direct ModelService trip vs Application command path | Application.execute / CommandManager | GF-EDM-069 correction routes through Application | Protection trip | UNVERIFIED | GF-MASTER-0029 |
| Dynamic state class vocabulary | `DynamicStateVector` | Current source defines `DynamicStateVector`; package export still references `DynamicState` | Dynamics imports/state | CONFIRMED conflict | GF-MASTER-0012 |
| Dynamic machine protocol vs concrete machine model | Canonical `DynamicMachineModel` contract if present | Current `machine_models.py` inspected source does not define the imported contract | Dynamics state vector | CONFIRMED conflict | GF-MASTER-0011 |
| Study results vs equipment persistent state | Study/result provenance | Frozen architecture says calculated study results are not authoritative physical state | Persistence/results | UNVERIFIED | GF-MASTER-0021, 0031 |
