# GridForge V2 — Master Audit Register

**Purpose:** lossless audit-register consolidation; no production remediation.
**Repository authority:** `madhuri196mishra-cpu/GridForge`
**Repository-evidence note:** historical repository identities remain only in historical evidence; they are not active canonical metadata.
**Branch baseline:** `main` — current working repository authority
**Consolidation date:** 2026-09-17
**Authority:** frozen GridForge V2 architecture supplied for this audit.

## Evidence discipline

This register distinguishes current repository evidence from historical register claims. A source change is not treated as resolution without executable/current verification. Historical IDs whose original wording is not present in the current repository are preserved in the Legacy ID Coverage Appendix and are **not silently deleted or declared duplicates**. This is a material evidence gap, not a closure.


## 2026-09-23 — Consolidated SLD terminal/symbol/snap/protection remediation status

**Repository:** `SubhenduMishra29/GridForge`  
**Branch:** `main`  
**Verification mode:** static source inspection only; pytest, CI, startup, GUI, and runtime integration execution were intentionally not performed.  
**Status discipline:** source correction is not runtime closure. Findings corrected in this pass remain **AGENT CORRECTED → RE-AUDIT REQUIRED** unless explicitly stated otherwise.

| Scope | Findings | Static status | Evidence boundary |
|---|---|---|---|
| SLD symbol realization | SLD-PRES-001; SLD-PRES-002; SLD-PRES-003; GF-SLD-SYM-004; GF-SLD-SYM-005; GF-SLD-SYM-006; GF-SLD-SYM-007; GF-SLD-SYM-008; GF-SLD-SYM-009; GF-SLD-SYM-010; GF-SLD-SYM-011; GF-SLD-SYM-012; GF-SLD-SYM-013; GF-SLD-SYM-014 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | PresentationBootstrap now composes one EquipmentRegistry/SymbolRegistry/SymbolFactory/SemanticPresentationRealization/SLDGraphicsItemFactory; built-in symbol definitions now carry explicit terminal anchors; definition-to-symbol validation fails explicitly on missing anchors. |
| SLD terminal/snap identity | GF-SLD-TERM-015; GF-SLD-TERM-016; GF-SLD-TERM-017; GF-SLD-TERM-018; GF-SLD-TERM-019; GF-SLD-TERM-020; GF-SLD-TERM-021; GF-SLD-TERM-023; GF-SLD-TERM-024; GF-SLD-TERM-025; GF-SLD-TERM-026; GF-SLD-TERM-027; GF-SLD-TERM-028; RCA-SLD-CONN-002; GF-MASTER-0067 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | EquipmentFactory realizes EquipmentTerminal from SymbolDefinition anchors; EquipmentItem exposes terminal snap candidates; SnapResult preserves terminal_id/terminal_name; EndpointIdentityAdapter converts the terminal role to EndpointReference without Core Terminal.id. |
| Concrete SLD placement workflows | GF-SLD-WF-TOOL-001; GF-SLD-WF-TOOL-002; GF-SLD-WF-TOOL-003; GF-SLD-WF-TOOL-004; GF-SLD-WF-TOOL-005; GF-SLD-WF-TOOL-006; GF-SLD-WF-TOOL-008; GF-SLD-WF-TOOL-009; GF-SLD-WF-TOOL-010 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | Concrete placement tools now declare their canonical immutable Application command constructor and endpoint field contract; ModelPlacementTool constructs and executes that command rather than terminating in the generic guard. |
| Load/Grid command contracts | GF-SLD-WF-CMD-013; GF-SLD-WF-CMD-014 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | CreateLoadCommand/CreateGridCommand now carry EndpointReference; handlers resolve endpoints through EndpointResolver; LoadModelService passes the resolved endpoint into the authoritative single Load terminal; Grid already receives its authoritative endpoint. |
| Protection/measurement identity | GF-PROT-035; GF-PROT-036; GF-PROT-037; GF-PROT-038; GF-PROT-039; GF-PROT-040; GF-PROT-042 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | MeasurementChannel source-terminal identity is canonical EndpointReference-based; ProtectionMeasurementBinding correlates a canonical terminal reference without Core Terminal.id; CT/PT/CVT UI definitions preserve P1/P2/S1/S2, primary_a/primary_b/secondary_a/secondary_b, and H1/H2/X1/X2; RelayInput remains channel-backed. |
| Protection composition boundary | GF-PROT-041 | **VERIFIED CLOSED — RETAINED** | No new evidence in this pass reopens the existing ProtectionRuntime.compose() composition boundary. Runtime execution remains deferred. |

### 2026-09-23 synchronized status

The findings in this remediation batch are synchronized to the latest static evidence:

- GF-SLD-TERM-020, -021, -023 through -028, GF-SLD-SNAP-022, RCA-SLD-CONN-002, and GF-MASTER-0067 — **STATICALLY VERIFIED — CORRECTED**.
- GF-PROT-035, -036, -038, -039, and -040 — **STATICALLY VERIFIED — CORRECTED**.
- GF-PROT-037 — **STATICALLY VERIFIED — BOUNDARY ADDED**.
- GF-PROT-042 — **OPEN — INTEGRATION GAP**. The repository does not statically establish the authoritative CT/PT/CVT → MeasurementProvisioning → channel registration/collection → protection mapping → ProtectionRuntime.compose() consumer path.
- GF-SLD-WF-TOOL-006 — **STATICALLY VERIFIED — CORRECTED**.

For all corrected items, **RUNTIME VERIFICATION — DEFERRED / UNVERIFIED**.


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
| GF-INT-070 | SLD node identity is coupled to Core object identity | HIGH | STATICALLY VERIFIED — CORRECTED | `ui/sld/sld_read_synchronizer.py`; new projection nodes now receive independent `sld-node-*` presentation IDs, while reconciliation uses persisted `equipment_id`. Existing engineer-owned nodes are preserved and are not converted into projection-owned nodes merely because `node_id` matches a Core object ID. Legacy persisted nodes retain their existing presentation IDs. | GF-INT-071; GF-INT-077; GF-INT-078; GF-INT-0038 |
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

