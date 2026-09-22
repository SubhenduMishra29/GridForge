# GridForge V2 — Master Audit Register

**Purpose:** lossless audit-register consolidation; no production remediation.
**Repository:** `pandaraseswari03-collab/GridForge`
**Branch baseline:** `main` at `d5900e8c8dbd85eefa5e148fb07079a7125accc0`
**Consolidation date:** 2026-09-17
**Authority:** frozen GridForge V2 architecture supplied for this audit.

## Evidence discipline

This register distinguishes current repository evidence from historical register claims. A source change is not treated as resolution without executable/current verification. Historical IDs whose original wording is not present in the current repository are preserved in the Legacy ID Coverage Appendix and are **not silently deleted or declared duplicates**. This is a material evidence gap, not a closure.

## Source registers discovered on `main`

1. `AUDIT_REPORT.md`
2. `AUDIT_STATUS_2026-09-10.md`
3. `AUDIT_STATUS_2026-09-10_FINAL.md`
4. `AUDIT_STATUS_2026-09-11_CORE_CLOSURE.md`
5. `AUDIT_STATUS_2026-09-12_FINAL_CLOSURE.md`
6. `RUNTIME_STARTUP_DEFECT_REGISTER.md`
7. `Modification_Register.txt`
8. `docs/audits/2026-09-03-gridforge-v2-ui-audit-checkpoints.md`
9. `docs/superpowers/audits/2026-09-10-gf-aud-210-220-edm-001-069-compatibility-sweep.md`
10. `docs/superpowers/audits/2026-09-10-gf-aud-210-220-edm-001-069-current-head-audit.md`
11. `docs/superpowers/audits/2026-09-10-gf-aud-210-220-edm-001-069-static-verification.md`
12. `docs/superpowers/audits/2026-09-11-protection-application-boundary-closure.md`
13. `contract.md` as an architectural/audit baseline.

Git history was also inspected for audit evolution and remediation lineage, including the runtime-startup closure merge at `4edcfd511300c868a30f2813ea1951fdc279374a`.

## Canonical register

