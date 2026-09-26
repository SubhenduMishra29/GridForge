"""Solver-owned combined dynamic state layout.

Author: Subhendu Mishra

Machine state and Dynamic Control state remain distinct slices in one
solver-owned global vector.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class DynamicControlStateSlice:
    controller_id: str
    start: int
    stop: int

    @property
    def size(self) -> int:
        return self.stop - self.start


class GlobalStateLayout:
    """Deterministic machine-then-controller global state layout."""

    def __init__(self, machine_size: int, controllers: Iterable[tuple[str, int]] = ()) -> None:
        if int(machine_size) < 0:
            raise ValueError("machine_size cannot be negative.")
        self.machine_size = int(machine_size)
        offset = self.machine_size
        slices = []
        for controller_id, size in controllers:
            controller_id = str(controller_id).strip()
            size = int(size)
            if not controller_id or size <= 0:
                raise ValueError("controller identity and positive state size are required.")
            slices.append(DynamicControlStateSlice(controller_id, offset, offset + size))
            offset += size
        self._controller_slices = tuple(slices)

    @property
    def controller_slices(self) -> tuple[DynamicControlStateSlice, ...]:
        return self._controller_slices

    @property
    def state_size(self) -> int:
        return self._controller_slices[-1].stop if self._controller_slices else self.machine_size

    def controller_slice(self, controller_id: str) -> DynamicControlStateSlice:
        for item in self._controller_slices:
            if item.controller_id == str(controller_id):
                return item
        raise KeyError(controller_id)


__all__ = ["DynamicControlStateSlice", "GlobalStateLayout"]
