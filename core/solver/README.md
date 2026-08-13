# GridForge V2 Solver Layer

## Overview

The `core/solver/` package provides the numerical computation framework for GridForge V2.

The solver layer is responsible for transforming authoritative GridForge network, model, and study inputs into deterministic numerical solutions.

It contains the numerical engines required for:

* power-flow analysis;
* short-circuit analysis;
* contingency and N-1 studies;
* dynamic simulation;
* common numerical operations;
* future specialized numerical solvers.

The fundamental principle is:

```text
Authoritative Model / Network State
              │
              ▼
         Solver Input
              │
              ▼
        Numerical Solver
              │
              ▼
       Numerical Result
```

The solver layer performs **numerical computation**.

It does not own the physical model, GUI state, project persistence, or protection-function architecture.

---

# 1. Architectural Position

The solver layer sits between the authoritative GridForge model/network representation and the analysis/results layer.

```text
                    GridForge Model
                          │
                          ▼
                    core.network
                          │
                          ▼
                  Solver / Analysis Input
                          │
                          ▼
                     core.solver
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
      Power Flow     Short Circuit      Dynamics
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                    Numerical Results
                          │
                          ▼
                    core.analysis
```

The solver does not become the authoritative owner of the physical network.

The model and network layers remain authoritative for their respective domains.

---

# 2. Core Solver Principle

The fundamental V2 relationship is:

```text
Model / Network
       │
       ▼
Numerical Representation
       │
       ▼
Solver
       │
       ▼
Result
```

The solver consumes authoritative inputs and produces numerical results.

It should not silently modify the underlying physical model merely to complete a calculation.

The distinction is:

```text
Model
    = What the physical system is

Network
    = Electrical/topological representation of that system

Solver
    = How the mathematical problem is solved

Result
    = What the numerical calculation produced
```

---

# 3. Package Structure

The solver layer is organized by numerical domain and shared numerical infrastructure.

The current architecture is:

```text
core/
└── solver/
    ├── __init__.py
    ├── common/
    │   ├── __init__.py
    │   ├── mismatch.py
    │   └── jacobian.py
    │
    ├── power_flow/
    │   └── ...
    │
    ├── short_circuit/
    │   └── ...
    │
    ├── dynamics/
    │   └── ...
    │
    └── contingency/
        └── ...
```

The exact implementation inventory within each solver domain may evolve independently, but the domain boundaries are architectural.

---

# 4. Solver Responsibilities

`core/solver/` is responsible for:

* numerical formulation;
* numerical iteration;
* convergence control;
* matrix construction where solver-specific;
* sparse numerical operations;
* nonlinear solution;
* linear solution;
* dynamic state integration;
* fault-network solution;
* contingency evaluation;
* solver diagnostics;
* convergence information;
* numerical result generation.

It is not responsible for:

* physical equipment ownership;
* GUI rendering;
* GUI interaction;
* project persistence;
* protection-function execution;
* relay coordination;
* breaker control;
* permanent network topology ownership.

---

# 5. Numerical Reference Layer

GridForge V2 provides a common numerical reference layer under:

```text
core/solver/common/
```

The current frozen numerical reference foundation includes:

```text
core/solver/common/
├── __init__.py
├── mismatch.py
└── jacobian.py
```

These modules provide reusable numerical primitives for nonlinear power-system solution.

The purpose of this layer is to prevent individual solvers from implementing incompatible versions of fundamental numerical operations.

---

# 6. `mismatch.py`

`mismatch.py` provides common mismatch calculations used by nonlinear power-system solvers.

Conceptually:

```text
Specified State
       │
       ▼
Calculated State
       │
       ▼
    Mismatch
       │
       ▼
Convergence / Correction
```

For power-flow problems, mismatch vectors may include:

```text
ΔP
ΔQ
```

The mismatch implementation should remain:

* deterministic;
* vectorized where appropriate;
* numerically explicit;
* independent of GUI state;
* reusable by multiple solver strategies.

