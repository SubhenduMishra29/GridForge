# ============================================================
# File: tests/core/analysis/test_contingency_bus_outage_isolation.py
# GridForge V2 — Contingency Bus-Outage Isolation Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from core.analysis.contingency import ContingencyAnalysis


class FakeBus:
    def __init__(self, bus_id: str):
        self.id = bus_id
        self.in_service = True


class FakeTerminal:
    def __init__(self, bus):
        self.bus = bus


class FakeLine:
    def __init__(self, line_id: str, bus):
        self.id = line_id
        self.in_service = True
        self.terminals = (FakeTerminal(bus),)


class FakeNetwork:
    def __init__(self):
        self.buses = [FakeBus("bus-1"), FakeBus("bus-2")]
        self.lines = [FakeLine("line-1", self.buses[0])]
        self.transformers = []
        self.generators = []
        self.loads = []
        self.shunts = []


def test_bus_outage_uses_isolated_network_and_leaves_base_unchanged(monkeypatch):
    network = FakeNetwork()
    analysis = ContingencyAnalysis.__new__(ContingencyAnalysis)
    analysis.network = network

    monkeypatch.setattr(
        "core.analysis.contingency.resolve_terminal_bus",
        lambda terminal: terminal.bus,
    )

    isolated = analysis._create_outage_case(("bus-1",))

    assert network.buses[0].in_service is True
    assert network.lines[0].in_service is True
    assert isolated.buses[0].in_service is False
    assert isolated.lines[0].in_service is False


def test_bus_outage_semantics_are_distinct_from_element_outage(monkeypatch):
    network = FakeNetwork()
    analysis = ContingencyAnalysis.__new__(ContingencyAnalysis)
    analysis.network = network

    monkeypatch.setattr(
        "core.analysis.contingency.resolve_terminal_bus",
        lambda terminal: terminal.bus,
    )

    isolated = analysis._create_outage_case(("line-1",))

    assert network.lines[0].in_service is True
    assert isolated.lines[0].in_service is False
    assert isolated.buses[0].in_service is True