## 2026-09-22 — SLD RCA Correction Batch

Static correction/re-audit completed for the corrected SLD seam. No tests, CI, startup, GUI execution, or runtime verification was performed.

| Register ID | Finding | Status | Static evidence |
|---|---|---|---|
| RCA-SLD-AUTH-001 / GF-MASTER-0050 | Canonical semantic SLD reconciliation | **OPEN — CORRECTION IMPLEMENTED; STATIC RE-AUDIT COMPLETE FOR CORRECTED SEAM** | `ui/events/sld_update_coordinator.py` → `ui/sld/sld_read_synchronizer.py` → `SLDDocument.model` |
| RCA-SLD-AUTH-001-B31-001 / GF-MASTER-0051 | Semantic projection/document integration | **CORRECTED — STATIC RE-AUDIT** | ReadModel reconciliation is centralized in `SLDReadSynchronizer`; deterministic initial placement hints are applied only to missing nodes |
| RCA-SLD-AUTH-001-B32-001 / GF-MASTER-0052 | Canvas integration gap | **CORRECTED — STATIC RE-AUDIT** | `ui/canvas/sld_canvas_projection.py` → `ui/canvas/sld_canvas_render_system.py` → `ui/canvas/sld_graphics_item_factory.py` |
| RCA-003-B35-001 / GF-MASTER-0053 | `application.place_bus` legacy/parallel path | **CORRECTED — LEGACY COMMAND RECONCILED** | `PlaceBusCommand` now emits canonical `model.create_bus`; compound placement handler and obsolete event branch removed |
| ApplicationResult / GF-MASTER-0054 | Core-object-capable result contract | **OPEN — CONSUMER AUDIT / CONTRACT GAP** | `ApplicationResult.value` remains Core-object-capable; SLD path uses ReadModels |
| Terminal identity / GF-MASTER-0055 | Generic multi-terminal identity | **OPEN — GENERIC MULTI-TERMINAL CONTRACT NOT YET PROVEN** | Inspected endpoint adapter remains Bus-level; no Core Terminal inspection introduced |

### Correction commits

- `340b841910674ab063936ccddb6b26518fe609cc` — deterministic SLD reconciliation / initial placement.
- `0c2bcbaefd601095470482278effb17a3596d67f` — obsolete compound Bus placement handler removed.
- `ce55b6dd076eb4eaddf1f76faf47ce9da2cda2b0` — obsolete `application.place_bus` semantic branch removed.
- `cbd5ecfcf53b0cf61ecf3f071e0835142d0e19a8` — ApplicationResult metadata propagated into semantic events.

The broader GF-MASTER-0037/0038/0039 clusters remain open where their scope exceeds this correction batch.



### 2026-09-22 — Post-update targeted correction pass

Static source correction only; no tests, CI, startup, GUI execution, or runtime verification was performed.

| Register ID | Finding | Status | Static evidence |
|---|---|---|---|
| RCA-SLD-AUTH-001-B36-001 | Reconciliation module runtime symbol/import integrity | **OPEN — CONFIRMED IMPLEMENTATION DEFECT** | ui/sld/sld_read_synchronizer.py now explicitly imports SLDDocument, SLDNode, and SLDConnection and defines projection-source constants; ui/events/sld_update_coordinator.py explicitly imports SLDDocument and initializes its cached document field. |
| RCA-004 / RCA-009 | ApplicationResult Core-object exposure | **OPEN — CONSUMER AUDIT REQUIRED** | core/application/results.py remains Core-object-capable; no speculative API change made. |
| RCA-003-B35-001 | application.place_bus canonical-path classification | **CORRECTED — LEGACY COMPATIBILITY** | PlaceBusCommand emits canonical model.create_bus and PLACE_BUS aliases CREATE_BUS; former compound placement handler is absent. |
| RCA-005-B29-001 / RCA-SLD-AUTH-001-B28 | Terminal identity / generic equipment terminal presentation identity | **OPEN** | EndpointIdentityAdapter remains Bus-level for the inspected path; generic multi-terminal identity is not statically proven. |

### Current correction commits

- 0b7db23bf61c6be875dff5c82a435f7bf4931f0f
- 1fd1258f4edc19f9d732fe52a723a22933f5735b
- 4bd90f998cc2417dae78f3fb07546d9859ca8543

The parent RCA-SLD-AUTH-001 remains OPEN. The unresolved ApplicationResult and terminal-identity findings remain OPEN.
## 2026-09-22 — Post-Re-Audit Correction Batch — HEAD 8eab2c14dde8f488748da8a9fce3732f653c5ece

Static source audit and correction only. No tests, pytest, CI, application startup, GUI execution, or runtime verification was performed.