| Master ID | Legacy IDs | Domain | Subsystem | Finding Title | Severity | Status | Root Cause | Impact | Frozen Principle Violated | Verification Required |
|---|---|---|---|---|---|---|---|---|---|---|
| GF-MASTER-0001 | GF-AUD-007 | Study | Contingency | Contingency result consumer is incompatible with authoritative Power Flow result vocabulary | CRITICAL | CONFIRMED | Consumer expects `converged`, `bus_voltage`, `line_loading`, `transformer_loading`; current `PowerFlowResult` exposes a different contract | Contingency decisions can be incorrect or fail at runtime | Studies consume authoritative prepared/result contracts | Yes |
| GF-MASTER-0002 | GF-AUD-005 | Study | Contingency | Bus-outage semantics require authoritative topology/state reconciliation | HIGH | UNVERIFIED | Historical contingency behavior disables a bus and connected equipment without current executable proof of canonical topology semantics | Incorrect outage isolation can affect study correctness | Core/network owns topology and authoritative electrical state | Yes |
| GF-MASTER-0003 | GF-AUD-006 | Core | Endpoint/Topology | Defensive terminal fallbacks in contingency logic are not proven canonical | HIGH | UNVERIFIED | Consumer-side endpoint fallback logic was retained instead of proven against the authoritative Terminal/EndpointReference contract | Endpoint identity/topology interpretation can diverge | Endpoint identity reconciles through canonical Core terminal references | Yes |
| GF-MASTER-0004 | GF-AUD-014 | SLD | Semantic presentation | SLD read-side vocabulary exceeds current semantic/render coverage | HIGH | UNVERIFIED | Read side can expose many equipment types while semantic realization/concrete graphics coverage is narrower | Non-bus SLD nodes may have no deliberate representation | SLD is a projection and must have an explicit presentation contract | Yes |
| GF-MASTER-0005 | GF-AUD-012; GF-DOC-A1 | Documentation | Architecture/audit documentation | Architectural and audit-state documentation can lag current implementation | MEDIUM | OPEN | Historical documents retain superseded/pending descriptions without a single authoritative reconciliation ledger | Engineers can act on stale architectural assumptions | Documentation must reflect the frozen architecture and evidence state | Yes |
| GF-MASTER-0006 | RS-005; RS-006; RS-013; RS-015; RS-017 | Runtime | Packaging/dependencies | Runtime dependency and packaging authority was historically fragmented | HIGH | UNVERIFIED | Earlier CI used ad-hoc dependencies; `pyproject.toml` now declares canonical runtime/dev dependencies, but current execution proof is absent | Fresh-process installation/startup may remain unproven; RS-013 is an exact duplicate of RS-005 | Runtime must have a reproducible canonical dependency contract | Yes |
| GF-MASTER-0007 | RS-007; RS-014; RS-019; RS-020 | Runtime | CI/startup verification | Startup CI coverage exists but current successful execution is not proven | HIGH | UNVERIFIED | Verification workflow is present and targets `main`/PR/remediation paths, but no completed successful run was established in the audit | Syntax/import/startup regressions can escape detection | Runtime correctness requires executable evidence | Yes |
| GF-MASTER-0008 | RS-008; RS-016 | Runtime | Startup execution | Current-main startup remains unverified | CRITICAL | OPEN | No successful current-main `import main` / application bootstrap execution evidence was available | Application startup can remain broken despite source-level changes | Runtime startup blockers require executable proof | Yes |
| GF-MASTER-0009 | RS-009 | Runtime | Source integrity | Historical Markdown-fence corruption required direct source verification | CRITICAL | RECLASSIFIED | Historical register reported fenced `state_vector.py`; current file is no longer fenced, but its API imports a missing `DynamicMachineModel`, so the historical syntax defect is superseded by a live API defect | Syntax issue may be replaced by import-time failure | Source integrity and canonical package API must both hold | Yes |
| GF-MASTER-0010 | RS-018 | Runtime | CI integrity | CI source-repair workaround was removed | HIGH | RESOLVED | Current workflow fails on source-integrity checks rather than rewriting source | Prevents verification from mutating the code under test | Audit/CI must not silently modify production source | No |
| GF-MASTER-0011 | — | Dynamics | Public API | `DynamicStateVector` imports a `DynamicMachineModel` contract that is absent from current `machine_models.py` | CRITICAL | CONFIRMED | State-vector implementation references a protocol/type not present in the current machine-model module | Import-time failure blocks Dynamics and may block startup paths | Canonical subsystem API must be internally consistent | Yes |
| GF-MASTER-0012 | — | Dynamics | Package exports | `core.solver.dynamics.__init__` exports obsolete `DynamicState` instead of current `DynamicStateVector` | CRITICAL | CONFIRMED | Package export vocabulary was not reconciled with the current state-vector class | Package import can fail before numerical execution | Public API must expose implemented canonical symbols | Yes |
| GF-MASTER-0013 | historical Dynamics API reconciliation; commit `30010462...` | Dynamics | Public API migration | Dynamics public symbols underwent incompatible contract migration | HIGH | UNVERIFIED | Legacy symbol names and newer implementations evolved across package exports | Import/consumer failures can propagate into startup | Canonical subsystem API requires consumer-wide reconciliation | Yes |
| GF-MASTER-0014 | historical Dynamics initial-state audit | Dynamics | PF→Dynamics initialization | Initial-state bridge may derive electrical operating-point power from mechanical input rather than authoritative solved power | HIGH | UNVERIFIED | Preparation boundary exists, but operating-point semantics require reconciliation | Dynamic initial state may not represent solved PF state | Studies initialize from authoritative prepared/result state | Yes |
| GF-MASTER-0015 | GF-AUD-019; GF-AUD-WS-019 | Dynamics | Transient/network coupling | Transient execution lacks a fully proven canonical algebraic network-coupling contract | CRITICAL | OPEN | Historical audit explicitly required a canonical algebraic network-coupling contract and did not add a speculative second architecture | Transient stability execution can be structurally incomplete | One authoritative network model; study execution consumes explicit contracts | Yes |
| GF-MASTER-0016 | GF-AUD-WS-003; GF-AUD-WS-004; GF-AUD-WS-005; GF-AUD-WS-006; GF-AUD-WS-008; GF-AUD-WS-009 | UI | Workspace/lifecycle | Workspace/project UI composition was source-remediated but runtime verification was deferred | HIGH | UNVERIFIED | Source-level composition exists without executable GUI lifecycle evidence | Startup/project activation/teardown can still diverge | UI is composed around Application and canonical workspace authority | Yes |
| GF-MASTER-0017 | GF-AUD-065; GF-AUD-069 | UI | Workspace consumers | Workspace/panel consumer coverage was historically inconclusive | MEDIUM | UNVERIFIED | Indexed search was explicitly insufficient and direct consumer tracing remained required | Stale placement consumers may survive unnoticed | Workspace/Layout is sole placement authority | Yes |
| GF-MASTER-0018 | GF-AUD-066; GF-AUD-068 | UI | Panel placement metadata | PanelArea/area ownership was duplicated across Workspace and panel metadata | HIGH | UNVERIFIED | PanelDescriptor/PanelState historically carried placement-like state while Workspace owns canonical placement | Competing placement authorities can reappear | Panel metadata/lifecycle must not own canonical workspace placement | Yes |
| GF-MASTER-0019 | GF-AUD-071 | UI | PanelsPlugin | PanelsPlugin historically performed direct Qt docking operations | HIGH | UNVERIFIED | Panel composition plugin crossed into workspace realization | Docking policy can bypass WorkspaceRealizer/MainWindow ownership | WorkspaceRealizer translates layout decisions into MainWindow/Qt operations | Yes |
| GF-MASTER-0020 | GF-AUD-072 | UI | Plugin composition | Plugin lifecycle/composition handoff and shutdown/rollback remain incompletely verified | HIGH | UNVERIFIED | Static architecture was established but complete lifecycle execution was not proven | Plugin ordering/resource cleanup can fail | Plugin infrastructure is separate from workspace/electrical authority | Yes |
| GF-MASTER-0021 | GF-AUD-003; GF-EDM-049; GF-EDM-050; GF-EDM-063; GF-EDM-064; GF-EDM-065 | Study | Power Flow preparation | Prepared Power Flow boundary is structurally present but runtime/immutability proof remains incomplete | HIGH | UNVERIFIED | Preparation converts engineering state to detached numerical structures but live `Network` access and nested mutability remain concerns | Analysis may mutate or mis-correlate authoritative state | Numerical solvers consume prepared authoritative snapshots | Yes |
| GF-MASTER-0022 | GF-EDM-001–019 | Core | Engineering data | Engineering-data findings remain incompletely reconciled study-by-study | HIGH | UNVERIFIED | Historical findings were broad; current consumers require per-study deterministic preparation verification | Missing/ambiguous engineering inputs can cause incorrect results | Physical model is authoritative; studies derive explicit representations | Yes |
| GF-MASTER-0023 | GF-AUD-212; GF-AUD-217; GF-AUD-218; GF-AUD-220 | Core | Transformer numerical data | Transformer impedance basis is explicit in model but conversion/persistence verification is incomplete | HIGH | UNVERIFIED | `pu`/`engineering` basis exists, while downstream support and round-trip proof are incomplete | Transformer study results can be wrong or data can be rejected unexpectedly | Engineering-unit interpretation belongs in preparation/migration | Yes |
| GF-MASTER-0024 | GF-EDM-028; GF-EDM-047; GF-EDM-067 | Study | Reactive equipment | Capacitor/Reactor preparation uses `PreparedShunt`, but executable numerical proof is pending | HIGH | UNVERIFIED | Prepared shunt representation exists without full execution evidence | Reactive injections/susceptance can be wrong | Numerical boundary consumes prepared state | Yes |
| GF-MASTER-0025 | GF-EDM-050; GF-EDM-063 | Study | Per-unit/YBus | Per-unit conversion and YBus authority are separated correctly, but deep immutability/consumer sweep remains incomplete | HIGH | UNVERIFIED | `PerUnitSystem` is canonical; YBus consumes prepared PU data, but SciPy CSR payload remains mutable | Snapshot integrity and downstream interpretation can diverge | One PU authority; YBus is numerical-only | Yes |
| GF-MASTER-0026 | GF-EDM-051–054 | Study | Short Circuit | Short-circuit detached preparation/result boundary is source-present but executable verification remains pending | HIGH | UNVERIFIED | Preparation and typed results were added after historical open state; no runtime study proof was established | Fault results/provenance can remain incorrect or incomplete | Studies consume detached authoritative input | Yes |
| GF-MASTER-0027 | GF-EDM-055–057 | Protection | Study preparation | Protection study/execution boundary remains source-present but end-to-end proof is absent | HIGH | UNVERIFIED | Detached preparation exists; offline-vs-simulation and measurement-chain behavior need executable verification | Protection decisions may not reflect authoritative measurements | Protection is a study/domain layer over authoritative equipment | Yes |
| GF-MASTER-0028 | GF-EDM-030–037; GF-EDM-038–045; GF-AUD-204; GF-AUD-205 | Protection | Measurement | CT/PT/CVT/MeasurementPoint/MeasurementChannel architecture has been reconciled, but conversion and channel tests were not executed | HIGH | UNVERIFIED | Source-level measurement conversion and duplicate-command cleanup exist without runtime proof | Relay pickup/measurement values may be wrong | Protection measurement must be derived from explicit engineering/numerical contracts | Yes |
| GF-MASTER-0029 | GF-EDM-069 | Protection | Breaker trip application boundary | Protection decision now routes through Application command execution, but integration verification is deferred | HIGH | UNVERIFIED | Prior direct `ModelService` mutation bypassed Application; source correction exists | History/transaction/event semantics can be bypassed if path regresses | All meaningful mutation crosses Application.execute() | Yes |
| GF-MASTER-0030 | GF-EDM-058; GF-EDM-059; GF-EDM-060; GF-EDM-061; GF-EDM-068 | Dynamics | Capability boundary | Dynamic preparation/control-model capabilities are deferred or absent in historical scope | HIGH | DEFERRED | Historical audits explicitly deferred detailed dynamic execution/model capabilities rather than inventing them | Required dynamic studies may be unavailable | Do not invent unsupported study models | Yes |
| GF-MASTER-0031 | GF-AUD-206; GF-AUD-216; GF-PERSIST-A7; GF-PERSIST-A8; GF-PERSIST-A11 | Persistence | Project package | Canonical `.gridforge` persistence boundary exists, but full semantic round-trip is unverified | CRITICAL | UNVERIFIED | Package structure is present; executable all-equipment reconstruction/equivalence proof is absent | Data loss, stale reconstruction, or ambiguous engineering state risk | `manifest.json` + `project.json` are canonical; QGraphics is not persistence authority | Yes |
| GF-MASTER-0032 | GF-PERSIST-A7; GF-PERSIST-A8; GF-PERSIST-A11 | Persistence | Engineering-state migration | Legacy Cable/Transformer engineering representation requires explicit metadata and ambiguity handling | HIGH | UNVERIFIED | Migration rejects ambiguous data rather than guessing, but full corpus coverage is unverified | Legacy projects may fail to load or be misinterpreted | Persistence preserves engineering truth and representation metadata | Yes |
| GF-MASTER-0033 | historical dynamic-model persistence commits | Persistence | Dynamics association | Project-scoped dynamic-model association persistence was added but round-trip proof is absent | HIGH | UNVERIFIED | Serialization/composition wiring exists without fresh reconstruction verification | Dynamic model identity/configuration can be lost across reload | Persistence reconstructs authoritative domain state | Yes |
| GF-MASTER-0034 | historical relay/protection persistence commits | Persistence | Protection serialization | Relay and project protection configuration persistence was added but full reconstruction proof is absent | HIGH | UNVERIFIED | Source serialization coverage exists without complete semantic round-trip evidence | Protection configuration can be lost or detached from equipment | Canonical project persistence must preserve required engineering state | Yes |
| GF-MASTER-0035 | GF-AUD-018; historical event audit | Application | Events | Semantic event vocabulary/restrictions have source-level reconciliation but runtime event propagation is unverified | HIGH | UNVERIFIED | Events are separated from presentation, but executable producer/consumer coverage is incomplete | UI projections/study lifecycle can become stale or over-react | Core→Application→UI event direction | Yes |
| GF-MASTER-0036 | historical Application revision findings | Application | Revision/validation | Application/Core revision and validation coordination remains insufficiently runtime-proven | HIGH | UNVERIFIED | Multiple historical revisions/dirty-state concerns were reconciled in source but not fully executed | Stale study/result state or dirty-state inconsistency | Revision/validation state has one authoritative coordination path | Yes |
| GF-MASTER-0037 | historical Application mutation findings | Application | Command/transaction/history | Application-only mutation boundary and undo/redo semantics require complete consumer verification | CRITICAL | UNVERIFIED | Historical findings identify direct mutation paths and divergent command handling; later source changes are not executable proof | Core state can change outside history/transaction/event guarantees | All meaningful UI/domain mutation uses immutable Command→Application.execute() | Yes |
| GF-MASTER-0038 | historical SLD terminal/equipment findings | SLD | Identity | Parallel UI/equipment/terminal identity representations require full consumer reconciliation | CRITICAL | UNVERIFIED | SLD/UI can carry presentation identities while Core owns authoritative equipment/terminal identity; historical duplicate abstractions require traceability | Wrong endpoint/equipment can be edited, connected, rendered, or persisted | No authoritative duplicate Terminal/equipment model in UI | Yes |
| GF-MASTER-0039 | historical SLD connection/topology findings | SLD | Connection lifecycle/topology | UI connection state and Core topology authority require complete migration proof | CRITICAL | UNVERIFIED | Historical connection/terminal concerns require Application/Core topology authority | SLD can diverge from actual connectivity | Core/network owns global topology | Yes |
| GF-MASTER-0040 | historical SLD rendering/factory findings | SLD | Projection-rendering | Rendering boundary is structurally separated, but supported-type coverage and runtime rendering remain unverified | HIGH | UNVERIFIED | Factory/projection separation exists while semantic coverage is incomplete | Render failures or accidental engineering logic in presentation | QGraphicsItem is presentation-only | Yes |
| GF-MASTER-0041 | historical Core architecture findings | Core | Authority-topology-equipment | Core authority is structurally defined but broad historical findings require current consumer-level verification | CRITICAL | UNVERIFIED | Multiple historical architecture concerns were source-reconciled in different batches without one executable repository-wide proof | Duplicate authority can re-emerge in consumers | Core owns authoritative engineering/domain truth | Yes |
| GF-MASTER-0042 | historical control findings; GF-EDM control-related records where applicable | Control | Control/automation | Control/ladder/simulation/command integration is not fully evidenced in the consolidated registers | HIGH | UNVERIFIED | Historical control scope is fragmented and current complete consumer chain was not demonstrated | Breaker/control interactions may bypass canonical Application events/commands | Control actions must use authoritative Application/Core boundaries | Yes |
| GF-MASTER-0043 | historical redundancy/migration findings | Architecture | Migration/redundancy | Legacy/parallel subsystem migration cannot be declared complete from absence or source deletion alone | HIGH | UNVERIFIED | Historical audits repeatedly warn that indexed absence is insufficient evidence | Duplicate authorities may remain hidden in consumers | One responsibility/one owner; no speculative deletion | Yes |
| GF-MASTER-0044 | historical test/evidence findings | Runtime | Verification | Large portions of remediation are source-level only; executable evidence is incomplete | HIGH | UNVERIFIED | Test specifications/workflows exist but current successful runs were not established | False closure can mask startup, persistence, study, and UI defects | RESOLVED requires current executable evidence | Yes |
| GF-MASTER-0045 | NEW — SLD contextual engineering-state hover/readout | UI/SLD | Canvas interaction | Canonical contextual hover/readout interaction contract is not composed | MEDIUM | OPEN | Application read-side state exists but no verified Canvas hover/readout contract was established | Users may lack contextual engineering-state feedback | UI consumes projections/read models; it does not invent authority | Yes |
| GF-MASTER-0046 | GF-AUD-001; GF-AUD-002; GF-AUD-004; GF-AUD-008; GF-AUD-009; GF-AUD-010; GF-AUD-011 | Architecture | Historical aligned findings | Previously aligned architectural findings are preserved but not all have fresh executable verification | MEDIUM | UNVERIFIED | Historical closure claims relied on static/source evidence; current main differs | Historical confidence may exceed current executable evidence | Claims of alignment require current evidence | Yes |
| GF-MASTER-0047 | GF-ARCH-A1; GF-ARCH-A2; GF-ARCH-A4; GF-ARCH-A5; GF-ARCH-A6; GF-ARCH-A7; GF-ARCH-A8; GF-ARCH-A9; GF-ARCH-A19; GF-ARCH-A20; GF-SLD-A1; GF-SLD-A2; GF-SLD-A4; GF-SLD-A5; GF-SLD-A6; GF-SLD-A7; GF-SLD-A8; GF-SLD-A53; GF-APP-A1; GF-APP-A2; GF-APP-A4; GF-APP-A5; GF-APP-A6; GF-APP-A7; GF-APP-A9; GF-APP-A10; GF-APP-A11; GF-APP-A12; GF-APP-A14; GF-APP-A15; GF-APP-A16; GF-APP-A18; GF-APP-A19; GF-APP-A20; GF-APP-A22; GF-APP-A23; GF-APP-A24; GF-CORE-A12; GF-CORE-A15; GF-CORE-A16; GF-CORE-A19; GF-CORE-A20; GF-PERSIST-A1; GF-PERSIST-A5; GF-PERSIST-A6; GF-PERSIST-A9; GF-PERSIST-A10 | Architecture | Historical mandatory-ID coverage | Historical IDs were explicitly required for preservation, but their complete original finding text is not present in the current register files inspected | Cannot safely infer exact root cause/status from ID alone | Lossless audit history must preserve IDs without fabricating missing facts | Yes |
| GF-MASTER-0048 | GF-ARCH-A3; GF-ARCH-A10; GF-ARCH-A12; GF-ARCH-A13; GF-ARCH-A14; GF-ARCH-A15; GF-ARCH-A17; GF-ARCH-A18; GF-ARCH-A22; GF-ARCH-A23; GF-ARCH-A26; GF-ARCH-A29; GF-ARCH-A30; GF-ARCH-A31; GF-ARCH-A32; GF-ARCH-A33; GF-ARCH-A35; GF-ARCH-A36; GF-ARCH-A37; GF-ARCH-A39; GF-ARCH-A40; GF-ARCH-A41; GF-ARCH-A42; GF-ARCH-A43; GF-ARCH-A44; GF-APP-A3; GF-APP-A8; GF-APP-A13; GF-APP-A27; GF-APP-A28; GF-APP-A29; GF-APP-A30; GF-APP-A31; GF-APP-A32; GF-APP-A33; GF-APP-A34; GF-APP-A36; GF-APP-A37a; GF-APP-A38; GF-APP-A39; GF-APP-A41; GF-APP-A42; GF-SLD-A3; GF-SLD-A9; GF-SLD-A10; GF-SLD-A11; GF-SLD-A12; GF-SLD-A13; GF-SLD-A14; GF-SLD-A15; GF-SLD-A16; GF-SLD-A17; GF-SLD-A18; GF-SLD-A19; GF-SLD-A20; GF-SLD-A21; GF-SLD-A22; GF-SLD-A23; GF-SLD-A24; GF-SLD-A25; GF-SLD-A26; GF-SLD-A27; GF-SLD-A28; GF-SLD-A29; GF-SLD-A30; GF-SLD-A31; GF-SLD-A33; GF-SLD-A34; GF-SLD-A35; GF-SLD-A37; GF-SLD-A38; GF-SLD-A39; GF-SLD-A40; GF-SLD-A41; GF-SLD-A42; GF-SLD-A43; GF-SLD-A44; GF-SLD-A45; GF-SLD-A46; GF-SLD-A47; GF-SLD-A48; GF-SLD-A49; GF-SLD-A50; GF-SLD-A52; GF-SLD-A54; GF-SLD-A55; GF-CORE-A13; GF-CORE-A17; GF-CORE-A18; GF-CORE-A21; GF-CORE-A22; GF-CORE-A21; GF-CORE-A22; GF-PERSIST-A7; GF-PERSIST-A8; GF-PERSIST-A11; GF-STUDY-A1; GF-STUDY-A2; GF-STUDY-A3; GF-STUDY-A4; GF-STUDY-A5; GF-STUDY-A6; GF-DOC-A1 | Architecture/Core/Application/UI/SLD/Persistence/Study/Documentation | Historical mandatory-ID coverage | Preservation-only holding area for unresolved historical IDs | Original detailed text is not present in the currently inspected source registers; no root-cause merge is asserted | Prevents silent loss of historical findings while avoiding invented descriptions | Yes |

