# GridForge V2 — Architecture Reconciliation Matrix

Historical reconciliation baseline: `main` @ `f27ef42a39333f5fb35522e5839d23f58a427207` (preserved for provenance). Current repository audit baseline: `madhuri196mishra-cpu/GridForge:main` @ `7b96f94182a1c879253cf101326388d0ce20bce6` (inspected 2026-10-21; full repository re-audit not yet established).

| Area | Frozen Requirement | Current Implementation Evidence | Status | Finding IDs | Root Cause |
|---|---|---|---|---|---|
| Core boundary | Core is authoritative electrical/domain truth; independent of Qt/UI | Current composition imports Core from `main.py`; historical audits retain Core authority as baseline | REMEDIATED — VERIFICATION DEFERRED | GF-MASTER-0041 | Broad consumer-level proof is incomplete |
| Application boundary | Sole UI↔Core orchestration/mutation boundary | `main.py` creates Application; historical C9 read facade and protection command boundary are documented | UNVERIFIED | GF-MASTER-0016, 0029, 0037 | Runtime and consumer-wide proof incomplete |
| UI/Core adapter | UI expresses intent through Application | Application/UI workspace adapters are present | UNVERIFIED | GF-MASTER-0016, 0037 | Execution path not fully verified |
| Command pipeline | immutable Command → Application.execute → CommandManager → Core | Protection closure documents this exact path | UNVERIFIED | GF-MASTER-0029, 0037 | End-to-end execution evidence absent |
| Undo/redo | Command history is authoritative for reversible mutation | Historical application findings exist; no complete current runtime sweep | UNVERIFIED | GF-MASTER-0037 | Divergent/legacy mutation paths require consumer verification |
| Transactions | Application/CommandManager owns mutation transactions | Protection correction explicitly keeps transaction ownership in CommandManager | UNVERIFIED | GF-MASTER-0029 | Runtime verification absent |
| Events | Core→Application→UI semantic events | Historical event vocabulary correction recorded | UNVERIFIED | GF-MASTER-0035 | Producer/consumer execution coverage incomplete |
| Revision | Application-level revision/state coordination | Historical dirty/revision audits exist; no executable repository-wide proof | UNVERIFIED | GF-MASTER-0036 | Multiple historical revision authorities |
| Validation | Validation remains authoritative and coordinated | Current architecture documents validation in Core/Application; full consumer audit incomplete | UNVERIFIED | GF-MASTER-0036 | Evidence fragmented |
| Studies | Studies consume prepared authoritative state | Power Flow, Short Circuit preparation boundaries are present | UNVERIFIED | GF-MASTER-0021, 0026, 0027 | Source-level remediation lacks execution proof |
| Study provenance | Results must carry stable revision/identity provenance | Historical audit explicitly identified inconsistent revision/result provenance | OPEN | GF-MASTER-0021, 0026, 0036 | Result contracts evolved unevenly |
| Persistence | `.gridforge` with manifest + project JSON is canonical | `pyproject` unrelated; historical persistence audit records package boundary | UNVERIFIED | GF-MASTER-0031, 0032 | Round-trip execution absent |
| Project lifecycle | Application owns load/reconstruction; Network owns authoritative reconstructed state | Main composition creates Network then Application; lifecycle audit records adapters | UNVERIFIED | GF-MASTER-0016, 0031 | Runtime reconstruction not executed |
| SLD model | SLD is projection, not second electrical database | SLDDocument/SLDProjection/SLDReadSynchronizer architecture documented | REMEDIATED — VERIFICATION DEFERRED | GF-MASTER-0038, 0039, 0040 |
| SLD projection | Read models flow through projection to canvas | C9 and UI audit document the projection stack | UNVERIFIED | GF-MASTER-0016, 0040 |
| SLD terminal identity | UI terminal identity ultimately resolves to Core Terminal | Historical terminal/equipment audit remains unresolved at consumer level | OPEN | GF-MASTER-0003, 0038 |
| Equipment identity | Stable equipment IDs propagate through read/projection | `equipment_id` audit checkpoint established; complete current sweep not proven | REMEDIATED — VERIFICATION DEFERRED | GF-MASTER-0038, 0040 |
| EndpointReference | Canonical endpoint resolver owns endpoint interpretation | Historical current-head audit identified `core/network/endpoint.py` as canonical | UNVERIFIED | GF-MASTER-0003 |
| Connection lifecycle | UI connection is not topology authority | Frozen architecture says `core/network` owns global connectivity | OPEN | GF-MASTER-0039 |
| Topology | Core/network owns global connectivity | Contract explicitly states this | UNVERIFIED | GF-MASTER-0039, 0041 |
| Switching | Breaker state is physical model state; topology interprets it | Protection command path ends in Core Breaker mutation | UNVERIFIED | GF-MASTER-0029 |
| Protection | Protection decision/measurement/trip remains domain/application separated | Relay/measurement architecture and Application trip boundary documented | UNVERIFIED | GF-MASTER-0027, 0028, 0029 |
| Relay | Relay remains a Core/protection model, not UI-only | Historical register says Relay/ProtectionElement/RelayBase architecture preserved | UNVERIFIED | GF-MASTER-0028, 0034 |
| CT/PT/CVT | Measurement channels are explicit and authoritative | Historical measurement audit reconciled CT/PT/CVT/MeasurementPoint/MeasurementChannel | UNVERIFIED | GF-MASTER-0028 |
| Control | Control commands/events interact through Application/Core | Complete current control chain not demonstrated | OPEN | GF-MASTER-0042 |
| Dynamics | Dynamic solver consumes explicit dynamic models and state vector | Current `state_vector.py` references missing `DynamicMachineModel`; `__init__.py` exports `DynamicState` | CONFIRMED | GF-MASTER-0011, 0012 |
| Plugin platform | Plugins compose capabilities, not electrical/layout authority | PluginContext/Manager/Loader boundaries documented | UNVERIFIED | GF-MASTER-0020 |
| UI lifecycle | UILifecycle/workspace teardown is canonical | MainWindow/bootstrap/lifecycle code exists; runtime execution unproven | UNVERIFIED | GF-MASTER-0016 |
| Documentation | Documentation must reflect current architecture/evidence | Multiple historical closure docs conflict with current unresolved evidence | OPEN | GF-MASTER-0005 |
| Runtime/startup | Fresh-process import/startup must be proven | Startup workflow exists; no successful run established; current Dynamics API is inconsistent | OPEN | GF-MASTER-0007, 0008, 0011, 0012 |
| Testing | Resolution requires executable evidence | Registers repeatedly state tests were not executed | OPEN | GF-MASTER-0044 |
| Migration/redundancy | One authority per responsibility; no deletion from search absence | Historical registers explicitly warn indexed absence is insufficient | REMEDIATED — VERIFICATION DEFERRED | GF-MASTER-0043 |
| Numerical PU | One canonical PU conversion authority; YBus consumes prepared PU | Current-head audit records `PerUnitSystem` and prepared YBus boundary | UNVERIFIED | GF-MASTER-0025 |
| Transformer basis | Basis explicit; conversion in preparation/migration | Current-head audit records `pu`/`engineering` basis and pending verification | UNVERIFIED | GF-MASTER-0023 |
| Reactive equipment | Capacitor/Reactor feed prepared shunt representation | Historical remediation records `PreparedShunt` integration | UNVERIFIED | GF-MASTER-0024 |
| Short Circuit | Detached sequence/fault input before solver | Historical remediation added Short Circuit preparation boundary | UNVERIFIED | GF-MASTER-0026 |
| Persistence engineering truth | Engineering units/bases preserved, ambiguity rejected | Migration audit documents explicit metadata/ambiguity rejection | UNVERIFIED | GF-MASTER-0032 |

