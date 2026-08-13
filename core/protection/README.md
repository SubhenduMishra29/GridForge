# GridForge V2 Protection Subsystem

## Overview

The `core/protection/` package provides the protection-system execution
framework for GridForge V2.

The subsystem is responsible for representing, executing, and collecting
results from protection functions while maintaining a strict separation
between:

- physical equipment;
- measurement infrastructure;
- protection-function logic;
- protection decisions;
- protection schemes;
- breaker/output operation.

The protection subsystem is designed for multifunction protection
architecture.

A physical Relay is therefore **not** assumed to represent one protection
function.

A single Relay may host multiple independent protection functions:

```text
Relay R1
│
├── 50  Instantaneous Overcurrent
├── 51  Time Overcurrent
├── 46  Negative Sequence
├── 67  Directional Overcurrent
└── 50BF Breaker Failure