## Batch 8 — SLDModel Ownership, Projection Isolation, Geometry Preservation & Persistence

The following `GF-INT` findings are the authoritative current-head batch entries supplied by the Batch 8 audit. They are retained as individual audit IDs rather than collapsed into historical master findings. `PASS / CLOSED` is preserved as the supplied severity/status notation for these explicit closure findings.

| ID | Finding | Severity | Status | Evidence | Cross-reference |
|---|---|---|---|---|---|
| GF-INT-068 | SLDModel is isolated from Core/electrical logic | PASS / CLOSED | CLOSED | `ui/sld/sld_model.py`; SLDModel contains SLDNode/SLDConnection presentation structures and does not own electrical calculations, topology, rendering, input handling, or solver logic. | GF-MASTER-0038; GF-MASTER-0040 |
| GF-INT-069 | SLDProjectionManager does not own persistent geometry | PASS / CLOSED | CLOSED | `ui/sld/sld_projection_manager.py`; ProjectionManager owns projection/layout behavior rather than persistent document geometry. | GF-MASTER-0040 |
| GF-INT-070 | SLD node identity is coupled to Core object identity | HIGH | OPEN | `ui/sld/sld_read_synchronizer.py`; synchronization uses Application/Core `object_id` as SLD `node_id`, despite SLDNode having separate `node_id` and `equipment_id`. | GF-INT-071; GF-INT-077; GF-INT-078; GF-INT-0038 |
| GF-INT-071 | Projection-source tagging exists but is not used as an ownership guard | HIGH | OPEN | `ui/sld/sld_read_synchronizer.py`; `projection_source="application_read_model"` is assigned and used for stale cleanup, but lookup occurs by `node_id/object_id` before ownership is established. | GF-INT-070; GF-INT-077 |
| GF-INT-072 | Existing user geometry is preserved during projection | PASS / CLOSED | CLOSED | `ui/sld/sld_read_synchronizer.py`; existing projected nodes receive semantic/projection updates without overwriting their existing `x/y` position. | GF-INT-073; GF-INT-085 |
| GF-INT-073 | Newly projected nodes default to `(0,0)` instead of using a persistent layout policy | MEDIUM | OPEN | `ui/sld/sld_read_synchronizer.py`; new projected nodes are created with `x=0.0`, `y=0.0`; projection synchronization does not establish a persistent initial-placement policy. | GF-INT-069; GF-INT-072; GF-INT-082 |
| GF-INT-074 | Projection reconciliation does not falsely mark the SLD document dirty | PASS / CLOSED | CLOSED | `SLDReadSynchronizer` mutates projection/model state without calling `SLDDocument.mark_modified()`; user-driven mutations participate in dirty tracking. | GF-INT-086 |
| GF-INT-075 | Persistence separates electrical network state from SLD presentation state | PASS / CLOSED | CLOSED | `core/persistence/project_persistence.py`; project persistence stores Network and SLD presentation separately. | GF-MASTER-0031; GF-INT-084 |
| GF-INT-076 | SLD geometry survives serialization/reload | PASS / CLOSED | CLOSED | `ui/sld/sld_document.py`; `ui/sld/sld_model.py`; node identity, equipment reference, coordinates, properties and connections are serialized/deserialized. | GF-INT-075; GF-INT-085; GF-MASTER-0031 |
| GF-INT-077 | Reload/projection reconciliation can convert a user presentation node into a projection-owned node | HIGH | OPEN | `ui/sld/sld_read_synchronizer.py`; a persisted user node whose `node_id` collides with a Core `object_id` can be found and assigned `equipment_id` and `projection_source`. | GF-INT-070; GF-INT-071; GF-INT-085 |
| GF-INT-078 | SLD connection identity is also coupled to Core branch identity | HIGH | OPEN | `ui/sld/sld_read_synchronizer.py`; Core branch `object_id` is used as the SLD connection identity. | GF-INT-070; GF-MASTER-0039 |

## Batch 9 — SLD Command Ownership, Collision Rules & Project-Load Ordering

The following `GF-INT` findings are the authoritative current-head batch entries supplied by the Batch 9 audit.

| ID | Finding | Severity | Status | Evidence | Cross-reference |
|---|---|---|---|---|---|
| GF-INT-079 | SLD commands have no explicit ownership classification | HIGH | OPEN | `core/application/commands/sld_commands.py`; Add/Remove/Position/Connection commands operate on presentation IDs without explicit user-authored versus projection-owned classification. | GF-INT-080; GF-INT-087; GF-MASTER-0037 |
| GF-INT-080 | Projection-owned SLD nodes can currently be removed through the generic SLD removal command | HIGH | OPEN | `ui/sld/sld_controller.py`; `core/application/commands/sld_commands.py`; `core/application/services/sld_service.py`; remove_node submits `RemoveSLDNodeCommand` without ownership check, allowing Core equipment to remain while its SLD representation is absent until reconciliation. | GF-INT-079; GF-INT-081; GF-INT-087 |
| GF-INT-081 | User movement of projection-owned nodes lacks explicit ownership semantics | MEDIUM/HIGH | OPEN | `SetSLDNodePositionCommand`; `SLDController.set_node_position()`; position mutation does not distinguish projection-owned equipment geometry from independent user-authored presentation objects. | GF-INT-070; GF-INT-079 |
| GF-INT-082 | Layout arrangement remains coupled to presentation/Core identity | MEDIUM | OPEN | `ui/sld/sld_controller.py`; `SLDProjectionManager`; `arrange_nodes()` uses `node.node_id` and passes it into position commands. | GF-INT-070; GF-INT-073; GF-INT-081 |
| GF-INT-083 | Project loading restores Core network and persistent SLD presentation before project-state activation | PASS / CLOSED | CLOSED | `core/application/project_lifecycle.py`; `open_project()` loads and validates the project, deserializes persistent presentation, activates the Network, installs ProjectContext/presentation, then activates project state. | GF-INT-084; GF-INT-085; GF-MASTER-0031 |
| GF-INT-084 | Persisted SLD state is restored rather than regenerated during project opening | PASS / CLOSED | CLOSED | `core/application/project_lifecycle.py`; persistent presentation is deserialized and installed when present rather than discarded and reconstructed. | GF-INT-075; GF-INT-083; GF-INT-085 |
| GF-INT-085 | Project-state activation still requires end-to-end proof that restored SLD state is not overwritten during immediate reconciliation | MEDIUM/HIGH | OPEN | `core/application/project_lifecycle.py`; project-state activation callback and SLD synchronization path; required invariant is restore → bind → reconcile semantic projection → preserve user geometry. | GF-INT-072; GF-INT-076; GF-INT-077; GF-INT-083; GF-INT-084 |
| GF-INT-086 | SLDDocument dirty state and SLDState local-view dirty state have unclear load semantics | MEDIUM | OPEN | `ui/sld/sld_controller.py`; `ui/sld/sld_document.py`; `ui/sld/sld_state.py`; `replace_document()` resets controller/local state without clearly establishing the authoritative clean baseline for the loaded SLDDocument. | GF-INT-074; GF-INT-083; GF-INT-084; persistence/load lifecycle |
| GF-INT-087 | Remove-node command can implicitly remove multiple SLD connections | MEDIUM | OPEN | `ui/sld/sld_model.py`; `core/application/services/sld_service.py`; removing one node automatically removes all attached SLD connections while command payload contains only node ID. | GF-INT-079; GF-INT-080; GF-MASTER-0037 |

## Batch 8/9 cross-reference register

- `GF-INT-070 ↔ GF-INT-077`
- `GF-INT-070 ↔ GF-INT-078`
- `GF-INT-071 ↔ GF-INT-077`
- `GF-INT-079 ↔ GF-INT-080`
- `GF-INT-081 ↔ GF-INT-070`
- `GF-INT-082 ↔ GF-INT-070`
- `GF-INT-085 ↔ GF-INT-077`
- `GF-INT-086 ↔ persistence/load lifecycle`
- `GF-INT-087 ↔ GF-INT-079 / GF-INT-080`

Earlier relationships retained:

- `GF-INT-064 ↔ transaction/rollback findings`
- `GF-INT-065 ↔ projection ownership`
- `GF-INT-066 ↔ identity collision`
- `GF-INT-067 ↔ project replacement/event binding`

## Architectural continuity note

The Batch 8/9 SLD ownership model is intentionally generic and does not freeze the current Contactor or motor-control architecture. The findings must remain applicable to future Contactor, Motor Starter, Composite Equipment Symbol, Protection Overlay, Control Overlay, Annotation, Grouping, and multi-terminal equipment presentation without allowing UI/SLD presentation objects to become authoritative Core electrical objects.

## Historical/runtime exact-duplicate disposition

- `RS-013` is an exact duplicate of `RS-005` and is represented by GF-MASTER-0006; its legacy ID is preserved.
- No other finding is marked `DUPLICATE` solely from similar wording. Related findings remain separate where remediation could differ.
- Historical “REMEDIATED — VERIFICATION DEFERRED”, “PARTIALLY CLOSED”, “OBSOLETE/SUPERSEDED”, and “REQUIRES ARCHITECTURAL DECISION” labels are retained as Historical Notes/evidence, not converted automatically to `RESOLVED`.

## Mandatory correction preservation

### GF-SLD-A32
The historical claim that `BusItem` did not exist was corrected by later repository evidence showing `ui/items/bus_item.py`. It is therefore preserved as a historical/reclassified observation and must not be presented as a current absence claim. The current UI audit record also identifies `BusItem` as a locked presentation-only component.

### Dynamics runtime correction state
Current `main` still has a public API inconsistency: `state_vector.py` imports `DynamicMachineModel`, while current `machine_models.py` exposes `ClassicalMachineParameters`, `MachineElectricalOutput`, and `ClassicalSynchronousMachine` in the inspected source, and `core/solver/dynamics/__init__.py` imports `DynamicState`. This is retained as an open runtime/API finding; no production change was made during consolidation.

## Current verification evidence

- Current `main` commit: `d5900e8c8dbd85eefa5e148fb07079a7125accc0`.
- `pyproject.toml` contains canonical runtime/dev dependency declarations.
- `.github/workflows/targeted-remediation.yml` installs the declared package, performs source integrity/syntax verification, targeted startup tests, relevant regressions, and a full test suite, but this audit did not establish a successful run.
- `state_vector.py` is no longer Markdown-fenced at the current head, but its `DynamicMachineModel` import is unresolved in the inspected `machine_models.py`.
- `__init__.py` imports `DynamicState`, while the current state-vector implementation defines `DynamicStateVector`.
- `AUDIT_STATUS_2026-09-12_FINAL_CLOSURE.md` explicitly records unresolved `GF-AUD-019` and an open SLD contextual hover/readout capability.
- `GF-EDM-069` source correction routes protection decisions through Application, but its test was documented as not executed.

## Root-cause clusters