## 2026-09-28 — Historical effective re-audit (authority statement superseded 2026-10-02)

The matrix above contains historical/status snapshots and is retained as audit chronology. Its authority statement naming `pandaraseswari03-collab/GridForge` is a historical snapshot superseded by the 2026-10-02 authority reconciliation. Current implementation and active audit/register target is `madhuri196mishra-cpu/GridForge:main`; `SubhenduMishra29/GridForge` is reference/audit evidence only when explicitly designated for a historical cycle. The final source re-audit found no new Core/Application architectural bypass. GF-MASTER-0104 was corrected in the styling boundary only: graphics helpers now resolve active Theme tokens and the canvas token is white. No Core/Application authority was duplicated. Runtime/GUI evidence remains deferred.

## 2026-09-28 — Superseding effective static re-audit

The historical table above is retained as chronology. For current source authority, the effective static re-audit is the current `main` source at `cbe167a533598c63afaba9a30cd10906370548b1`.

- Core/Application boundary: no new UI/Core mutation bypass identified in the current source pass.
- Dynamics: the historical `state_vector.py` artifact is absent; current `core/solver/dynamics/__init__.py` exports implemented symbols and does not export obsolete `DynamicState`; current `machine_models.py` does not contain the historical `DynamicMachineModel` dependency.
- SLD placement: `ModelPlacementTool` uses transient `CreationDraft` state, preview-layer presentation, and explicit Application creation commands; it does not create persistent SLD nodes during preview.
- SLD realization: `SLDCanvasRenderSystem` resolves nodes through `SemanticPresentationRealization` and `SLDGraphicsItemFactory`; failures are retained as structured diagnostics.
- Palette: `EquipmentPanelWidget` resolves definitions through `EquipmentRegistry`, activates the definition's `tool_id` through `ToolManager`, and renders icons through the canonical `SymbolRegistry`. `PaletteSymbolAdapter` now renders canonical text primitives and active style tokens.
- Canvas styling: `StyleTokens.canvas_background` is `#FFFFFF`; graphics helpers resolve active QApplication tokens when no explicit token set is supplied.
- Runtime/GUI/study execution remains deferred wherever the register requires executable evidence.