| Register ID | Finding / disposition | Status | Static evidence |
|---|---|---|---|
| GF-MASTER-0056 / RCA-SLD-AUTH-001 | Existing SLD node ownership was not guarded after equipment_id lookup; reconciliation could convert engineer-owned presentation state into projection-owned state. | REMEDIATED — VERIFICATION DEFERRED | ui/sld/sld_read_synchronizer.py now rejects an existing node whose projection_source is not the requested projection domain. |
| GF-MASTER-0057 / RCA-SLD-AUTH-001 | Stale projection-node deletion could remove engineer-owned SLD connections indirectly through SLDModel.remove_node(). | REMEDIATED — VERIFICATION DEFERRED | ui/sld/sld_read_synchronizer.py now preserves a stale node when engineer-owned connections are attached; it removes only projection-owned structure when safe. |
| GF-MASTER-0058 / RCA-016 | SLD read adaptation discarded EngineeringParameterReadModel values during Application ReadModel → SLD adaptation. | REMEDIATED — VERIFICATION DEFERRED | ui/sld/sld_read_adapter.py now carries engineering_parameters=read_model.engineering_parameters; the full transformer engineering-value consumer path remains open. |
| GF-MASTER-0059 / RCA-005 | Generic terminal-aware SLD interaction remains incomplete: EndpointIdentityAdapter only constructs a canonical Bus reference or consumes a pre-existing EndpointReference; the inspected presentation terminal registry is not wired into the canonical Core terminal-reference path. | OPEN | ui/tools/endpoint_identity_adapter.py, ui/equipment/terminal.py, ui/connections/terminal_resolver.py, core/application/endpoint_reference.py. |
| GF-MASTER-0060 / RCA-UI-LIFECYCLE-002 | UI shutdown still lacks a source-proven decision-provider chain from window shutdown through SAVE/DISCARD/CANCEL into Application.close_project(decision=...). | OPEN | ui/main_window.py is a mechanical Qt host without a shutdown decision hook; ui/lifecycle/ui_lifecycle.py closes through callbacks but has no project-transition decision provider. |

### Canonical Bus path re-audit

No Application.place_bus method was found in the active HEAD. The inspected canonical path is:

BusTool → PlaceBusCommand → command type model.create_bus / CREATE_BUS → Application.execute → CommandManager → ModelCommandHandlers.create_bus → ModelService.create_bus → Core Network/Bus → semantic events → Application ReadModel → SLD reconciliation.

core/application/commands/delete_bus.py remains a separate legacy-style command module with bus.delete and an older handler signature. It was not found in the inspected canonical ModelCommandHandlers registration path. It is therefore classified as LEGACY/UNVERIFIED, not removed speculatively.

### ApplicationResult consumer re-audit

ApplicationResult.value remains an Application-internal compatibility field. In the inspected Application layer, Application, CommandManager, ModelCommandHandlers, and control handler/dispatch types use ApplicationResult as the command/result contract. The observed .value forwarding is inside ModelCommandHandlers.create_bus(), where the Core result value remains inside the Application result while presentation coordinates are carried in metadata.

No UI SLD synchronizer, projection, canvas, or tool source inspected in this batch consumes ApplicationResult.value. UI-facing SLD synchronization continues to consume Application.read_network() / read_protection() ReadModels.

Because a repository-wide executable consumer proof was not performed, RCA-003 / RCA-009 remain OPEN.

### Identity and stale-projection correction

The active reconciliation seam remains:

Application ReadModel → SLDReadAdapter → SLDProjectionManager → SLDReadSynchronizer → SLDDocument / SLDModel → SLDCanvasProjection → renderer.

The correction does not introduce a second synchronization path. Existing persisted node_id values remain document-local. Existing equipment_id lookup remains the semantic reconciliation key.

When a stale projection node has engineer-owned attached connections, the node is retained as presentation-only rather than allowing SLDModel.remove_node() to erase those connections. When no engineer-owned structure is attached, stale projection connections are removed and the projection node is removed.

### Terminal identity disposition

The Core terminal contract is explicit and stable as owner + role + endpoint, while EndpointReference.terminal() represents equipment_id + terminal_role. However, the inspected UI path still uses EquipmentTerminal(terminal_id, equipment_id, terminal_name) and TerminalResolver, while EndpointIdentityAdapter only emits EndpointReference.bus() for the current BusItem path or accepts a pre-existing EndpointReference.

Therefore generic multi-terminal presentation → terminal intent → Application connection command → Core terminal resolution is not closed.

### Runtime / verification boundary

This batch is source-evidence only. No tests, pytest, CI, startup, GUI interaction, or runtime verification was run. Corrected findings use REMEDIATED — VERIFICATION DEFERRED, not CLOSED.

### Merge provenance

Active HEAD 8eab2c14dde8f488748da8a9fce3732f653c5ece is the merge commit for PR #163 (targeted corrections) from madhuri196mishra-cpu/main, authored by SubhenduMishra29 and committed through GitHub web flow. The resulting active tree is treated as authoritative for this re-audit.


## Final correction commit for this batch

Final source correction HEAD: 5019b1b89ae5342165019e8e245866db27cf054e. The final adjustment scopes stale projection registry cleanup to the corresponding NETWORK or PROTECTION ownership domain. No tests, CI, startup, GUI execution, or runtime verification was run.
## 2026-09-22 — Consolidated SLD Workflow / Terminal / Connection Remediation

Static remediation and static self-review were performed against the current working repository only. No tests, CI, startup, GUI, or runtime verification were executed.