1. Authoritative Core vs presentation authority
2. Application mutation/read boundary
3. Parallel SLD/equipment/terminal representations
4. Endpoint/identity propagation
5. Workspace/panel placement authority
6. Prepared numerical boundary
7. Engineering-unit/PU basis ambiguity
8. Persistence and legacy migration
9. Study-result identity/provenance
10. Short Circuit preparation
11. Protection measurement/preparation
12. SLD projection ownership and presentation identity
13. SLD command ownership and project-load reconciliation


## Phase A — Single Application Mutation Authority — 2026-09-18

**Remediation state:** AGENT CORRECTED → RE-AUDIT REQUIRED

This correction pass addresses the confirmed Phase A registration/authority defects without declaring architectural verification.

| Finding / lineage | Correction | Affected files | Status |
|---|---|---|---|
| GF-MASTER-0037 — historical Application mutation findings | Controller already delegates execution/history through Application; the Application command registry was strengthened so duplicate handler ownership is rejected rather than silently tolerated. | ui/core/controller.py; core/application/application.py; core/application/command_manager.py | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-MASTER-0042 — historical control findings | Control command handlers are now composed into the same Application CommandManager registry as model/protection handlers at the Application composition root. | core/application/bootstrap.py; core/application/control_command_handlers.py; core/application/services/control_service.py | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-MASTER-0037 / GF-MASTER-0042 — command authority/registration lineage | Model, relay-protection, protection-configuration, and control handler families now pass through one duplicate-rejecting registration function before CommandManager construction. | core/application/bootstrap.py | AGENT CORRECTED → RE-AUDIT REQUIRED |
| Phase A SLD registration dependency | SLD registration remains attached to the same Application CommandManager; duplicate SLD ownership is now an explicit registration error rather than silently skipped. Full composition-root/static consumer reconciliation remains outstanding. | core/application/application.py; core/application/sld_command_handlers.py | AGENT CORRECTED → RE-AUDIT REQUIRED |

### Phase A remaining findings

- Full repository-wide static proof that no UI/tool/plugin path owns or invokes a second mutation authority is still required.
- ToolManager currently receives the canonical Application and does not expose a command manager in its constructor; consumer-level tracing of all tool factories remains required.
- PluginContext currently carries gridforge_application and no command_manager field, but all plugin consumers must still be traced before the Phase A authority finding can be re-audited.
- SLD handlers are registered when SLDService is attached after the initial Application composition; this is the same Application CommandManager, but the staged registration lifecycle must be reconciled during the remaining Phase A audit rather than assumed closed.
- No tests, CI, or application execution were run during this correction pass.

> Verification: none. These entries record source corrections only. The subsequent static re-audit must establish the complete consumer graph and may reopen any finding where an executable parallel authority remains.


## 2026-09-19 Workflow/Project/Study Remediation Ledger

The historical finding IDs below are required by the current remediation pass but are not present verbatim in the canonical register rows on this branch baseline. They are preserved here rather than silently discarded. Status is intentionally **VERIFIED** until the mandated static re-audit completes.

| Finding ID | Module | File | Symbol | Category | Severity | Expected | Actual | Root Cause | Impact | Required Correction | Architecture Constraint | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-STUDY-3AZ-005 | Application | core/application/study.py | StudyRequest / StudyResult / StudyService | Study scope | HIGH | Study execution/results are project-generation scoped and provenance-bearing | Results were keyed only by study_id and lifecycle events lacked enforced scope | Study service had global UUID-only storage | Cross-project study/result ambiguity | Add project_id, activation_generation, source_revision and scoped storage/lookup | One authoritative Application study boundary | Static source re-audit required | VERIFIED |
| GF-STUDY-3AZ-002 | Application | core/application/study.py; core/application/application.py | StudyService / Application.execute_study | In-flight study lifecycle | HIGH | Project transition cannot occur while a project-bound study is active | Transition policy was implicit | No explicit relationship between active studies and lifecycle transition | A study could outlive its project generation | Explicitly block new/open/close while active studies exist | Project lifecycle and study orchestration remain Application-owned | Static source re-audit required | VERIFIED |
| GF-DYN-3AZ-001 | Application/Dynamics | core/application/study_preparation.py; core/application/application.py | StudyPreparationService / capture_project_snapshot | Study snapshot | CRITICAL | Study preparation consumes a captured project snapshot, not lifecycle.network | Preparation accepted a live Network provider | Study boundary resolved mutable active state lazily | Study could follow another active project | Capture detached Network plus dynamic-model snapshot at study start | No live Network inside detached study input | Static source re-audit required | VERIFIED |
| GF-DYN-3AZ-002 | Dynamics | core/analysis/dynamic_model_association.py | DynamicMachineModelAssociation | Provenance | HIGH | Dynamic associations identify project and activation generation | Associations had no authoritative project provenance fields | Registry scope existed only implicitly | Dynamic model leakage across projects | Add immutable project_id and activation_generation and stamp persistence boundary | Registry remains outside Network topology | Static source re-audit required | VERIFIED |
| GF-DYN-3AZ-003 | Persistence/Dynamics | core/persistence/project_persistence.py | ProjectPersistenceService.load | Dynamic persistence | HIGH | Loaded dynamic associations are stamped to the candidate project before activation | Loader reconstructed associations without project scope | Persistence boundary did not carry project provenance into associations | Cross-project dynamic state ambiguity | Supply candidate project_id and generation at reconstruction, install only on activation | Candidate load is side-effect free | Static source re-audit required | VERIFIED |
| GF-PERSIST-3AZ-001 | Persistence | core/application/project_lifecycle.py | ProjectLifecycleService | Project activation | CRITICAL | Candidate project state is validated before activation | Validation was absent as an explicit lifecycle hook | Loading and activation were coupled | Invalid candidate could mutate active runtime | Add candidate validation boundary before runtime replacement | One Application-owned activation authority | Static source re-audit required | VERIFIED |
| GF-PERSIST-3AZ-003 | Persistence | core/application/project_lifecycle.py; core/application/application.py | ProjectLifecycleService / SLD activation | SLD activation | CRITICAL | SLD binding participates in project activation | Binding was performed after lifecycle return | Application activation was split between lifecycle and SLD setup | Partial project presentation activation possible | Move SLD bind/detach behind lifecycle activation callback | One persistent SLD mutation authority | Static source re-audit required | VERIFIED |
| GF-APP-3AZ-004 | Application | core/application/application.py; core/application/project_lifecycle.py | _replace_runtime / activation | Revision authority | HIGH | Revision reset is explicit project activation state, not runtime replacement side effect | _replace_runtime reset revision implicitly | Runtime replacement and revision lifecycle were coupled | Revision state could reset independently of project activation | Remove implicit reset and reset only after successful new/open/close lifecycle transition | Application owns project revision state | Static source re-audit required | VERIFIED |
| GF-APP-3AW-004 | Application | core/application/events.py; core/application/application.py | Project/Study events | Event provenance | HIGH | Lifecycle/study events identify project generation | Events relied on loosely populated metadata | Provenance was not enforced at the study/lifecycle boundary | Stale events could be misinterpreted | Emit consistent project_id and activation_generation | Semantic Application event path only | Static source re-audit required | VERIFIED |
| GF-APP-3AW-005 | Application | core/application/study.py; core/application/application.py | Study result lookup | Result authority | HIGH | Result access is project-generation scoped | study_result previously accepted only study_id | Result store was globally keyed | Cross-project result retrieval ambiguity | Require project_id and activation_generation for lookup/cancel | No global unscoped study-result authority | Static source re-audit required | VERIFIED |


## 2026-09-19 Static Re-audit — New Findings

| Finding ID | Module | File | Symbol | Category | Severity | Expected | Actual | Root Cause | Impact | Required Correction | Architecture Constraint | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-REMED-20260919-001 | Application | core/application/project_lifecycle.py; core/application/bootstrap.py | ProjectLifecycleService activation | Transaction/activation | CRITICAL | Candidate activation is all-or-nothing with rollback of every project-bound service | Candidate validation and presentation binding now occur before runtime replacement, but runtime/state callbacks still mutate Application services without a complete rollback contract | Existing callback API separates validation from activation but has no transaction object spanning Network, dynamic registry, protection runtime, SLD, revision, and command history | A late activation failure can still leave partial project-bound state | Introduce one Application-owned activation transaction/staged runtime commit with explicit rollback or failure-safe candidate swap | One authoritative project activation boundary | Static re-audit: unresolved | RE-AUDIT REQUIRED |
| GF-REMED-20260919-002 | SLD/UI | ui/sld/sld_read_synchronizer.py | SLDReadSynchronizer | Persistent SLD mutation authority | CRITICAL | Read/projection synchronization must not mutate persistent SLDDocument state | Synchronizer still creates/removes/updates SLDDocument nodes and connections from Application read models | Legacy read synchronizer remains a second document mutation path | Persistent SLD state can bypass Application SLD commands/transactions | Convert to read-only projection adapter or remove after complete consumer tracing | Exactly one persistent SLD mutation route through SLDService | Static re-audit: unresolved | RE-AUDIT REQUIRED |
| GF-REMED-20260919-003 | SLD/UI | ui/sld/sld_read_synchronizer.py | _synchronize_connections | Topology presentation projection | HIGH | All required topology-bearing equipment has an explicit presentation mapping | Current synchronizer branch mapping remains limited to LINE/CABLE/TRANSFORMER | Existing projection vocabulary was narrower than the frozen topology-bearing equipment contract | Breaker/switch/disconnector/fuse presentation relationships may remain incomplete | Reconcile authoritative presentation mapping without making SLD authoritative for topology | Core topology remains authoritative | Static re-audit: unresolved | RE-AUDIT REQUIRED |
| GF-REMED-20260919-004 | Dynamics/Application | repository call sites | DynamicMachineModelAssociation construction | API migration | HIGH | Every association constructor/binder supplies authoritative project provenance | Association now requires project_id/activation_generation, but a repository-wide constructor consumer sweep could not be completed through the available source API | Provenance was introduced at the model boundary without executable repository-wide callsite verification | Existing consumers may still construct unscoped associations | Trace and reconcile every constructor/bind/persistence call site | Dynamic registry remains project-scoped and outside Network topology | Static re-audit: unresolved | RE-AUDIT REQUIRED |


## 2026-09-19 Static Re-audit — Persistence Status Correction

| Finding ID | Module | File | Symbol | Category | Severity | Expected | Actual | Root Cause | Impact | Required Correction | Architecture Constraint | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-PERSIST-20260919-005 | Persistence | core/persistence/project_persistence.py | ProjectPersistenceService | Persistence package integrity | CRITICAL | Canonical manifest.json + project.json package, provenance preservation, atomic replacement, and rollback-safe failed writes | Source-level package structure and atomic replacement are present, but the current source requires independent static re-audit; remediation history is not verification evidence | Persistence remediation was treated as verified without a fresh current-head audit | Corrupt, incomplete, or stale project packages could compromise lifecycle reconstruction | Independently re-audit the complete persistence implementation and package contract | manifest.json + project.json remain authoritative; no transient Qt/QGraphics state is persisted | Static source re-audit required | RE-AUDIT REQUIRED |

## GF-REMED-20260919-006

| Field | Value |
|---|---|
| Finding ID | GF-REMED-20260919-006 |
| Severity | CRITICAL |
| Area | Application / Project Lifecycle |
| Files | core/application/project_lifecycle.py; core/application/bootstrap.py |
| Symbol | ProjectLifecycleService |
| Category | Lifecycle Contract / Missing Helper |
| Expected | Every invoked lifecycle helper is defined and candidate activation is validated before publication. |
| Actual | new_project() and open_project() invoked _validate_candidate() and _create_presentation(), but these helpers were absent from the affected implementation at the time of finding. |
| Root cause | Activation transaction remediation introduced calls to lifecycle helpers without completing the corresponding class contract. |
| Impact | Project lifecycle implementation was internally incomplete and could not be considered statically ready. |
| Required correction | Implement/reconcile the helpers through the existing Application-owned validator and presentation factory contracts, then re-audit the complete activation workflow. |
| Architecture constraint | Application owns lifecycle orchestration. Core remains authoritative engineering state. UI must not become a lifecycle authority. Exactly one project activation transaction boundary. |
| Status | AGENT CORRECTED → RE-AUDIT REQUIRED |