The historical OPEN/CONFIRMED wording in earlier matrix rows must not be interpreted as current status where the effective CSV/register has since reconciled the finding. Historical rows remain preserved for audit chronology.

## 2026-11-02 — Documentation refresh reconciliation (current repository authority)

The dated sections above are retained as historical audit evidence. Their repository authority statements and implementation snapshots are not current status for this refresh.

- **Authoritative repository:** `SubhenduMishra29/GridForge`, branch `main`. The README and current architecture refresh use mainline commit `a9e07287c90667a7aae8bcc060e4e2d0cadf261e` as the implementation baseline.
- **Merged PR #908 / current-main D15F register:** includes Protection Study scenario snapshots; supported CT terminal-current sampling and ANSI 50N/51N residual bindings; tap-aware transformer sequence preparation; explicit Grid/Generator source equivalents and neutral/earth paths; Line/Cable SLD-derived conductor graph; Breaker/Switch/Disconnector/Fuse pole paths; Transformer winding graph/multiport, grounded-wye earth return, evidence-bound zero-sequence and delta-loop MNA increments through D15F-37. Each is limited to its explicit construction and input contract.
- **Merged PR #909:** changes draft-wire preview presentation only; it does not change canonical electrical connectivity.
- **Not merged at this baseline:** PRs #912–#918 are open/draft follow-up workstreams. Their proposed code must not be described as mainline capability until individually reconciled and merged.
- **Architecture distinction:** conventional Simple Wire terminal-to-terminal relationships remain separate from the explicit phase-domain physical conductor graph. Neither is inferred from SLD geometry.
- **Open evidence obligations:** automatic Motor source equivalent and unsupported machine/load/arc-fault/switching models; complete neutral CT/CBCT coverage; full persistence round-trip and construction configurators; complete Protection Study runtime integration; numerical validation and commissioning. Supported SLD-derived graph construction exists for the D15F equipment cases and must not be described as a general-purpose graph editor.
- **Verification statement:** PR #908 records remote source inspection/integration review only; no tests/CI, syntax/import checks, persistence round-trip, numerical fixtures or end-to-end runtime execution were run.