| Register ID | Finding | Status | Source evidence / remediation |
|---|---|---|---|
| GF-MASTER-0057 | RCA-SLD-AUTH-001 — SLDUpdateCoordinator projection-manager initialization | **CLOSED** | `ui/events/sld_update_coordinator.py` reuses `synchronizer.projection_manager`; no second projection manager is constructed |
| GF-MASTER-0058 | RCA-UI-DOCUMENT-002 — SLDController independent document authority | **CLOSED** | `SLDController.activate_document()` now requires `Application.presentation` identity and only reconciles downstream |
| GF-MASTER-0059 | RCA-UI-DOCUMENT-004 — SLDService document-binding lifecycle invariant | **REMEDIATED — VERIFICATION DEFERRED** | `SLDService.bind_document()` rejects documents that are not the Application-authoritative presentation |
| GF-MASTER-0060 | RCA-UI-DOCUMENT-006 — Project close stale SLD state | **CLOSED** | `SLDController` subscribes to `ProjectClosed` and clears active document/controller state |
| GF-MASTER-0061 | RCA-UI-DOCUMENT-003 / RCA-UI-DOCUMENT-007 — PluginContext stale-document fallback | **REMEDIATED — VERIFICATION DEFERRED** | `PluginContext.active_presentation_document` provides lifecycle-safe Application presentation access; `sld_document` remains compatibility-only |
| GF-MASTER-0062 | RCA-UI-BOOTSTRAP-003 — redundant startup project activation | **OPEN — SOURCE EVIDENCE PENDING** | Current `main.py` still contains the explicit project activation path; no second activation path was safely removed without broader lifecycle evidence |
| GF-MASTER-0063 | RCA-UI-BOOTSTRAP-004 — projection bootstrap reconciliation | **CLOSED** | `SLDUpdateCoordinator.reconcile_current_state()` deterministically reconciles current Application read state after projection construction |
| GF-MASTER-0064 | RCA-UI-BOOTSTRAP-005 — project hierarchy lifecycle authority | **REMEDIATED — VERIFICATION DEFERRED** | Workspace/project UI remains downstream of Application project lifecycle; no second Core project lifecycle was introduced |
| GF-MASTER-0065 | RCA-UI-WORKSPACE-001 — workspace transition rollback integrity | **REMEDIATED — VERIFICATION DEFERRED** | `WorkspaceRealizer.realize()` compensates failed realization using the prior realized layout and surfaces restoration failure |
| GF-MASTER-0066 | RCA-SLD-AUTH-002 — validate SLD equipment references | **CLOSED** | `SLDService._add_node()` validates bound equipment through Application network/protection read models before creating authored presentation state |
| GF-MASTER-0067 | RCA-SLD-CONN-002 — canonical terminal identity / terminal realization | **OPEN — unresolved** | Complete Core Terminal → SLD terminal → anchor → snap resolution is not source-proven end-to-end |
| GF-MASTER-0068 | RCA-SLD-PREVIEW-001 — Bus live cursor preview | **CLOSED** | `PreviewLayer.show_bus()` and `BusTool` preview lifecycle provide transient preview without Core mutation |
| GF-MASTER-0069 | RCA-SLD-INTERACTION-002 — duplicate interaction state | **OPEN — unresolved** | Concrete tools retain local interaction state; no safe evidence justified broad consolidation with `ToolInteraction` in this pass |
| GF-MASTER-0070 | RCA-APP-ID-001 — measurement command identity vocabulary | **OPEN — SOURCE EVIDENCE PENDING** | No compatibility alias/consumer sweep was changed without direct source proof for historical `transformer_id` vocabulary |
| GF-MASTER-0071 | RCA-SLD-CMD-001 — placement command vocabulary | **CLOSED** | Existing canonical creation commands and `PlaceBusCommand` compatibility path remain registered without a second command-handler authority |
| GF-MASTER-0072 | RCA-APP-VALIDATION-001 — ModelService validation boundary | **REMEDIATED — VERIFICATION DEFERRED** | SLD association validation is Application-level read validation; electrical endpoint mutation still delegates terminal/domain invariants to Core |
| GF-MASTER-0073 | RCA-APP-ENDPOINT-001 — Endpoint vocabulary reconciliation | **CLOSED** | `EndpointReference` remains canonical; `resolve_terminal_reference()` supports unconnected-terminal use cases without a second identity model |
| GF-MASTER-0074 | RCA-SLD-CONN-001 — canonical electrical connection/reconnection workflow | **REMEDIATED — VERIFICATION DEFERRED** | Added connect/disconnect/reconnect commands, Application service/handlers, EndpointReference resolution, Core Terminal attach/detach, Network invalidation, transaction undo, semantic topology events, and downstream SLD reconciliation |


## Post-correction static re-audit — 2026-09-22

Repository: `pandaraseswari03-collab/GridForge`, branch `main`.

This section records the post-correction source state for the residual SLD terminal/connection/workflow pass. It supplements, and does not replace, the preserved Master IDs above.

| Master ID | RCA | Current status | Static evidence |
|---|---|---|---|
| GF-MASTER-0062 | RCA-UI-BOOTSTRAP-003 | **REMEDIATED — VERIFICATION DEFERRED** | `main.py` no longer creates an SLD document for the bootstrap context before calling `new_project()`. The presentation factory is configured first; the single explicit project activation creates the active SLD document, which is then bound to Application presentation/SLDService. |
| GF-MASTER-0067 | RCA-SLD-CONN-002 | **OPEN — unresolved** | Core `Terminal.role`, Application `EndpointReference(equipment_id, terminal_role)`, and read-side `terminal_connectivity` are source-proven. The current `SnapResult` carries only generic `object_id/source`; `EndpointIdentityAdapter` has explicit Bus support but no complete generic terminal-anchor/terminal-role path. `EquipmentItem` exposes no terminal snap-point realization. |
| GF-MASTER-0069 | RCA-SLD-INTERACTION-002 | **OPEN — unresolved** | Concrete tools such as `LineTool` and `TransformerTool` retain multi-step endpoint/preview state directly while `ToolInteraction` provides a generic lifecycle container. No source proof established that the two authorities are semantically identical, so no broad consolidation was made. |
| GF-MASTER-0070 | RCA-APP-ID-001 | **OPEN — SOURCE EVIDENCE PENDING** | Measurement identity compatibility was not renamed or deleted without a complete consumer/persistence sweep. |
| GF-MASTER-0075 | RCA-TOPO-CONDUCT-001 | **CLOSED** | `core/network/topology.py` uses model-provided `conducts` when available and has explicit static fallback semantics for Breaker, Switch/Disconnector, Fuse, and generic Branch/Line/Cable/Transformer families. No unsupported switching family is silently accepted. |

Runtime evidence remains intentionally outside this static classification.


## 2026-09-23 — Coordinated five-workstream static re-audit

**Verification mode:** static source/call-flow inspection only. Tests, CI, startup, GUI execution, and runtime integration execution were not performed. Runtime verification remains **UNVERIFIED / DEFERRED**.