## GF-REMED-20260919-007

| Field | Value |
|---|---|
| Finding ID | GF-REMED-20260919-007 |
| Severity | CRITICAL |
| Category | Application Lifecycle / API Contract |
| Expected | ProjectLifecycleService and bootstrap must use one matching, fully-defined activation transaction contract. |
| Actual | bootstrap passed activation_transaction=activate_project_transaction while ProjectLifecycleService did not accept that parameter; the lifecycle constructor also required the activate_network callback but bootstrap had not supplied it. |
| Required correction | Use ProjectLifecycleService._activate_candidate() as the single activation transaction boundary, supply the existing activate_network and project_state_activator callbacks, and remove the dangling activation_transaction path. |
| Status | AGENT CORRECTED → RE-AUDIT REQUIRED |

## GF-REMED-20260919-008

| Field | Value |
|---|---|
| Finding ID | GF-REMED-20260919-008 |
| Severity | CRITICAL |
| Category | Application Lifecycle / Missing Implementation |
| Expected | Every referenced activation callback must have one authoritative implementation and rollback contract. |
| Actual | bootstrap referenced activate_project_transaction, but no corresponding implementation existed; the actual rollback-bearing callbacks are activate_network and activate_project_state. |
| Required correction | Make _activate_candidate() the sole transaction boundary and wire the existing rollback callbacks into that boundary. |
| Status | AGENT CORRECTED → RE-AUDIT REQUIRED |

## GF-REMED-20260919-009

| Field | Value |
|---|---|
| Finding ID | GF-REMED-20260919-009 |
| Severity | CRITICAL |
| Category | SLD / Projection Source Integrity |
| Expected | SLDReadSynchronizer must use the canonical SLD semantic vocabulary and all referenced symbols must be defined/imported. |
| Actual | semantic_type, _BRANCH_TYPES and _PROJECTION_SOURCE were referenced without definitions/imports in the synchronizer module. |
| Required correction | Remove the discarded connection-building path from SLDReadSynchronizer; keep semantic mapping in SLDReadAdapter/sld_vocabulary and topology endpoint representation in SLDProjection, with canonical topology types sourced from sld_vocabulary. |
| Status | AGENT CORRECTED → RE-AUDIT REQUIRED |


## 2026-09-19 Static Remediation Batch — GF-REMED-20260919-010 through 013

The following findings were source-corrected in the current remediation batch. They remain **AGENT CORRECTED → RE-AUDIT REQUIRED**. No runtime, test, CI, startup, or GUI execution is verification evidence for this batch.

| Finding ID | Module | File | Symbol | Category | Severity | Expected | Actual | Root Cause | Impact | Required Correction | Architecture Constraint | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-REMED-20260919-010 | Application | core/application/revision_service.py | RevisionService.snapshot_state / restore_state | Revision transaction state | HIGH | Exactly one snapshot/restore pair preserves current revision, persisted revision state, undo/redo history, and persisted generation; restore validates structure; runtime replacement does not reset revision | Duplicate snapshot/restore definitions created source ambiguity; the latter definitions silently shadowed the former | Incomplete consolidation of the activation rollback contract | Revision rollback semantics were source-ambiguous and could drift from the activation contract | Retain one complete validated snapshot/restore pair; keep revision reset explicit to project activation | Revision authority remains Application-owned; no Core/UI/SLD/CommandManager revision authority | Static source correction only; independent static re-audit required | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-011 | UI/SLD | ui/projection/projection_registry.py; ui/sld/sld_projection_manager.py; ui/sld/sld_read_synchronizer.py | ProjectionRegistry; SLDProjectionManager; SLDReadSynchronizer | Projection registry API / stale reconciliation | HIGH | Projection lifecycle is centrally managed and stale projections can be enumerated and removed without private registry access | Synchronizer attempted registry.values(), but the registry exposed no values API and cleanup reached through private internals | Registry read API and projection lifecycle boundary were incomplete | Stale projection cleanup was effectively a no-op and synchronizer depended on private registry structure | Add read-only domain-scoped registry enumeration and route reconciliation through SLDProjectionManager | Application read model → SLDReadAdapter → SLDProjectionManager → ProjectionRegistry; no Core mutation | Static source correction only; independent static re-audit required | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-012 | UI/SLD | ui/sld/sld_read_synchronizer.py | SLDReadSynchronizer synchronization methods | Read/projection boundary | HIGH | Read projection synchronization is independent of persistent SLDDocument state | Every synchronizer entry point required an SLDDocument solely to assert it was unused | Legacy API carried a misleading persistent-presentation dependency | Read projection appeared coupled to persistent SLD state and obscured the single persistent SLD mutation path | Remove SLDDocument from network/protection/element synchronization APIs and update callers; keep persistent SLD mutation behind Application SLD commands/services | Read projection remains presentation-only; SLDDocument stays outside the read-only path | Static source correction performed; repository-wide caller re-audit remains required; no execution performed | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-013 | UI/SLD | ui/sld/sld_read_synchronizer.py; ui/sld/sld_projection_manager.py; ui/projection/projection_registry.py | SLDReadSynchronizer; SLDProjectionManager; ProjectionRegistry | Projection-domain ownership | HIGH | Network and protection synchronization reconcile only their own projection domains without call-order assumptions | Network reconciliation treated the entire shared registry as network-owned and could remove protection relay projections | Shared registry lacked explicit ownership namespaces | Network/protection projection lifecycles interfered with each other | Introduce centrally defined NETWORK and PROTECTION projection domains, register ownership explicitly, and reconcile through domain-scoped manager APIs | Stable Core object identity remains the projection key; canonical SLD vocabulary remains unchanged; protection remains Application-owned; projections remain presentation-only | Static source correction performed; independent static re-audit required; no execution performed | AGENT CORRECTED → RE-AUDIT REQUIRED |


## 2026-09-19 Static Remediation Batch — GF-REMED-20260919-014 through 018

The following findings were source-corrected in this remediation batch. They remain **AGENT CORRECTED → RE-AUDIT REQUIRED**. No tests, CI, application startup, GUI, or runtime execution was performed.

| Finding ID | Module | File | Symbol | Category | Severity | Expected | Actual | Root Cause | Impact | Required Correction | Architecture Constraint | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-REMED-20260919-014 | Application | core/application/revision_service.py; core/application/application.py; core/application/bootstrap.py | RevisionService; Application revision consumers | Revision API / transition authority | CRITICAL | RevisionService exposes the complete canonical consumer contract for command success, undo, redo, presentation changes, project reset, snapshot/restore, and persistence; exact immutable revision transitions are preserved | Consumers invoked methods that were absent from RevisionService; revision transition authority was incomplete and topology vocabulary was duplicated in Application | Revision service consolidation was incomplete after earlier remediation | Application source contract was internally inconsistent; dirty, undo/redo, presentation, persisted-generation, and activation rollback semantics could not be centrally guaranteed | Implement the complete RevisionService consumer API; derive command revisions centrally; preserve exact undo/redo transitions; reset only during successful project activation; keep snapshot/restore and persisted-generation state authoritative | One Application-owned RevisionService; immutable ProjectRevision; no duplicate revision/history authority; _replace_runtime() does not reset revision state | Static source correction performed; independent static re-audit required | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-015 | Application | core/application/revision_service.py; core/application/application.py | RevisionService.is_topology_command; Application._is_topology_command | Topology revision classification | HIGH | All authoritative breaker topology mutations participate in topology revision semantics through one canonical command vocabulary | Application classified breaker commands separately while RevisionService omitted the breaker family | Topology classification vocabulary was duplicated across Application and RevisionService | Breaker switching mutations could update model revision without updating topology revision | Centralize topology classification in RevisionService and include the breaker command family; Application delegates classification to the canonical service | Model, topology, presentation, and persisted revisions remain distinct; no divergent topology command lists | Static source correction performed; independent static re-audit required | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-016 | Composition/UI | main.py; ui/sld/sld_read_synchronizer.py | SLDReadSynchronizer composition | Obsolete read API | CRITICAL | Composition root passes Application read models to SLDReadSynchronizer; persistent SLDDocument is never an input to the read synchronizer | main.py passed SLDDocument plus NetworkReadModel using the obsolete call shape | Composition root was not reconciled after the read/projection API correction | Startup composition retained a stale API contract and blurred persistent presentation state with read projection state | Attach the Application once to SLDReadSynchronizer and call synchronize_network/synchronize_protection with Application read models only | Application → read model → SLDReadSynchronizer/Adapter → SLDProjectionManager; no SLDDocument in read synchronization | Static source correction performed; independent static re-audit required; no startup execution performed | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-017 | UI/SLD | ui/events/sld_update_coordinator.py | SLDUpdateCoordinator | Persistent SLD dependency | HIGH | Coordinator consumes Application semantic events/read models and never owns or caches persistent SLDDocument state | Coordinator constructor and lifecycle retained an SLDDocument dependency and document binding/detachment state | Earlier read-path correction did not complete coordinator responsibility reconciliation | Read/projection coordination appeared to retain a second presentation-state dependency | Remove SLDDocument from coordinator construction and lifecycle; route projection refresh through Application read models and domain-scoped synchronizer APIs | Persistent SLDDocument mutation remains exclusively behind Application SLD commands/SLDService; coordinator is read/projection-only | Static source correction performed; independent static re-audit required | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-018 | UI/SLD/Application | core/application/application.py; core/application/events.py; ui/events/sld_update_coordinator.py; ui/sld/sld_read_synchronizer.py | ProtectionChanged; SLDUpdateCoordinator; SLDReadSynchronizer | Protection projection event/read workflow | HIGH | Relay/protection semantic changes and project activation drive ProtectionReadModel → SLDReadAdapter.protection() → domain-scoped protection projection reconciliation without affecting network projections | Network projection refresh existed, but protection changes had no established coordinator event path and protection configuration commands emitted no projection-driving semantic event | Protection read/projection synchronization was implemented at the adapter/manager level but not connected to the Application semantic event workflow | Protection relay/configuration projection could become stale while network projection refreshed; domain ownership was not exercised end-to-end | Add the missing Application protection semantic event for protection configuration commands; route relay Element events and ProtectionChanged/project-load events to synchronize_protection_from_application(); retain domain-scoped reconcile methods | Application read/event boundary remains authoritative; protection and network projection domains are independently reconciled; no persistent SLD mutation in read path; no second SLD authority | Static source correction performed; independent static re-audit required | AGENT CORRECTED → RE-AUDIT REQUIRED |
| GF-REMED-20260919-019 | Application / UI / SLD | core/application/read_service.py; core/application/read_models.py; ui/sld/sld_read_adapter.py; ui/sld/sld_read_synchronizer.py; ui/sld/sld_projection_manager.py; ui/projection/projection_registry.py; main.py | Projection Domain Ownership / Read Model Contract | Network/Protection projection identity collision | CRITICAL | NetworkReadService excludes Relay from the NETWORK presentation collection; Relay remains authoritative in Core Network and is exposed through ProtectionReadService for the PROTECTION presentation domain; domain-scoped SLD reconciliation remains independent and order-safe | NetworkReadService previously exposed relays through NetworkReadModel while ProtectionReadService exposed the same Relay identities through ProtectionReadModel, causing incompatible projection-domain registration for one Core object ID | Read-model element ownership and presentation projection-domain ownership were not fully reconciled | Initial SLD synchronization could register the same Relay identity through NETWORK and PROTECTION paths, violating explicit projection-domain ownership | Make Relay protection-domain presentation-owned by excluding relays only from NetworkReadService.network(); retain Relay Core ownership, ProtectionReadService, protection configuration/studies, and relay-specific Application reads; preserve explicit ProjectionRegistry domain validation and domain-scoped reconciliation | Core remains authoritative; Application owns read orchestration; NETWORK contains authoritative electrical/network presentation projections; PROTECTION contains authoritative protection presentation projections; persistent SLDDocument remains outside read synchronization; no duplicate identity authority | Static source correction performed; independent static source re-audit required; tests, CI, startup, and runtime execution intentionally not performed | AGENT CORRECTED → RE-AUDIT REQUIRED |



