# GridForge V2 — Architecture Reconciliation Matrix

Baseline: `main` `4edcfd511300c868a30f2813ea1951fdc279374a`

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