The module does not own the solver iteration loop.

---

# 7. `jacobian.py`

`jacobian.py` provides common Jacobian construction functionality.

For Newton-type power-flow solution:

```text
             ∂P/∂θ     ∂P/∂V
J =
             ∂Q/∂θ     ∂Q/∂V
```

The Jacobian layer is responsible for numerical Jacobian assembly.

It does not decide:

* which solver algorithm should be used;
* how many iterations should be performed;
* how the GUI displays convergence;
* how a physical model is persisted.

Those decisions belong to the appropriate solver/application layers.

---

# 8. Power-Flow Solver

The GridForge V2 power-flow solver is responsible for nonlinear steady-state network solution.

Its conceptual workflow is:

```text
Network Model
      │
      ▼
Initial State
      │
      ▼
Y-bus / Network Equations
      │
      ▼
Power Calculation
      │
      ▼
Mismatch
      │
      ▼
Jacobian
      │
      ▼
Correction
      │
      ▼
Convergence Test
      │
   ┌──┴──┐
   │     │
  No    Yes
   │     │
   └─────┤
         ▼
      Solution
```

The solver architecture is designed to support robust nonlinear solution methods including:

* Newton-Raphson;
* adaptive line search;
* Armijo-type damping;
* trust-region methods;
* Levenberg-Marquardt stabilization;
* hybrid nonlinear solution strategies;
* continuation power flow;
* fast contingency screening;
* CPU and future GPU acceleration.

These are solver strategies.

They must not leak into the physical model layer.

---

# 9. Power-Flow Solver Architecture

The power-flow solver operates on a mathematical representation derived from the authoritative network.

```text
core.model
     │
     ▼
core.network
     │
     ├── topology
     ├── per-unit
     └── Y-bus
     │
     ▼
core.solver.power_flow
     │
     ├── mismatch
     ├── Jacobian
     ├── nonlinear iteration
     ├── convergence control
     └── solution
     │
     ▼
Power-Flow Result
```

The solver must not duplicate the authoritative network model.

---

# 10. Per-Unit Boundary

GridForge V2 uses a dedicated per-unit infrastructure.

The solver consumes the canonical per-unit representation rather than implementing independent base-conversion rules inside each solver.

Conceptually:

```text
Physical Equipment
       │
       ▼
Canonical Per-Unit Representation
       │
       ▼
Network
       │
       ▼
Solver
```

This prevents inconsistent voltage-base and impedance-base calculations between numerical domains.

---

# 11. Short-Circuit Solver

The short-circuit solver provides fault-network numerical analysis.

Its responsibility is to calculate electrical quantities associated with specified fault conditions.

Conceptually:

```text
Network
   │
   ▼
Fault Definition
   │
   ▼
Faulted Network
   │
   ▼
Numerical Solution
   │
   ▼
Fault Currents / Voltages
```

The short-circuit solver must not become the owner of:

* protection decisions;
* relay logic;
* breaker operation;
* protection coordination.

The relationship is:

```text
Short-Circuit Solver
        │
        ▼
Fault Electrical Quantities
        │
        ▼
Protection / Analysis Consumers
```

---

# 12. Dynamics Solver

The dynamics subsystem provides time-domain numerical simulation.

Its purpose is to solve differential and algebraic system behavior over time.

The conceptual structure is:

```text
Initial Dynamic State
        │
        ▼
t = t₀
        │
        ▼
Evaluate Dynamic Equations
        │
        ▼
Numerical Integration
        │
        ▼
Update State
        │
        ▼
t = t + Δt
        │
        └───────────────┐
                        │
                        ▼
                   Next Step
```

The dynamics solver may consume:

* generator models;
* dynamic model parameters;
* network state;
* AVR models;
* governor models;
* PSS models;
* other dynamic plugins.

The model layer remains responsible for the physical equipment.