## 2026-09-19 Static Remediation Batch — GF-REMED-020

| Field | Value |
|---|---|
| Finding ID | GF-REMED-20260919-020 |
| Domain | Application / UI / SLD |
| Subsystem | Read Model Contract / Projection Domain Ownership |
| Severity | HIGH |
| Title | Network single-element Relay read violates Protection presentation-domain ownership |
| Root cause | The bulk NetworkReadService.network() path was corrected to exclude Relays, but the generic single-element NetworkReadService.element() path still accepted relay/relays aliases and could return an ElementReadModel(RELAY). SLDReadSynchronizer.synchronize_element_from_application() then projected that result into ProjectionDomain.NETWORK, recreating the presentation-domain ownership violation through a single-element workflow. |
| Impact | A Relay could still be projected under the NETWORK presentation domain through the generic single-element synchronization path, creating a second presentation ownership path and potentially conflicting with the canonical PROTECTION Relay projection. |
| Required correction | Reconcile the single-element Application read contract with the established presentation ownership. Relay presentation reads use the ProtectionReadService/read_relay path and cannot silently enter the NETWORK projection domain. Preserve Core Network Relay ownership and the existing ProtectionReadModel/RelayReadModel architecture. Ensure SLD single-element synchronization rejects Relay as a NETWORK element and uses the explicit protection projection path for ProtectionReadModel inputs. |
| Architecture constraints | Core remains authoritative for physical Relay objects. Application remains the UI↔Core read boundary. Relay presentation ownership is PROTECTION. Network presentation reads exclude Relay. ProjectionRegistry remains strict and domain-aware. SLDReadSynchronizer remains read/projection-only. No direct Core access from SLD. No duplicate read/projection architecture. |
| Verification | Static source inspection only. Tests, CI, startup and runtime execution are deferred. |
| Status | AGENT CORRECTED → RE-AUDIT REQUIRED |

## GF-INT-20260919-022

| Field | Value |
|---|---|
| Finding ID | GF-INT-20260919-022 |
| Severity | CRITICAL |
| Category | Application Integration / Lifecycle Contract |
| Finding | `Application.attach_sld_service()` invokes `ProjectLifecycleService.configure_presentation_activator()`, but the current `ProjectLifecycleService` exposed no such configuration method despite already defining `presentation_activator` and `_activate_presentation()` support. |
| Root Cause | The presentation activation lifecycle contract was partially implemented: the internal callback storage/activation path existed, but the public configuration boundary required by the Application composition path was missing. |
| Impact | Application startup fails during SLD service attachment before the UI can be constructed. |
| Required Correction | Complete the existing `ProjectLifecycleService` presentation-activator configuration contract and preserve the single `_activate_candidate()` project activation transaction. |
| Architecture Constraint | No second lifecycle transaction, no UI→Core mutation, no SLD→Core mutation, no direct Core access from SLD/UI, and no bypass of Application orchestration. |
| Verification State | AGENT CORRECTED → RE-AUDIT REQUIRED |
| Verification | Static source inspection only. Runtime/test verification remains deferred according to the current stabilization policy. |

## GF-UI-20260919-023

| Field | Value |
|---|---|
| Finding ID | GF-UI-20260919-023 |
| Severity | HIGH |
| Category | UI / Canvas / PySide6 Integration / Hit Testing |
| Finding | Canvas hit testing invoked `QGraphicsScene.items(QPointF)`. PySide6 overload dispatch reached a runtime type expression containing `collections.abc.Sequence[QPoint]`, producing repeated FIXME diagnostics during mouse movement. |
| Affected path | `GraphicsView` → `MouseEventAdapter` → scene hit test → PySide6 overload dispatcher |
| Root Cause | PySide6 runtime overload resolution incompatibility with the parameterized generic in the selected Qt overload path. |
| Impact | Repeated FIXME diagnostics during Canvas mouse movement and a defective/fragile Qt hit-testing integration path. |
| Required Correction | Replace the problematic point overload with the scalar rectangle query overload using a small indexed candidate region, then apply the exact `QGraphicsItem.contains()` point test before existing selectable-ancestor resolution. Preserve descending stacking order and stable presentation identity. |
| Architecture Constraint | Hit testing remains entirely within the UI/Canvas presentation boundary. No QGraphics/Qt objects enter Core. No direct UI→Core mutation. No Application bypass. |
| Verification State | AGENT CORRECTED → RE-AUDIT REQUIRED |
| Verification | Static source inspection only. Tests, CI, application startup, GUI execution, and runtime verification were not performed. |

### GF-UI-20260919-023 correction notes

- `ui/canvas/mouse_event_adapter.py` was corrected.
- The affected call no longer dispatches `QGraphicsScene.items(QPointF)`.
- The replacement uses the six-argument scalar rectangle overload: `(x, y, w, h, ItemSelectionMode, SortOrder)`, avoiding the geometry overload that triggered the parameterized-generic `isinstance()` diagnostic.
- The candidate query remains Qt scene-indexed and uses `Qt.DescendingOrder`, preserving topmost-first candidate ordering.
- A precise `QGraphicsItem.contains()` check after `mapFromScene(scene_position)` restores exact point-hit semantics rather than treating the small candidate rectangle as a selection tolerance.
- Existing selectable-ancestor traversal and `object_id` extraction remain unchanged.
- Repository inspection found no additional direct `QGraphicsScene.items(QPointF)` hit-test invocation in the affected Canvas path. `ui/core/snap_system.py` uses `scene.items()` with no geometry argument and is unrelated to this overload defect.
- The requested `ui/canvas/tool_manager.py`, `ui/canvas/tool_base.py`, and `ui/canvas/snap_system.py` paths do not exist on `main`; the corresponding current implementations are `ui/core/tool_manager.py`, `ui/tools/tool_base.py`, and `ui/core/snap_system.py`. They were inspected and no same defective point-overload call was identified.


## Batch 3 — Core Integration Boundary Remediation Addendum

**Static remediation baseline:** current main after Batch 3 source corrections.
**Verification policy:** no tests, CI, application startup, GUI execution, or runtime verification were performed.

| Finding ID | Severity | Affected area | Status | Static disposition / remaining risk |
|---|---|---|---|---|
| GF-INT-018 | HIGH | Terminal ownership | REMEDIATED — VERIFICATION DEFERRED | Terminal ownership is enforced by Core validation and Network registration; runtime verification remains deferred. |
| GF-INT-020 | HIGH | Endpoint ownership | REMEDIATED — VERIFICATION DEFERRED | Terminal endpoints are restricted to Core ElectricalObjects and Network membership tokens reject cross-Network/unregistered endpoints. |
| GF-INT-021 | HIGH | Network identity | REMEDIATED — VERIFICATION DEFERRED | NetworkRegistry now owns one canonical identity map and rejects unsupported/arbitrary ID-bearing objects. |
| GF-INT-022 | MEDIUM | File headers | REMEDIATED — VERIFICATION DEFERRED | Required headers added to affected Batch 3 files. |
| GF-INT-023 | MEDIUM | File headers | REMEDIATED — VERIFICATION DEFERRED | Required headers added to newly touched Batch 3 files. |
| GF-INT-024 | HIGH | Registration/identity | REMEDIATED — VERIFICATION DEFERRED | Registration validates Core type, identity, structure, ownership, endpoint membership, and duplicate identity. |
| GF-INT-025 | HIGH | Deletion invariants | REMEDIATED — VERIFICATION DEFERRED | Registry removal rejects deletion while another authoritative Terminal references the object. |
| GF-INT-027 | HIGH | Canonical lookup | REMEDIATED — VERIFICATION DEFERRED | Added unambiguous canonical lookup by global object identity while preserving typed compatibility lookup. |
| GF-INT-028 | HIGH | Identity uniqueness | REMEDIATED — VERIFICATION DEFERRED | Global duplicate identity is rejected across supported Network object families. |
| GF-INT-029 | HIGH | Endpoint type safety | REMEDIATED — VERIFICATION DEFERRED | Terminal-to-Terminal endpoints and arbitrary non-Core objects are rejected. |
| GF-INT-030 | HIGH | Registration boundary | REMEDIATED — VERIFICATION DEFERRED | Network registration is the authoritative admission boundary. |
| GF-INT-031 | HIGH | Persistence reconstruction | REMEDIATED — VERIFICATION DEFERRED | Persisted endpoint references resolve through ModelTypeRegistry plus canonical Network identity lookup. |
| GF-INT-032 | HIGH | Bus/topology semantics | OPEN — ARCHITECTURAL AMBIGUITY | Current TopologyManager represents graph vertices directly with Bus objects. The frozen requirement distinguishes Bus from Topological Node; changing this safely requires an explicit canonical topology-node contract. |
| GF-INT-033 | HIGH | Endpoint resolution | REMEDIATED — VERIFICATION DEFERRED | Valid unconnected terminals resolve as absence; malformed endpoint relationships remain distinct errors. |
| GF-INT-035 | HIGH | EquipmentType | REMEDIATED — VERIFICATION DEFERRED | EquipmentType is derived from terminal-owning Core model types instead of an incomplete hand-maintained list. |
| GF-INT-036 | HIGH | Project validation | REMEDIATED — VERIFICATION DEFERRED | Core Network validation and cross-domain project validation are enforced at load/save boundaries. |
| GF-INT-037 | HIGH | Persistence endpoint mapping | REMEDIATED — VERIFICATION DEFERRED | Independent persistence endpoint-type mapping was removed; persisted types resolve through ModelTypeRegistry. |
| GF-INT-038 | HIGH | Terminal role contract | OPEN — PARTIAL RECONCILIATION | Canonical role spellings and case sensitivity are documented in Terminal, but legacy model literals remain distributed across model implementations. |
| GF-INT-039 | HIGH | Deletion/reference integrity | REMEDIATED — VERIFICATION DEFERRED | Authoritative removal rejects external Terminal references to the removed object. |
| GF-INT-040 | HIGH | Transaction rollback | REMEDIATED — VERIFICATION DEFERRED | Rollback failure places CommandManager in DEGRADED state and blocks further command execution. |
| GF-INT-041 | HIGH | Undo recovery | REMEDIATED — VERIFICATION DEFERRED | Zero-operation undo failure restores history; partial inverse execution marks the boundary DEGRADED. |
| GF-INT-042 | HIGH | Post-commit history | REMEDIATED — VERIFICATION DEFERRED | History-recording failure after Core commit is surfaced and places CommandManager in DEGRADED state. |
| GF-INT-043 | HIGH | Save validation | REMEDIATED — VERIFICATION DEFERRED | Persistence save performs Network/topology and cross-domain validation before package replacement. |
| GF-INT-044 | HIGH | Load validation | REMEDIATED — VERIFICATION DEFERRED | Loaded Network is reconstructed, rebuilt, validated, and cross-domain project state is validated before LoadedProject is returned. |
| GF-INT-045 | HIGH | Command history/project transitions | REMEDIATED — VERIFICATION DEFERRED | Project activation replaces the project-bound CommandManager runtime, preventing old history from surviving into a new Network. |
| GF-INT-046 | HIGH | Revision/project transitions | REMEDIATED — VERIFICATION DEFERRED | Project activation resets RevisionService separately from CommandManager history. |
| GF-INT-047 | HIGH | Dynamic project state | REMEDIATED — VERIFICATION DEFERRED | Application bootstrap owns DynamicMachineModelRegistry, activates loaded state, and supplies it to persistence save. |
| GF-INT-048 | HIGH | Protection project state | REMEDIATED — VERIFICATION DEFERRED | Application bootstrap owns ProtectionConfigurationService state, activates loaded configuration, and supplies it to persistence save. |
| GF-INT-049 | MEDIUM | Persistence filesystem durability | REMEDIATED — VERIFICATION DEFERRED | Existing temporary-package replacement is retained; documentation distinguishes exception-safe replacement from process-crash/filesystem durability. |

