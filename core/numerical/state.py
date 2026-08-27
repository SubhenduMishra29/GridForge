# File: core/numerical/state.py

# GridForge V2

# Author: Subhendu Mishra

"""
Generic numerical state containers for GridForge V2.

Numerical state is derived computational state. It is not:
- physical Model state;
- Network topology state;
- Study semantics;
- Solver algorithm state;
- UI/SLD state;
- persistence state.

BusState stores bus-level numerical quantities.

DynamicState stores a generic numerical state vector whose meaning is
defined by the corresponding physical/dynamic model or study formulation.
"""

from **future** import annotations

from copy import deepcopy
from math import isfinite
from numbers import Real
from typing import Any

class BusState:
"""
Numerical state associated with one physical network bus.

```
BusState deliberately does not reference the physical Bus object and
does not determine PQ/PV/Slack classification.
"""

__slots__ = ("_vm", "_va", "_p", "_q")

def __init__(
    self,
    vm: Real = 1.0,
    va: Real = 0.0,
    p: Real = 0.0,
    q: Real = 0.0,
) -> None:
    self.vm = vm
    self.va = va
    self.p = p
    self.q = q

@staticmethod
def _validate_real(value: Real, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number.")

    value = float(value)

    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")

    return value

@property
def vm(self) -> float:
    return self._vm

@vm.setter
def vm(self, value: Real) -> None:
    value = self._validate_real(value, "vm")

    if value <= 0.0:
        raise ValueError("vm must be greater than zero.")

    self._vm = value

@property
def va(self) -> float:
    return self._va

@va.setter
def va(self, value: Real) -> None:
    self._va = self._validate_real(value, "va")

@property
def p(self) -> float:
    return self._p

@p.setter
def p(self, value: Real) -> None:
    self._p = self._validate_real(value, "p")

@property
def q(self) -> float:
    return self._q

@q.setter
def q(self, value: Real) -> None:
    self._q = self._validate_real(value, "q")

def copy(self) -> "BusState":
    """Return an independent copy."""
    return BusState(
        vm=self.vm,
        va=self.va,
        p=self.p,
        q=self.q,
    )

def validate(self) -> None:
    """Validate all stored bus quantities."""
    self.vm = self.vm
    self.va = self.va
    self.p = self.p
    self.q = self.q

def as_dict(self) -> dict[str, float]:
    """Return a backend-neutral representation."""
    return {
        "vm": self.vm,
        "va": self.va,
        "p": self.p,
        "q": self.q,
    }

def __repr__(self) -> str:
    return (
        "BusState("
        f"vm={self.vm!r}, "
        f"va={self.va!r}, "
        f"p={self.p!r}, "
        f"q={self.q!r}"
        ")"
    )
```

class DynamicState:
"""
Generic numerical dynamic state container.

```
The container stores values only. It does not define the physical
meaning, equations, dimensions, or integration method of the state.
"""

__slots__ = ("_values",)

def __init__(self, values: Any = None) -> None:
    self.values = values

@staticmethod
def _copy_values(values: Any) -> Any:
    if values is None:
        return None

    try:
        return values.copy()
    except AttributeError:
        return deepcopy(values)

@property
def values(self) -> Any:
    return self._values

@values.setter
def values(self, value: Any) -> None:
    self._values = self._copy_values(value)

def copy(self) -> "DynamicState":
    """Return an independent copy."""
    return DynamicState(self.values)

def validate(self) -> None:
    """
    Validate basic scalar/iterable numerical values.

    Detailed dimensional and equation-specific validation belongs
    to the corresponding numerical model or solver.
    """
    values = self.values

    if values is None:
        return

    if isinstance(values, Real):
        if isinstance(values, bool) or not isfinite(float(values)):
            raise ValueError(
                "Dynamic state contains a non-finite value."
            )
        return

    try:
        iterator = iter(values)
    except TypeError:
        return

    for value in iterator:
        if isinstance(value, Real):
            if isinstance(value, bool) or not isfinite(float(value)):
                raise ValueError(
                    "Dynamic state contains a non-finite value."
                )

def as_value(self) -> Any:
    """Return an independent copy of the stored values."""
    return self._copy_values(self.values)

def __repr__(self) -> str:
    return f"DynamicState(values={self.values!r})"
```

**all** = [
"BusState",
"DynamicState",
]