The dynamics solver remains responsible for numerical time-domain execution.

---

# 13. Dynamics Architecture

The V2 dynamics architecture is designed around separation between:

```text
Physical Equipment Model
        │
        ▼
Dynamic Model / Plugin
        │
        ▼
Dynamic Runtime State
        │
        ▼
Dynamics Solver
```

For example:

```text
Generator
   │
   ├── AVR
   ├── Governor
   └── PSS
        │
        ▼
Dynamics Solver
```

The generator model itself must not become the owner of the numerical integration loop.

---

# 14. Contingency Solver

The contingency subsystem evaluates network conditions under defined contingencies.

Typical applications include:

* N-1 analysis;
* branch outage;
* generator outage;
* transformer outage;
* selected equipment outages;
* fast screening;
* contingency ranking.

Conceptually:

```text
Base Case
    │
    ▼
Contingency Definition
    │
    ▼
Modified Study Case
    │
    ▼
Solver
    │
    ▼
Contingency Result
```

Contingency logic should reuse the appropriate underlying numerical solver rather than duplicating complete power-flow or short-circuit algorithms.

---

# 15. Solver Reuse

A core GridForge V2 principle is:

```text
One Numerical Capability
        ↓
Reusable Solver Infrastructure
```

For example, contingency analysis should not create a second independent Newton-Raphson implementation.

Instead:

```text
Contingency Solver
       │
       ▼
Power-Flow Solver
       │
       ▼
Common Numerical Layer
```

This improves:

* numerical consistency;
* maintainability;
* testing;
* performance;
* solver reliability.

---

# 16. Solver Results

Solver results are outputs of numerical computation.

They may contain:

* convergence status;
* iteration count;
* residual norm;
* solved voltages;
* solved angles;
* branch flows;
* generator outputs;
* fault currents;
* fault voltages;
* dynamic trajectories;
* contingency metrics;
* numerical diagnostics.

A result object represents the outcome of a calculation.

It does not become a replacement for the authoritative physical model.

---

# 17. Convergence

Convergence is a first-class numerical concept.

A solver should explicitly report:

* converged / not converged;
* iteration count;
* residual or mismatch norm;
* numerical termination reason;
* applicable solver diagnostics.

The solver must not silently return apparently valid numerical data when convergence has failed.

Conceptually:

```text
Numerical Iteration
       │
       ▼
Convergence Test
       │
   ┌───┴────┐
   │        │
Converged  Failed
   │        │
   ▼        ▼
Solution  Diagnostic
```

---

# 18. Numerical Robustness

GridForge V2 solver architecture is intended for engineering-grade numerical robustness.

The numerical layer should support appropriate mechanisms such as:

* sparse matrix operations;
* vectorized computation;
* scaling;
* damping;
* line search;
* trust regions;
* regularization;
* continuation;
* robust initialization;
* explicit convergence criteria;
* numerical diagnostics.

Robustness mechanisms belong in the numerical layer rather than being hidden inside physical model classes.

---

# 19. Sparse Numerical Architecture

Large power-system networks require sparse numerical representations.

GridForge V2 therefore favors:

```text
Sparse Matrix
      │
      ▼
CSR / compatible sparse representation
      │
      ▼
Vectorized Numerical Operations
      │
      ▼
Solver
```

Dense numerical structures should not be introduced as the default representation for large-system calculations when a sparse representation is appropriate.

---

# 20. CPU and GPU Execution

The solver architecture is designed to permit multiple numerical execution backends.

Conceptually:

```text
                  Solver Algorithm
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
          CPU Backend          GPU Backend
             │                     │
             └──────────┬──────────┘
                        ▼
                   Numerical Result
```

GPU acceleration is an implementation strategy.

It must not alter the solver's architectural contracts or introduce GPU-specific assumptions into:

* model objects;
* network objects;
* GUI objects;
* protection objects.

---

# 21. Solver Determinism