**Batch 3 register rule:** no Batch 3 finding is marked VERIFIED from source modification alone. GF-INT-032 and GF-INT-038 remain open pending explicit architectural reconciliation.


## Batch 3 — Static Correction Re-audit — 2026-09-19

This addendum reflects the current main branch after the Batch 3 source corrections. No tests, CI, application startup, GUI execution, or runtime verification were performed.

| Finding | Static status | Disposition |
|---|---|---|
| GF-INT-031 | REMEDIATED — VERIFICATION DEFERRED | Deferred persisted object references are recursively resolved through ModelTypeRegistry and the canonical NetworkRegistry identity map before topology validation. |
| GF-INT-032 | OPEN — STATIC GAP | Application endpoint/object-type coverage is not yet one complete authoritative taxonomy; the current Application command set does not cover every Core/persistence object family. |
| GF-INT-033 | REMEDIATED — VERIFICATION DEFERRED | Persisted references and terminal endpoints resolve by canonical Core identity and explicit persisted type checks. |
| GF-INT-036 | REMEDIATED — VERIFICATION DEFERRED | Reconstructed Network and project-level dynamic/protection state are validated before lifecycle activation. |
| GF-INT-037 | OPEN — STATIC GAP | ModelTypeRegistry, NetworkRegistry aliases/collections, and Application command-type coverage remain separate mapping authorities. |
| GF-INT-038 | REMEDIATED — VERIFICATION DEFERRED | Network membership tokens plus canonical registry identity reject cross-Network endpoint references. |
| GF-INT-039 | OPEN — STATIC GAP | Persistence separates registration from connection, but every create/connect/undo/redo mutation path has not been proven to preserve the same explicit lifecycle separation. |
| GF-INT-040 | REMEDIATED — VERIFICATION DEFERRED | ProjectLifecycleService now exposes explicit ROLLBACK_FAILED state and blocks further project transitions until recovery. |
| GF-INT-041 | REMEDIATED — VERIFICATION DEFERRED | CommandManager restores zero-operation undo failures and degrades on partial inverse execution. |
| GF-INT-042 | REMEDIATED — VERIFICATION DEFERRED | Post-commit history failure is surfaced and places CommandManager in DEGRADED state rather than attempting an invalid rollback. |
| GF-INT-043 | REMEDIATED — VERIFICATION DEFERRED | Save validates Network and complete project state before serialization and package replacement. |
| GF-INT-044 | REMEDIATED — VERIFICATION DEFERRED | Dynamic-model and protection references are included in project-level validation; presentation state remains outside Core validation. |
| GF-INT-045 | REMEDIATED — VERIFICATION DEFERRED | RevisionService is marked persisted only after the persistence operation succeeds. |
| GF-INT-046 | REMEDIATED — VERIFICATION DEFERRED | Project activation constructs a fresh CommandManager runtime, establishing a history boundary between projects. |
| GF-INT-047 | REMEDIATED — VERIFICATION DEFERRED | Dynamic model associations are loaded, generation-bound during activation, validated, and supplied back to persistence on save. |
| GF-INT-048 | REMEDIATED — VERIFICATION DEFERRED | Bootstrap wires the real protection configuration service and dynamic registry into lifecycle activation and persistence. |
| GF-INT-049 | REMEDIATED — VERIFICATION DEFERRED | Save writes a complete staged package, fsyncs files, preserves a prior-package backup during replacement, and load can recover that backup after an interrupted replacement. Full filesystem-journal durability remains platform-specific. |
| GF-INT-050 | REMEDIATED — VERIFICATION DEFERRED | Meaningless isinstance(element, object) validation was replaced with explicit Core ElectricalObject validation. |

### Batch 3 closure decision

**Batch 3 is NOT CLOSED.**

The static lifecycle chain is materially corrected, but GF-INT-032, GF-INT-037, and GF-INT-039 remain open. They are retained as explicit findings rather than being inferred closed.

Verification remains **deferred** exactly as required by the remediation scope.

# WF-041-V1–V15 — Plugin Lifecycle Static Re-audit

**Repository:** `pandaraseswari03-collab/GridForge`  
**Branch:** `main`  
**Static-audit head after correction:** `a82e4b35ebbbb6a03d4eedee5a4bf0da5dbfb3f1`  
**Verification mode:** static source inspection only. Tests, CI, application startup, GUI execution, and runtime verification were not performed.

## Scope

The re-audit covered:

- `ui/plugins/plugin_manager.py`
- `ui/plugins/plugin_registry.py`
- `ui/plugins/plugin_state.py`
- `ui/plugins/plugin_events.py`

The frozen ownership chain remains:

`Composition Root → PluginManager → PluginRegistry → PluginStateStore`.

No second lifecycle state store, lifecycle manager, event bus, or `PARTIALLY_INITIALIZED` state was introduced.

## Static event matrix

| Operation | Success path | Failure path |
|---|---|---|
| Load | `LOAD_REQUESTED → LOADED` per newly introduced plugin | `LOAD_REQUESTED → FAILED(operation=load)`; transaction-created registrations are compensated |
| Initialize | `INITIALIZE_REQUESTED → INITIALIZING → plugin.initialize() → StateStore initialized → INITIALIZED` | `INITIALIZE_REQUESTED → INITIALIZING → FAILED(operation=initialize)`; started callbacks receive rollback shutdown compensation |
| Shutdown | `SHUTDOWN_REQUESTED → SHUTTING_DOWN → plugin.shutdown() → StateStore uninitialized → SHUTDOWN` | `SHUTDOWN_REQUESTED → SHUTTING_DOWN → FAILED(operation=shutdown)`; failed plugin remains initialized |
| Disable | successful state transition → `DISABLED` | `FAILED(operation=disable)`; shutdown success is preserved if disable itself fails |
| Unload | `UNLOAD_REQUESTED → shutdown if required → disable if required → unregister → UNLOADED` | `FAILED(operation=unload)` or the underlying lifecycle failure event; `UNLOADED` is never emitted prematurely |
| Rollback | existing shutdown/unload vocabulary with `rollback=true` metadata | rollback failures are retained and aggregated |

## Finding register

| Finding | Affected implementation | Root cause | Correction | Static verification | Residual observation | Status |
|---|---|---|---|---|---|---|
| WF-041-V1 | `PluginManager._emit`; Registry event sink | Registry could externally publish lifecycle events in addition to Manager | Registry lifecycle emission removed; Manager is the sole external publisher | Manager/Registry event ownership statically reconciled | No runtime observer verification | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V2 | `PluginManager._initialize_transaction` | Success/failure event ordering was not transactionally aligned | INITIALIZED follows successful Registry/state transition; FAILED is emitted on callback failure | Event sequence statically traced | Runtime event stream not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V3 | `PluginManager._shutdown_one` | Success event could be separated from actual shutdown semantics | SHUTDOWN is emitted only after successful Registry shutdown | State/event ordering statically traced | Runtime callback behavior not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V4 | `PluginManager.unload` | Unload had no complete request→teardown→unregister boundary | Added UNLOAD_REQUESTED and success-only UNLOADED boundary | Unload path statically traced | Runtime unregister behavior not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V5 | `load/load_many/load_all`; `initialize/initialize_many`; `shutdown/shutdown_all` | Single and bulk operations had separate observability behavior | Shared transaction/helper boundaries established | Single/bulk implementation paths compared | Runtime equivalence not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V6 | `PluginManager._load_plugins` | Loading was not tracked independently from initialization | Explicit `loaded_here` tracking and rollback added | Variable lifecycle and rollback paths statically traced | Runtime dependency failure not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V7 | `PluginManager.load_many` | Bulk-load transaction semantics were implicit | One resolved order is processed through one load transaction | Bulk boundary statically verified | Runtime batch failure not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V8 | `PluginManager._initialize_transaction` | Implicit loads could outlive initialization rollback | Separate `loaded_here` and `initialized_here` scopes now roll back together | Transaction paths statically verified | Runtime compensation not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V9 | `shutdown/shutdown_all` | Shutdown could abort or incorrectly proceed through failed dependency chains | Reverse ordering, dependency blocking, independent continuation, and aggregation implemented | Control flow statically traced | Runtime failure aggregation not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V10 | `PluginManager.enable/disable`; Registry enable/disable | Local Registry operations could become the observable lifecycle boundary | Manager owns orchestration/events; Registry performs local state transition | Ownership and event source statically verified | Runtime state transition not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V11 | `PluginManager.unload` | Inclusive dependant closure could treat target as its own dependant | Target explicitly excluded from registered-dependant guard | Guard statically verified | Runtime dependency graph not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V12 | `PluginManager.unload` | Unload failure stage was not explicit in FAILED events | Deterministic `unload.shutdown`, `unload.disable`, and `unload.unregister` failure operations; success events remain stage-gated | Static event/state paths checked; runtime verification deferred | **REMEDIATED — VERIFICATION DEFERRED** |
| WF-041-V13 | Manager/Registry/StateStore failure paths | Lifecycle failures could diverge from authoritative state | StateStore remains sole state authority; success events are success-gated; failed shutdown does not mark uninitialized | State invariants and failure branches statically checked | Runtime state observation not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V14 | Manager + Registry event paths | Manager and Registry could duplicate externally visible events or publish success prematurely | Registry lifecycle event emission removed; Manager publishes at orchestration boundaries | Event matrix and source ownership statically checked | Runtime event consumer behavior not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V15 | Registry guards; Manager rollback | Cleanup/retry paths risked unsafe state fabrication | Existing idempotent guards preserved; failed-init compensation failure protects the plugin from unsafe unregister | Guard and compensation control flow statically checked | Runtime retry behavior not executed | **CLOSED — STATICALLY VERIFIED** |
| WF-041-V16 | `PluginManager._initialize_transaction`; `PluginRegistry.initialize` | Initialization state-commit/diagnostic failure could trigger duplicate shutdown compensation | Canonical state commit is terminal for failed-init compensation; diagnostic clear is not a post-commit failure point | Static compensation paths checked; runtime verification deferred | **REMEDIATED — VERIFICATION DEFERRED** |

### Architectural residual observation

The Registry retains its existing `event_sink` compatibility parameter, but current Registry lifecycle methods no longer publish lifecycle events through it. This does not create a second event publisher or state authority. Runtime behavior remains intentionally unverified because tests, CI, startup, and GUI execution were explicitly excluded.



## Batch 17 — Persistent SLD/Core Association Validation

### Architectural decision state

Static repository tracing did not establish an authoritative rule selecting automatic SLD-node removal, explicit unresolved/orphan retention, or Core-equipment deletion protection when a persistent SLD node references missing Core equipment.

**ARCHITECTURAL DECISION REQUIRED.**

The correction therefore introduces read-only Application validation that distinguishes `equipment_id=None`, a resolved Core identity, and an unresolved Core identity. It does not delete, repair, rewrite, fabricate, or otherwise resolve the unresolved state.

### Finding register