This section is a documentation authority correction, not a new implementation audit. For the consolidated frozen architecture and exact evidence boundaries, see [GRIDFORGE_V2_ARCHITECTURE_2026-11-02.md](../docs/architecture/GRIDFORGE_V2_ARCHITECTURE_2026-11-02.md) and [PROTECTION_PHASE_DOMAIN_ARCHITECTURE_AMENDMENT_2026-11-02.md](../docs/architecture/PROTECTION_PHASE_DOMAIN_ARCHITECTURE_AMENDMENT_2026-11-02.md).


## 2026-11-03 — Signal infrastructure and heterogeneous simulation architecture amendment

This is an approved additive architecture direction, not an implementation or runtime-verification claim. See [SIGNAL_INFRASTRUCTURE_AND_HETEROGENEOUS_SIMULATION_AMENDMENT_2026-11-03.md](../docs/architecture/SIGNAL_INFRASTRUCTURE_AND_HETEROGENEOUS_SIMULATION_AMENDMENT_2026-11-03.md).

| Area | Frozen / amended requirement | Status | Evidence / next audit |
|---|---|---|---|
| Signal identity and measurement | Shared canonical signal/measurement contracts for physical and virtual instruments; engineering units, source identity, timestamp, quality and provenance | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Audit existing CT/PT/CVT, MeasurementChannel, RTD/thermocouple and sensor contracts before adding types |
| Acquisition and I/O | Explicit CT/PT, RTD/thermocouple, AI/AO/DI/DO and communication acquisition interfaces; channel availability and diagnostics | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Reconcile channel registry, adapters, calibration and failure semantics |
| Signal processing/routing | Scaling, filtering, quality/freshness and explicit consumer subscriptions; no duplicate Control/Protection measurement authorities | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Audit signal routes and consumer binding |
| Protection/Control consumers | Shared signals; separate Protection and Control execution and decision ownership; explicit cross-domain interfaces | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Trace Control canvas inputs, relay inputs, interlocks, blocking and permissives |
| Device lifecycle | Decision ≠ command ≠ output activation ≠ physical response ≠ feedback | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Reconcile trip/close, contactor, output-channel and feedback paths |
| Historian | Shared time-series/event/SOE/disturbance recording with real-vs-simulated source provenance | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Audit existing historian, event and archive services before adding storage |
| Simulation model contract | One hardware-independent equipment physics model; no separate CPU/GPU physics definitions | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Audit existing solver/dynamics and Motor Dynamics plugin contracts |
| CPU backend | Universal reference implementation and fallback | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Establish reference results and model lifecycle |
| GPU backend | Suitable parallel numerical physics and batch/scenario execution; capability- and workload-aware selection | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Verify supported hardware/runtime and numerical tolerance |
| NPU backend | Supported AI inference/predictive analytics; never substitute for safety-critical protection calculations | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Verify model/operator/provider/device support and advisory provenance |
| Simulation orchestration | Explicit simulation clock, scheduling, state/result buffers, backend provenance, deadline diagnostics and safe failure handling | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Define CPU/GPU/NPU execution and timing contracts |
| Virtual instrumentation | Virtual instruments use the same measurement/routing contracts as physical sources | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Motor reference scenario |
| Closed-loop simulation | Equipment physics → virtual measurements → Protection/Control → command → simulated actuation → feedback → Historian | ARCHITECTURE APPROVED — IMPLEMENTATION NOT AUDITED | Motor Dynamics plugin is first reference integration |
| Safety boundary | Desktop simulation is not a hard-real-time or sole safety-critical protection controller; HIL requires separate architecture | FROZEN CONSTRAINT | Preserve explicit timing, isolation, watchdog and commissioning requirements for future HIL |

No tests/CI or runtime checks were performed as part of this documentation-only architecture update.