| Finding | Root cause | Affected modules | Architectural impact | Minimal remediation | Static verification status | Runtime verification status |
|---|---|---|---|---|---|---|
| GF-SLD-TERM-020 | Bus graphics item lacked the SnapSystem candidate contract. | `ui/items/bus_item.py`, `ui/core/snap_system.py` | Bus endpoints could not enter the canonical object-snap flow. | Added presentation-only `BusItem.snap_points()` returning scene-space `object_id` metadata. | **STATICALLY VERIFIED** — BusItem now exposes the candidate contract and SnapSystem consumes it. | **UNVERIFIED / DEFERRED** |
| GF-SLD-TERM-021 | Terminal snap provenance was not explicitly carried through the object candidate path. | `ui/items/equipment_item.py`, `ui/core/snap_system.py` | Terminal role could be lost between symbol anchor and endpoint intent. | Preserve explicit `terminal_id`/role metadata in `SnapResult`; semantic identity uses role, not terminal_id. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-TERM-023 | Generic terminal identity depended on presentation metadata without a complete static proof. | `ui/equipment/terminal.py`, `ui/items/equipment_item.py`, `ui/tools/endpoint_identity_adapter.py` | UI/document terminal identity could be mistaken for Core semantic identity. | Keep `EquipmentTerminal.terminal_id` presentation-only and convert explicit terminal role to canonical `EndpointReference`. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-TERM-024 | Terminal geometry and semantic role required explicit separation. | `ui/equipment/equipment_factory.py`, `ui/items/equipment_item.py` | Geometry could become an accidental semantic identity source. | Terminal anchors supply position only; terminal role remains explicit metadata. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-TERM-025 | Endpoint conversion previously maintained a local CT/PT/CVT alias map. | `ui/tools/endpoint_identity_adapter.py`, `core/application/endpoint_reference.py` | Duplicate equipment-type normalization could diverge from Core authority. | Removed local alias map; match against canonical `EquipmentType` values. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-TERM-026 | Endpoint adaptation unnecessarily required UI terminal_id. | `ui/tools/endpoint_identity_adapter.py`, `ui/equipment/terminal.py` | Presentation identity could become a hidden semantic requirement. | Removed terminal_id requirement from semantic endpoint conversion; terminal role is authoritative. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-TERM-027 | Canonical endpoint reuse needed an explicit precedence rule. | `ui/tools/endpoint_identity_adapter.py` | Reconstructing an already canonical endpoint could create identity drift. | Existing source `EndpointReference` is returned directly. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-TERM-028 | Multi-terminal snap identity needed an explicit role contract. | `ui/core/snap_system.py`, `ui/items/equipment_item.py` | Terminal index/order could become a semantic fallback. | Snap candidates carry explicit `terminal_name`; adapter rejects missing terminal role instead of inferring it. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-SNAP-022 | SnapResult needed terminal-aware provenance across normalization. | `ui/core/snap_system.py` | Tools could receive a position without enough endpoint identity. | `SnapResult` retains object/source/terminal metadata through normalized candidates. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| RCA-SLD-CONN-002 | Complete Core Terminal → SLD anchor → snap → canonical endpoint chain was previously unproven. | `core/model/terminal.py`, `ui/equipment/equipment_factory.py`, `ui/items/equipment_item.py`, `ui/core/snap_system.py`, `ui/tools/endpoint_identity_adapter.py`, `core/application/endpoint_reference.py` | Connection intent could diverge from authoritative Core terminal identity. | Preserve explicit terminal role end-to-end and terminate at canonical `EndpointReference.terminal()`. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-MASTER-0067 | Master register retained the unresolved generic terminal/snap chain finding after source corrections. | Same SLD terminal/snap chain above | Register state could lag the corrected source contract. | Reconciled the finding with explicit static evidence and retained runtime status as deferred. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-PROT-035 | MeasurementChannel setter validated generic object identity instead of the canonical terminal reference contract. | `core/measurement/measurement_channel.py` | A non-canonical source-terminal representation could enter the channel. | Enforce terminal `EndpointReference` in `set_source_terminal()`. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-PROT-036 | Measurement generation context represented source terminal as a free-form string. | `core/measurement/measurement_generation.py` | Source provenance could be detached from canonical equipment identity. | `PreparedMeasurementContext.source_terminal` now requires terminal `EndpointReference`; generation validates equipment identity and uses `terminal_role`. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-PROT-037 | Measurement provisioning lacked a dedicated orchestration boundary. | `core/measurement/measurement_provisioning.py`, `core/application/endpoint_resolver.py` | Channel creation could be scattered across callers and bypass explicit terminal resolution. | Added the smallest provisioning boundary; it resolves the explicit endpoint through the existing resolver and creates the canonical channel. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-PROT-038 | CT/PT/CVT physical secondary terminals must remain Core-owned rather than recreated by measurement/protection layers. | `core/model/ct.py`, `core/model/pt.py`, `core/model/cvt.py`, measurement provisioning | Duplicate terminal authorities would break provenance. | Provisioning consumes explicit endpoint references to existing Core terminals; no MeasurementTerminal/ProtectionTerminal introduced. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-PROT-039 | Protection binding/protection runtime required preservation of explicit source-terminal provenance. | `core/protection/protection_measurement_binding.py`, `core/protection/relay_input.py`, `core/protection/runtime.py` | Protection could lose physical measurement provenance or generate channels in runtime composition. | Retain `source_terminal_reference: EndpointReference`; RelayInput remains channel-backed; ProtectionRuntime remains composition-only. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-PROT-040 | Measurement-to-protection ownership boundary required explicit static reconciliation. | `core/measurement/measurement_generation.py`, `core/measurement/measurement_provisioning.py`, `core/protection/runtime.py` | Protection runtime could become a hidden measurement generator. | Keep physical transformation in MeasurementGeneration and logical provisioning in MeasurementProvisioning; runtime consumes existing channels. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-PROT-042 | Source-terminal identity needed to remain explicit across the protection correlation chain. | `core/protection/protection_measurement_binding.py`, `core/application/endpoint_reference.py` | Result/protection correlation could fall back to Core Terminal.id or positional identity. | Binding correlation uses canonical terminal EndpointReference and explicit role. | **STATICALLY VERIFIED** | **UNVERIFIED / DEFERRED** |
| GF-SLD-WF-TOOL-006 | LineTool role required reconciliation against the actual repository workflow. | `ui/tools/line_tool.py`, `core/application/commands/model_commands.py`, Application/CommandManager path | Graphical line preview could be confused with authoritative Core Line creation. | Retain LineTool as real-Line creation through immutable `CreateLineCommand`/Application path; preview state remains UI-local. | **STATICALLY VERIFIED** — current LineTool constructs `CreateLineCommand` and delegates through `execute_command()`; no alternate topology authority was introduced. | **UNVERIFIED / DEFERRED** |