Where the numerical method permits it, solver execution should be deterministic for identical inputs and configuration.

Determinism includes:

* defined initialization;
* defined iteration order;
* stable matrix assembly;
* explicit solver settings;
* explicit convergence criteria;
* deterministic contingency ordering;
* reproducible result metadata.

Parallel execution must not silently introduce nondeterministic model state.

---

# 22. Solver Configuration

Solver configuration should remain separate from solver runtime state.

Conceptually:

```text
Solver
│
├── Configuration
│     ├── tolerance
│     ├── max_iterations
│     ├── method
│     └── numerical options
│
└── Runtime
      ├── current iteration
      ├── residual
      ├── matrices
      └── temporary state
```

Configuration represents user/study-selected numerical behavior.

Runtime represents transient execution state.

Neither should be confused with the persistent physical model.

---

# 23. Solver Runtime State

Transient numerical state may include:

* iteration vectors;
* Jacobians;
* residuals;
* factorization data;
* solver workspaces;
* integration states;
* temporary sparse matrices;
* convergence history.

This state belongs to the solver execution.

It must not become authoritative project state.

---

# 24. Solver and Analysis Separation

GridForge V2 distinguishes between **analysis orchestration** and **numerical solving**.

Conceptually:

```text
Analysis
   │
   ├── defines study intent
   ├── prepares inputs
   ├── interprets results
   └── exposes study-level API
           │
           ▼
        Solver
           │
           ├── numerical formulation
           ├── iteration
           ├── convergence
           └── numerical result
```

The solver should not become a general study-management layer.

Likewise, the analysis layer should not duplicate numerical algorithms.

---

# 25. Solver and Protection Separation

Protection functions may consume results produced by solvers.

However:

```text
Solver
   ≠
Protection Engine
```

For example:

```text
Short-Circuit Solver
       │
       ▼
Fault Current / Voltage
       │
       ▼
Measurement / Protection Infrastructure
       │
       ▼
Protection Function
       │
       ▼
ProtectionDecision
```

The short-circuit solver does not execute relay logic.

Likewise, protection functions do not perform their own short-circuit network solution merely to obtain electrical quantities that should come from authoritative simulation/network infrastructure.

---

# 26. Solver and Model Separation

The solver consumes model information.

It does not own the physical equipment.

```text
Generator Model
       │
       ▼
Solver Input
       │
       ▼
Numerical Calculation
```

A solver must not silently modify the generator's authoritative engineering parameters to achieve numerical convergence.

If a study requires modified parameters, the study case or appropriate numerical representation should own those modifications.

---

# 27. Solver and GUI Separation

The solver is completely GUI-independent.

No solver implementation should depend on:

* PySide6;
* widgets;
* graphics scenes;
* GUI controllers;
* rendering;
* user-interface state.

The intended relationship is:

```text
GUI
 │
 ▼
Controller / Application Layer
 │
 ▼
Analysis / Study
 │
 ▼
Solver
```

Never:

```text
Solver
 │
 ▼
GUI
```

---

# 28. Solver and Persistence Separation

The solver does not perform project-file I/O.

It must not own:

* JSON serialization;
* file paths;
* file dialogs;
* project loading;
* project saving.

Persistence belongs to the dedicated serialization/project layer.

Solver configuration and results may be serialized by that layer when required, but serialization is not a solver responsibility.

---

# 29. Error Handling

Numerical failure must be explicit.

Appropriate failure conditions include:

* singular Jacobian;
* singular or ill-conditioned matrix;
* non-convergence;
* invalid numerical input;
* impossible operating point;
* invalid fault definition;
* integration failure;
* unsupported solver configuration.

The solver should provide meaningful diagnostics rather than silently producing invalid results.

Conceptually:

```text
Solver Failure
      │
      ├── Status
      ├── Reason
      ├── Diagnostics
      └── Relevant Numerical Information
```

---

# 30. Validation Boundary

Input validation should occur at appropriate architectural levels.

