# ============================================================
# GridForge V2 — Electrical Insertion Contracts
# ============================================================

"""Declarative Application-owned equipment insertion contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InsertionContract:
    equipment_type: str
    insertion_mode: str
    terminal_mapping: tuple[str, str]
    required_parameters: tuple[str, ...] = ()


INSERTION_CONTRACTS = {
    "breaker": InsertionContract(
        equipment_type="breaker",
        insertion_mode="SERIES",
        terminal_mapping=("from", "to"),
    ),
    "disconnector": InsertionContract(
        equipment_type="disconnector",
        insertion_mode="SERIES",
        terminal_mapping=("from", "to"),
        required_parameters=("voltage_kv", "rated_current_a"),
    ),
    "transformer": InsertionContract(
        equipment_type="transformer",
        insertion_mode="SERIES",
        terminal_mapping=("FROM", "TO"),
        required_parameters=("r", "x"),
    ),
    "current_transformer": InsertionContract(
        equipment_type="current_transformer",
        insertion_mode="SERIES_PRIMARY",
        terminal_mapping=("P1", "P2"),
        required_parameters=("primary_rated_current_a", "secondary_rated_current_a"),
    ),
}


__all__ = ["InsertionContract", "INSERTION_CONTRACTS"]