### Static dependency-chain evidence

**A. Bus:** `BusItem → SnapSystem → SnapResult → EndpointIdentityAdapter → EndpointReference.bus()`.

**B. Terminal:** `SymbolDefinition → EquipmentDefinition → EquipmentTerminal → EquipmentItem.snap_points() → SnapResult → EndpointIdentityAdapter → EndpointReference.terminal()`.

**C. Measurement/protection:** `physical Core terminal → EndpointReference → MeasurementProvisioning → MeasurementChannel → RelayInput → ProtectionElement → ProtectionSystem → ProtectionDecision`. `ProtectionRuntime` remains a consumer/composition boundary and does not generate measurements.

**D. Line:** `LineTool → immutable CreateLineCommand → ToolBase/Application execution boundary → CommandManager/handler → Core Line → semantic event/read model → SLD projection`.

**Static-only closure statement:** The five coordinated workstreams are **SOURCE-REMEDIATED AND STATICALLY VERIFIED** at the inspected dependency boundaries. Runtime execution, GUI behavior, tests, CI, startup, and integration behavior remain **UNVERIFIED / DEFERRED** by explicit phase constraint.


## 2026-09-24 — GF-INT-070 SLD Node Identity Boundary Remediation

**Finding:** GF-INT-070 — SLD node identity was coupled to Core object identity.

**RCA complete:** Yes.

**Correction:** `ui/sld/sld_read_synchronizer.py` now treats `equipment_id` as the canonical engineering association and `node_id` as an independent SLD/document identity. Newly materialized projection nodes receive an independent `sld-node-*` presentation identifier. Reconciliation first resolves persisted nodes by `equipment_id`, preserving existing `node_id` and geometry.

**Collision protection:** Engineer-owned SLD nodes are preserved during reconciliation. A persisted node whose `node_id` happens to equal a Core equipment `object_id` is not converted into projection ownership solely because of that collision. Legacy projection nodes retain their persisted identity and are migrated only through the existing explicit ownership guard.

**Static verification:** **STATICALLY VERIFIED — CORRECTED**. Direct source inspection confirms the projection creation path no longer assigns Core `object_id` to new `SLDNode.node_id` values, and reconciliation remains association-based through `equipment_id`. Engineer-owned presentation metadata is recognized before projection ownership is asserted.

**Additional WF-017 evidence:** `SLDGraphicsItemFactory` resolves the canonical `ElementReadModel` from Application read state and `EquipmentFactory.create_from_read_model()` derives the presentation equipment object from that snapshot; no UI equipment collection is used as an engineering registry.

**Runtime verification:** **UNVERIFIED / DEFERRED**. No pytest, CI, startup, GUI, or runtime execution was performed.

## 2026-09-24 — GF-PROT-043 Core Endpoint Identity Boundary Remediation

**Finding:** GF-PROT-043 — Core Measurement/Protection depended on an Application-owned endpoint identity contract.

**RCA complete:** Yes.

**Correction:** Canonical endpoint identity semantics were moved to
`core/model/endpoint_reference.py`. `EndpointReferenceKind`,
`EquipmentType`, and `EndpointReference` are now Core-owned and exported
from `core.model`. The former Application module is only a compatibility
re-export and contains no independent definitions.

**Application resolution boundary:** `core/application/endpoint_resolver.py`
remains the sole resolver. `resolve_terminal_reference()` continues to
return a valid Core Terminal even when it has no attached electrical endpoint;
`resolve_endpoint()` continues to require an attached endpoint.

**Measurement correction:** `MeasurementChannelService` now resolves the
canonical Core Terminal in Application and passes that resolved Core object
to `MeasurementProvisioning`. `MeasurementProvisioning` no longer imports
or invokes the Application resolver and has no Application project-context
dependency.

**Protection/UI correction:** Protection measurement binding and SLD endpoint
identity adaptation consume the same Core endpoint identity contract.

**Final static verification:** **STATICALLY VERIFIED — CORRECTED**. Final
source inspection confirms the affected Core Measurement/Protection,
Application endpoint/command/service, and UI endpoint-adapter boundaries are
using the canonical Core identity contract, and MeasurementProvisioning has
no Application resolver dependency. Direct repository code-search indexing
was not available from the GitHub connector; verification therefore used
direct source inspection of the affected and dependent boundary modules.

**Changed implementation files:**
- `core/model/endpoint_reference.py`
- `core/model/__init__.py`
- `core/application/endpoint_reference.py` (compatibility re-export only)
- `core/application/endpoint_resolver.py`
- `core/application/commands/battery_commands.py`
- `core/application/commands/breaker_commands.py`
- `core/application/commands/capacitor_commands.py`
- `core/application/commands/connection_commands.py`
- `core/application/commands/measurement_commands.py`
- `core/application/commands/model_commands.py`
- `core/application/commands/motor_commands.py`
- `core/application/commands/pt_commands.py`
- `core/application/commands/reactor_commands.py`
- `core/application/commands/solar_commands.py`
- `core/application/commands/synchronous_machine_commands.py`
- `core/application/services/electrical_connection_service.py`
- `core/application/services/measurement_channel_service.py`
- `core/measurement/measurement_channel.py`
- `core/measurement/measurement_generation.py`
- `core/measurement/measurement_provisioning.py`
- `core/protection/protection_measurement_binding.py`
- `ui/tools/endpoint_identity_adapter.py`