```text
Model Validation
       │
       ▼
Network Validation
       │
       ▼
Solver Input Validation
       │
       ▼
Numerical Execution
```

The solver may validate numerical preconditions required for its operation.

It should not become responsible for validating every possible physical-model invariant.

---

# 31. Solver Extensibility

The solver architecture is intentionally extensible.

Future numerical domains may include:

* optimal power flow;
* security-constrained OPF;
* electromagnetic transient simulation;
* harmonic analysis;
* state estimation;
* voltage stability;
* continuation methods;
* probabilistic studies;
* real-time simulation;
* hybrid CPU/GPU solvers.

New solver domains should reuse common numerical infrastructure where appropriate.

They should not destabilize the existing solver contracts.

---

# 32. Plugin Architecture

Specialized numerical algorithms may be provided through plugin mechanisms where appropriate.

A solver plugin should clearly define:

* input contract;
* configuration;
* runtime state;
* execution interface;
* result contract;
* numerical dependencies;
* capability metadata.

Plugins must not bypass the authoritative model/network boundaries.

---

# 33. Common Numerical Contracts

Shared numerical infrastructure should be preferred over duplicated implementations.

Examples include:

```text
Mismatch
Jacobian
Sparse Matrix Utilities
Linear Solvers
Convergence Criteria
Numerical Scaling
```

Where a numerical operation is genuinely common across solver domains, it belongs in the appropriate common numerical layer.

Domain-specific mathematics should remain inside the corresponding solver.

---

# 34. Power-System Numerical Flow

A typical GridForge V2 study follows:

```text
Physical Model
      │
      ▼
Network Representation
      │
      ▼
Per-Unit / Y-bus / Study Equations
      │
      ▼
Solver Initialization
      │
      ▼
Numerical Iteration
      │
      ▼
Convergence
      │
      ▼
Solver Result
      │
      ▼
Analysis / Study Layer
```

Each stage has a distinct responsibility.

---

# 35. Architectural Invariants

The following invariants must be preserved throughout GridForge V2.

## 35.1 Solver Does Not Own the Physical Model

```text
Model ≠ Solver
```

The solver consumes model/network information.

---

## 35.2 Solver Does Not Own GUI State

```text
Solver ≠ GUI
```

No numerical implementation may depend on GUI objects.

---

## 35.3 Solver Does Not Own Persistence

```text
Solver ≠ Persistence
```

Numerical code must not perform project-file I/O.

---

## 35.4 Solver Does Not Become Protection Logic

```text
Solver ≠ Protection Engine
```

Protection functions consume authoritative electrical information but remain in the protection architecture.

---

## 35.5 Analysis Does Not Duplicate Numerical Algorithms

```text
Analysis
   ↓
Solver
```

Study orchestration and numerical computation remain separate.

---

## 35.6 Numerical Runtime State Is Transient

Solver workspaces and iteration state are not authoritative project state.

---

## 35.7 Solver Results Are Outputs

A solver result does not replace the physical model.

---

## 35.8 Common Numerical Infrastructure Is Reusable

Fundamental numerical operations should not be independently reimplemented in every solver.

---

## 35.9 Deterministic Ordering Must Be Preserved

Where ordering affects numerical reproducibility, the ordering must be explicit and deterministic.

---

## 35.10 Numerical Failure Must Be Observable

Non-convergence and numerical failure must never be silently represented as successful results.

---

# 36. Dependency Direction

The intended dependency direction is:

```text
core.model
     │
     ▼
core.network
     │
     ▼
core.solver.common
     │
     ├──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼
power_flow    short_circuit    dynamics     contingency
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                            │
                            ▼
                       core.analysis
```

The dependency direction must not be reversed.

The solver should not depend on GUI implementation or application-level presentation logic.

---

# 37. Current Solver Foundation

The GridForge V2 solver architecture has established the following major numerical domains:

```text
core/solver/
├── common
├── power_flow
├── short_circuit
├── dynamics
└── contingency
```

The major frozen numerical foundations include:

```text
core/solver/common/
├── mismatch.py
└── jacobian.py
```

The major solver baselines are:

```text
Power Flow
    → GridForge Power Flow Solver V1.0

Short Circuit
    → GridForge Short-Circuit Solver V2.0

Dynamics
    → GridForge Dynamics Solver V2 baseline
```

These solver domains are intended to remain independently evolvable while sharing the common numerical foundation.

---

# 38. Future Numerical Architecture

The solver architecture is prepared for future expansion without changing the fundamental model/network boundary.

Potential future structure:

```text
core/solver/
│
├── common/
│
├── power_flow/
│
├── short_circuit/
│
├── dynamics/
│
├── contingency/
│
├── opf/
│
├── scopf/
│
├── state_estimation/
│
├── voltage_stability/
│
└── emt/
```

Each domain should expose a clear numerical contract.

A new solver should not introduce duplicated physical-model ownership.

---

# 39. Design Philosophy

GridForge V2 treats the solver layer as the **numerical execution engine of the digital twin**.

The solver answers:

> Given an authoritative model/network state and a defined study configuration, what numerical solution satisfies the required mathematical formulation?

It does not answer:

> What physical equipment exists?

That belongs to `core/model`.

It does not answer:

> How is the electrical network represented?

That belongs to `core/network`.

It does not answer:

> What protection function should operate?

That belongs to `core/protection`.

It does not answer:

> How should the result be displayed?

That belongs to the UI/application layer.

The resulting architecture is:

```text
                 DIGITAL TWIN
                      │
                      ▼
                 Physical Model
                      │
                      ▼
                  core.network
                      │
                      ▼
                Study Formulation
                      │
                      ▼
                 core.solver
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
      Power Flow  Short Circuit  Dynamics
          │           │            │
          └───────────┼────────────┘
                      ▼
                Numerical Result
                      │
                      ▼
                Analysis Layer
```

---

# 40. Freeze Status

**`core/solver/README.md` → FINALIZE / FREEZE**

This document is the package-level architectural reference for the GridForge V2 Solver Layer.

The solver architecture should be treated as a stable foundation.

Future solver changes should:

1. preserve the model/network/solver separation;
2. preserve the common numerical contracts;
3. preserve deterministic execution;
4. preserve explicit convergence and failure reporting;
5. avoid duplicating numerical infrastructure;
6. keep solver runtime state transient;
7. keep GUI and persistence outside the solver;
8. keep protection execution outside the numerical solver;
9. preserve existing solver-domain contracts;
10. add new numerical domains without destabilizing established solvers.

The guiding rule is:

```text
Preserve the numerical architecture.
Improve numerical capability without corrupting ownership boundaries.
```

---

# 41. Final Architectural Summary

The GridForge V2 solver layer is based on five fundamental separations:

```text
Physical Model
       ≠
Network Representation
```

```text
Network Representation
       ≠
Numerical Solver
```

```text
Numerical Solver
       ≠
Analysis Orchestration
```

```text
Numerical Result
       ≠
Physical Model State
```

```text
Solver
       ≠
Protection / GUI / Persistence
```

The resulting architecture is:

```text
                     Physical Model
                           │
                           ▼
                     core.network
                           │
                           ▼
                  Numerical Representation
                           │
                           ▼
                    core.solver.common
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Power Flow      Short Circuit      Dynamics
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                     Contingency
                           │
                           ▼
                    Solver Results
                           │
                           ▼
                    Analysis Layer
                           │
                           ▼
                 Application / Studies
```

This architecture provides GridForge V2 with a reusable numerical foundation capable of supporting increasingly advanced power-system studies while preserving strict separation between physical models, network representation, numerical execution, protection, analysis, GUI, and persistence.

**`core/solver/README.md` → FINALIZE / FREEZE**