| Finding | Affected implementation | Root cause | Correction | Static verification | Residual observation | Status |
|---|---|---|---|---|---|---|
| SLD-WF-100 | Persistent SLD/Core deletion and reconciliation policy | Persistent SLD orphan policy is undefined | No deletion, repair, or Core-protection policy was invented; unresolved references remain observable and require architecture decision | Static trace of SLD model, persistence, lifecycle, commands, and audit material | Policy remains undefined | **OPEN** |
| SLD-WF-101 | `core/application/revision_service.py`; Application validation | Dirty/revision semantics did not classify unresolved SLD references | Validation is read-only; presentation revision remains owned by Application command success; unresolved references do not create a second dirty authority | Static revision/validation path reconciliation | No new dirty-state system introduced | **OPEN** |
| SLD-WF-102 | `core/persistence/project_persistence.py` | Persistence did not validate persistent SLD equipment references | Persistence now invokes the Application SLD association validator; unresolved references are diagnosed but not rejected pending orphan policy | Static load/save gate traced | Unresolved-reference policy remains undecided | **OPEN** |
| SLD-WF-103 | `core/application/services/validation_service.py`; `core/application/application.py` | No Application-level SLD association validation gate | Added immutable association-state/result contracts and Application project-validation integration | Static call path and ownership boundary checked | Runtime validation not executed | **OPEN** |
| SLD-WF-104 | `core/application/services/validation_service.py` | `equipment_id=None` semantics were undefined | Explicit `UNREFERENCED` state is distinct from `UNRESOLVED` | Static state vocabulary checked | Meaning remains presentation-policy neutral | **OPEN** |
| SLD-WF-105 | Application command/revision/history and SLD presentation | Independent Core/SLD history can permit association divergence | Existing Application command/history boundary is preserved; no compound Core+SLD deletion was invented without policy | Static command, SLDService, revision, and undo/redo paths checked | Compound deletion policy remains an architecture decision | **OPEN** |
| SLD-WF-106 | `ProjectLifecycleService.discard_project_changes`; persistence/load validation | Discard reloads persisted state but persisted SLD semantic validity was not guaranteed | Discard continues to restore persisted state; association validation now diagnoses unresolved references without silently repairing them | Static discard → load → activation path checked | Guarantee depends on the unresolved-reference policy | **OPEN** |
| SLD-WF-107 | Application validation vs Dynamic/Protection cross-domain checks | SLD validation lacked parity with other cross-domain association validation | SLD association validation now uses the canonical Network identity lookup alongside existing Dynamic/Protection validation | Static cross-domain validation comparison checked | Runtime verification deferred | **OPEN** |

### Static re-audit conclusion

Source correction is present, but Batch 17 is **not closed**. The repository still requires an explicit architectural decision for persistent SLD references whose Core equipment no longer exists. No runtime, test, CI, application-startup, GUI, or runtime verification was performed.


## Batch 18 — Core Equipment / Persistent SLD Deletion Intent and Transaction Boundaries

### Architectural decision state

Static repository tracing found no authoritative engineer-facing policy that makes SLD-node deletion imply Core-equipment deletion, Core-equipment deletion imply persistent SLD deletion, or both actions a single canonical use case. The existing architecture explicitly keeps `RemoveSLDNodeCommand` presentation-only and keeps generic Core delete commands presentation-neutral.

**ARCHITECTURAL DECISION REQUIRED.**

No coordinated Core+SLD deletion command is introduced in Batch 18 because the required policy/intent has not been authoritatively approved. This preserves the existing distinction between presentation-only deletion and Core-only deletion and avoids inventing a compound workflow.

### Finding register

| Finding | Severity | Status | Static evidence / correction |
|---|---|---|---|
| SLD-WF-108 | CRITICAL | **OPEN** | No canonical Application equipment-representation deletion use case was found. Existing `PlaceBusCommand` establishes a compound-command pattern for placement, but no authoritative deletion intent was found. |
| SLD-WF-109 | CRITICAL | **OPEN** | Core deletion and persistent SLD deletion remain independent command/history boundaries. No nested `Application.execute()` composition was introduced. |
| SLD-WF-110 | HIGH | **OPEN** | `SLDController.remove_node()` is explicitly documented and traced as presentation-only; it submits `RemoveSLDNodeCommand` and does not infer equipment deletion. |
| SLD-WF-111 | HIGH | **OPEN** | SLD selection is transient UI state. `SLDNode.equipment_id` provides identity mapping, but no verified engineer-facing equipment-deletion workflow exists. |
| SLD-WF-112 | CRITICAL | **OPEN** | Generic Core delete commands contain Core identity payloads only; no persistent SLD reconciliation boundary is attached to them. |
| SLD-WF-113 | HIGH | **OPEN** | Core delete undo restores Core state through the existing Application history/transaction mechanism, but does not and must not silently mutate persistent SLD state without an approved compound deletion policy. |
| SLD-WF-114 | HIGH | **OPEN** | Runtime projection reconciliation remains distinct from persistent `SLDDocument` mutation. No projection path is authorized to rewrite persistent SLD state. |
| SLD-WF-115 | HIGH | **OPEN** | Engineer-facing meaning of SLD-node deletion versus equipment deletion remains undefined; no intent was inferred from Delete-selection infrastructure or selection state. |

### Static deletion-path re-audit

| Path | Result |
|---|---|
| SLD canvas/controller node removal | Routes through `SLDController.remove_node()` → immutable `RemoveSLDNodeCommand` → `Application.execute()` → one Application transaction → `SLDService` only. |
| SLD selection | UI-only; `selected_node_ids` remain transient and do not mutate Core. |
| Core equipment deletion | Generic `model.delete_*` commands remain presentation-neutral and operate through the Core/Application model boundary. |
| Context menu / keyboard Delete | No authoritative engineer-facing coordinated deletion workflow was found; no workflow was invented. |
| Explorer / equipment panel / inspector | No authoritative coordinated Core+SLD deletion path was found in the inspected repository; recorded as a workflow gap rather than synthesized behavior. |
| Undo/redo | Existing `CommandManager` transaction/history boundary remains authoritative. Independent commands retain independent history entries; no nested public execution was introduced. |
| Persistence/orphan handling | Existing SLD association validation remains diagnostic/read-only; unresolved references are not silently deleted, fabricated, or repaired. |

### Transaction and rollback contract

If a future architecturally approved coordinated deletion is introduced, it must enter through one immutable Application command and one CommandManager transaction. Its mutation order must be explicit and its inverse operations registered with the existing `Transaction.record_undo()` mechanism. For the currently authorized workflows, `RemoveSLDNodeCommand` records only SLD restoration; Core delete commands record only their Core inverse state.

### Semantic event contract

Current SLD-only removal publishes `SLDPresentationChanged`; Core deletion publishes the applicable Core semantic events such as `ElementRemoved`, `NetworkChanged`, and `TopologyChanged` where applicable. No compound event lifecycle was invented because no compound deletion command is authorized.

### Verification boundary

**CORRECTED — STATIC VERIFICATION COMPLETE** for the intent-boundary clarification and register reconciliation.

Batch 18 remains **OPEN / RE-AUDIT REQUIRED** for SLD-WF-108 through SLD-WF-115 because the missing engineer-facing coordinated deletion policy is an architectural decision, not something source modification alone can legitimately close.

No tests, CI, application startup, GUI execution, or runtime verification was performed.


## RCA-016 — Configuration / Units / Engineering Parameters / Typed Values

### Static evidence review

The inspected repository already has explicit engineering-unit semantics for the principal Core quantities (for example `nominal_voltage_kv`, `frequency_hz`, `resistance_ohm`, `shunt_susceptance_siemens`) and a single canonical per-unit utility in `core/base/per_unit.py`. No evidence was found requiring a new generic writable configuration store, UI engineering database, second CommandManager, or second conversion service.

One concrete typed-semantic defect was confirmed in the transformer engineering contract: `impedance_basis` was represented and stored as an unrestricted string even though the domain permits only two semantic states. This allowed an engineering-basis concept to cross the Core/Application boundary as arbitrary text.

### Finding register

| Finding | Module | File | Root Cause | Frozen Contract | Correction | Affected Workflow(s) | Status | Verification Evidence | Remaining Risk |
|---|---|---|---|---|---|---|---|---|---|
| RCA-016-001 | Core transformer engineering configuration | `core/model/transformer.py`; `core/application/commands/model_commands.py` | Transformer impedance basis was an unrestricted string rather than a typed domain value | Engineering meaning must not depend on arbitrary strings; Application commands must carry typed engineering intent into Core | Added `ImpedanceBasis(str, Enum)` with `PU` and `ENGINEERING`; Transformer normalizes legacy string input once at the Core boundary and stores the typed enum; transformer command type now accepts the typed basis while preserving compatibility with existing string callers | Transformer creation → Application command → ModelService → Core → Power Flow preparation → persistence | **REMEDIATED — VERIFICATION DEFERRED** | Static source inspection confirms the domain vocabulary is closed to the two supported bases; existing persistence already serializes Enum values through the canonical ModelDTO encoder | Runtime compatibility and persisted-project round-trip remain unexecuted by policy |

### Static re-audit conclusion

- No second configuration authority was introduced.
- No second unit-conversion service was introduced.
- No UI/Canvas/Plugin mutation path was introduced.
- Transformer `r/x/b` basis remains explicit and is now represented by a typed Core value.
- Existing per-unit conversion remains centralized in `core/base/per_unit.py`.
- Existing persistence Enum support is reused; no parallel persistence format was added.
- No tests, CI, application startup, GUI execution, or runtime verification was performed.

| RCA-016-B6-005 | UI/Application Projection | `ui/projection/selection_projection_coordinator.py`; `ui/projection/projection_state.py` | Selection projection discarded authoritative engineering attributes before the Inspector boundary | Application ReadModel engineering information must reach immutable ProjectionState without UI/Core bypass | Existing selection projection now maps immutable ElementReadModel engineering parameters into generic immutable EngineeringParameterState values; PropertiesPanel remains unchanged and presentation-only | Application.read_element() → ElementReadModel → SelectionProjectionCoordinator → ProjectionState → PropertiesPanel | **REMEDIATED — STATICALLY VERIFIED** | Static source trace confirms engineering values originate in the Application ReadModel and are not taken from ElementUpdated.changes or Core objects | Runtime/tests/CI intentionally deferred; cross-link RCA-016-B6-001 and RCA-016-B6-004 preserved |
| RCA-016-B6-008 | Application/UI Projection Contract | `core/application/read_models.py`; `core/application/read_service.py`; `ui/projection/projection_state.py` | ProjectionState had no generic semantic representation for authoritative engineering configuration | Generic immutable engineering representation must preserve parameter identity, value, unit, datatype, choices, editability, derived/coupled metadata, validation metadata, topology impact, and study impact | Added generic EngineeringParameterReadModel and EngineeringParameterState; Application read service supplies read metadata from canonical field contracts; no Transformer-specific projection/store introduced | Core model → Application ReadService → ElementReadModel.engineering_parameters → generic UI projection → PropertiesPanel | **REMEDIATED — STATICALLY VERIFIED** | Static source trace confirms immutable, equipment-independent contracts with no Core references and no command/event authority in ProjectionState | Runtime/tests/CI intentionally deferred; cross-link RCA-016-B6-004 and RCA-017-010 preserved |

### B39 cross-linked remaining findings

| Finding | Status | B39 boundary |
|---|---|---|
| RCA-016-B6-001 | **OPEN — SOURCE EVIDENCE PENDING** | Not changed by B39; broader configuration/units evidence remains outside this correction |
| RCA-016-B6-004 | **OPEN — CONFIRMED** | Transformer update lifecycle remains separate and was intentionally not implemented |
| RCA-017-010 | **OPEN — CONFIRMED** | Engineer-facing Transformer configuration workflow remains separate and was intentionally not implemented |

RCA-016 remains **OPEN / RE-AUDIT REQUIRED** for the broader configuration/units workflow until the remaining study, persistence, Inspector, SLD, plugin, and project-isolation consumers are statically re-audited after this correction.

## RCA-017 — Static Correction Record

RCA-017 equipment catalogue/tool activation correction is source-remediated with verification deferred. RCA-017-003 is retracted. Cross-reference: RCA-016 Transformer configuration findings. No tests, CI, startup, GUI, or runtime verification performed.


### RCA-017 — Static re-audit addendum

The re-audit identified one residual competing construction surface: `ui/tools/tool_factory.py` still contained concrete legacy constructors despite being documented as non-authoritative. It has now been reduced to a compatibility marker that raises on construction and exposes no concrete creation methods. Authoritative construction remains `ToolManager` → `create_default_tool_factories()`.

Status remains **REMEDIATED — VERIFICATION DEFERRED**. No tests, CI, application startup, GUI execution, or runtime verification were performed.