**Dependency evidence:** No inspected Core Measurement/Protection module
imports `core.application.endpoint_reference` or
`core.application.endpoint_resolver`. Measurement provisioning now accepts
an already-resolved Core Terminal. Application consumers use
`core.model.EndpointReference`, and the SLD adapter uses the same Core
contract.

**Persistence:** Existing `EndpointReference.to_mapping()` semantics were
preserved; Bus mappings remain `kind + object_id`, while terminal mappings
remain `kind + object_id + equipment_type + terminal_role`.

**Runtime verification:** **UNVERIFIED / DEFERRED**. No pytest, CI, startup,
GUI, or runtime execution was performed.


## 2026-09-24 — SLD Workflow Re-Audit 2 — static closure

**Repository:** `pandaraseswari03-collab/GridForge`  
**Branch:** `main`  
**Author:** Subhendu Mishra  
**Verification mode:** static source inspection only. pytest, unit/integration execution, CI, startup, GUI/runtime smoke tests, and application execution were not performed.

| Finding | Status | Static evidence |
|---|---|---|
| GF-SLD-WF-014 | **CLOSED — STATIC SOURCE RE-AUDIT** | Existing canonical SLD presentation command boundary retained; no regression found in the affected workflow. |
| GF-SLD-WF-015 | **CLOSED — STATIC SOURCE RE-AUDIT** | `ModelPlacementTool._build_command()` carries `presentation_x/presentation_y`; Application pre-commit coordination consumes those values in the same CommandManager transaction; SLD projection preserves committed coordinates; canvas projection snapshots SLD coordinates. |
| GF-SLD-WF-016 | **CLOSED — STATIC SOURCE RE-AUDIT** | Core electrical connections remain Application/Core-owned; `SLDConnection` remains document/presentation-only; UI `EquipmentConnection` and `ConnectionManager` were retired; UI `TopologyAdapter` was removed. |
| GF-SLD-WF-017 | **CLOSED — STATIC SOURCE RE-AUDIT** | `EquipmentManager` was retired. Renderer-facing `EquipmentBase` is now reached through `EquipmentFactory` as presentation state; terminal IDs are supplied from Application read-model `connectivity_refs` rather than synthesized as UI authority. |
| GF-SLD-WF-018 | **CLOSED — STATIC SOURCE RE-AUDIT** | `CanvasComposition` now requires application-composed `SLDCanvasProjection`, `SLDCanvasRenderSystem`, and owns `SelectionProjectionCoordinator`; main composition no longer injects SLD projection/render dependencies after construction. |
| GF-SLD-WF-019 | **CLOSED — STATIC SOURCE RE-AUDIT** | `CanvasPlugin` consumes and identity-checks the same projection/render instances held by `CanvasComposition`; render-system scene identity is checked against the composition scene. |
| GF-SLD-WF-020 | **CLOSED — STATIC SOURCE RE-AUDIT** | `ProjectLoaded` clears/rebinds/reconciles projection state; `ProjectClosed` clears the projection registry and detaches the document; CanvasPlugin clears the render system when Application presentation is absent. Element lifecycle events reconcile from Application read models. |
| GF-SLD-WF-021 | **CLOSED — STATIC SOURCE RE-AUDIT** | CommandManager now exposes an Application pre-commit hook. Application placement coordination invokes `SLDService.execute(AddSLDNodeCommand, transaction)` before the same transaction commits. The coordinator no longer issues Add/Remove SLD commands as a second transaction. Undo reverses SLD projection before Core creation inverse; redo re-executes the original placement command and recreates exactly one deterministic projection node. |

### Closure evidence — affected call relationships

- **Placement:** `ModelPlacementTool._build_command()` → immutable model command metadata → `Application.execute()` → `CommandManager` transaction → Core model handler → Application pre-commit placement coordinator → `SLDService` → `SLDDocument` → post-commit semantic event → `SLDReadSynchronizer` reconciliation → `SLDCanvasProjection` → `SLDCanvasSnapshot` → `SLDCanvasRenderSystem`.
- **Removal:** Core delete command → Application `ElementRemoved` → `SLDReadSynchronizer.synchronize_network()` stale projection reconciliation → canvas snapshot/render. No independent SLD delete transaction is initiated by `SLDUpdateCoordinator`.
- **Project replacement:** `ProjectClosed` → projection registry clear/document detach → canvas refresh/clear; `ProjectLoaded` → projection registry clear → Application presentation bind → network/protection reconciliation → canvas projection/render.
- **Undo/redo:** the coordinated placement projection mutation is recorded in the same Transaction undo journal as the Core mutation; no second CommandManager history entry is created.
- **Ownership:** projection-owned SLD nodes remain tagged with `projection_source`; engineer-owned nodes are not overwritten by projection reconciliation.

**Runtime verification:** **UNVERIFIED / DEFERRED by instruction.**

## 2026-09-25 — GF-SLD-WF-014..021 — final consolidated SLD workflow re-audit

**Repository:** madhuri196mishra-cpu/GridForge  
**Branch:** main  
**Author:** Subhendu Mishra  
**Verification mode:** static source inspection only. pytest, unit/integration execution, CI, startup, GUI/runtime smoke tests, and application execution were not performed.

| Finding | Status | Static evidence |
|---|---|---|
| GF-SLD-WF-014 | **CLOSED** | PanelsPlugin.initialize() creates the visible EquipmentPanelWidget and binds the canonical PluginContext.equipment_registry and tool_manager; EquipmentPanelWidget.activate_equipment() resolves the definition through that registry and activates the canonical ToolManager. The legacy logical EquipmentPanel is not composed as the visible widget. |
| GF-SLD-WF-015 | **CLOSED** | ModelPlacementTool._build_command() carries presentation_x/presentation_y; BusTool carries x/y into canonical CREATE_BUS and Application._coordinate_pre_commit() now normalizes that compatibility form and resolves bus_id. The Application pre-commit hook projects the SLD node in the same transaction. SLDReadSynchronizer, SLDCanvasProjection, and the renderer preserve the committed presentation coordinates. |
| GF-SLD-WF-016 | **CLOSED** | Retired ui/equipment/EquipmentConnection, ConnectionManager, and topology adapter are absent from the active tree. ui/sld/sld_model.py owns SLDConnection as presentation/document state, while Core terminal connectivity is represented by Application/Core connection commands. Remaining ui/connections/Connection is non-authoritative interaction/presentation state and does not mutate Core. |
| GF-SLD-WF-017 | **CLOSED** | EquipmentManager is retired. SLDGraphicsItemFactory resolves ElementReadModel from Application.read_network() / protection read state and EquipmentFactory.create_from_read_model() creates transient presentation equipment. No UI equipment collection is the engineering authority. |
| GF-SLD-WF-018 | **CLOSED** | PresentationBootstrap composes the canonical equipment/symbol registries, semantic realization, and SLDGraphicsItemFactory; main.py constructs one SLDCanvasProjection and one SLDCanvasRenderSystem, then injects both into the single CanvasComposition. SLDCanvasRenderSystem.synchronize() consumes only immutable SLDCanvasSnapshot data. |
| GF-SLD-WF-019 | **CLOSED** | CanvasComposition owns the scene, ToolManager-related canvas services, SLD projection, render system, and selection projection. CanvasPlugin only consumes that composition and asserts identity against the same PluginContext projection/render instances and scene. |
| GF-SLD-WF-020 | **CLOSED** | UIUpdateBoundary is the single Application-event ingress; UIProjectionCoordinator routes lifecycle/model events to SLDUpdateCoordinator. ProjectLoaded clears projection state, binds the new presentation, reconciles network/protection, and refreshes the canvas. ProjectClosed clears projection state, detaches the document, and invokes the CanvasPlugin synchronization path, which clears the render system when no active presentation exists. |
| GF-SLD-WF-021 | **CLOSED** | Application._coordinate_pre_commit() invokes SLDService.execute(AddSLDNodeCommand, transaction) before CommandManager commits. SLDService records the SLD inverse in that same Transaction. A projection failure therefore causes the canonical transaction to roll back rather than creating a second SLD history operation. |

### Final end-to-end static proof

EquipmentPanelWidget._on_item_clicked() → activate_equipment() → EquipmentRegistry.require() → canonical ToolManager.activate() → concrete placement Tool → live PreviewLayer only → immutable model command → ToolBase.execute_command() → Application.execute() → CommandManager._execute_command() → Core handler → Application pre-commit SLD projection → SLDService / SLDDocument transaction mutation → commit → semantic ElementCreated/related event → UIUpdateBoundary → UIProjectionCoordinator → SLDUpdateCoordinator.refresh() → SLDReadSynchronizer → SLDDocument/SLDModel → SLDCanvasProjection.project() → SLDCanvasSnapshot → SLDCanvasRenderSystem.synchronize() → SLDGraphicsItemFactory / semantic realization → GridScene.

### Final corrections made during this pass

1. Removed the stale initial_positions reference from ui/events/sld_update_coordinator.py; the current event-driven path now reconciles directly from Application read state.
2. Normalized the Bus compatibility placement path in core/application/application.py so PlaceBusCommand's presentation-only x/y and bus_id participate in the same Application pre-commit SLD transaction as all other placement commands.
3. Re-audited the affected paths after those corrections and recorded the result in this master register.

**Runtime verification:** **UNVERIFIED / DEFERRED by instruction.**


## 2026-09-25 — SLD Engineer Entry Surface / Equipment Palette Remediation

**Repository:** madhuri196mishra-cpu/GridForge  
**Branch:** main  
**Author:** Subhendu Mishra  
**Verification mode:** static source inspection only. pytest, CI, startup, GUI/runtime execution were not performed.

| Finding | Status | Static evidence |
|---|---|---|
| GF-SLD-UI-PALETTE-001 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | PresentationBootstrap.equipment_registry is the single EquipmentRegistry.create_default() catalogue; PluginContext passes that exact instance to PanelsPlugin; PanelsPlugin.initialize() composes EquipmentPanelWidget and calls bind_equipment_runtime(context.equipment_registry, context.tool_manager); the widget populates its QListWidget from catalogue(); canonical SLD_WORKSPACE places equipment on PanelArea.LEFT with visible=True; main.py registers the equipment dock with WorkspaceRealizer before WorkspaceController.activate_default(). No second live EquipmentRegistry is composed by the Browser. |
| GF-SLD-UI-PALETTE-002 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | EquipmentPanelWidget._on_item_clicked() resolves the canonical equipment type and activate_equipment() calls EquipmentRegistry.require() → definition.tool_id → ToolManager.activate(). create_default_tool_factories() provides factories for every default catalogue tool ID. Concrete tools route through SnapSystem, transient preview state, immutable Application command construction, ToolBase.execute_command() → Application.execute() → CommandManager → Core handlers. Line/Cable/Transformer use the same Application boundary and do not perform direct Core mutation. |
| GF-UI-COMPOSE-001 | **AGENT CORRECTED → RE-AUDIT REQUIRED** | main.py now resolves and validates canvas_plugin.synchronize_sld before defining/subscribing handle_project_workspace_changed; the callback therefore cannot reference an uninitialized synchronization local. |

Register status discipline: these findings are not marked CLOSED. Static correction is recorded as AGENT CORRECTED → RE-AUDIT REQUIRED. Runtime verification remains deferred.
