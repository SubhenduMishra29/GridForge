# ============================================================
# GridForge V2
# ============================================================
# File:
#     tests/ui/connections/test_terminal_resolver.py
#
# Purpose:
#     Unit tests for ui.connections.terminal_resolver.
#
# ============================================================

from __future__ import annotations

import pytest

import ui.connections.terminal_resolver as resolver_module
from ui.connections.terminal_resolver import TerminalResolver


# ============================================================
# TEST DOUBLE
# ============================================================


class FakeEquipmentTerminal:
    """
    Minimal logical terminal test double.

    The production resolver requires EquipmentTerminal.
    The resolver module's imported class is replaced with this
    test type so the resolver can be tested independently of
    EquipmentTerminal construction details.
    """

    def __init__(
        self,
        terminal_id: str,
        equipment_id: str,
    ) -> None:
        self.terminal_id = terminal_id
        self.equipment_id = equipment_id


@pytest.fixture
def terminal_type(monkeypatch):
    """
    Replace the resolver's imported EquipmentTerminal class
    with the deterministic test double.
    """

    monkeypatch.setattr(
        resolver_module,
        "EquipmentTerminal",
        FakeEquipmentTerminal,
    )

    return FakeEquipmentTerminal


@pytest.fixture
def terminals(terminal_type):
    """
    Return a deterministic collection of test terminals.
    """

    return (
        terminal_type("T1", "E1"),
        terminal_type("T2", "E1"),
        terminal_type("T3", "E2"),
    )


# ============================================================
# INITIALIZATION
# ============================================================


def test_initial_state():
    resolver = TerminalResolver()

    assert len(resolver) == 0
    assert resolver.terminals() == ()
    assert resolver.terminal_ids() == ()
    assert repr(resolver) == "TerminalResolver(count=0)"


# ============================================================
# REGISTRATION
# ============================================================


def test_register_terminal(terminal_type):
    resolver = TerminalResolver()
    terminal = terminal_type("T1", "E1")

    resolver.register(terminal)

    assert len(resolver) == 1
    assert resolver.get("T1") is terminal
    assert resolver.require("T1") is terminal
    assert resolver.contains("T1")
    assert "T1" in resolver


def test_register_preserves_terminal_object_identity(
    terminal_type,
):
    resolver = TerminalResolver()
    terminal = terminal_type("T1", "E1")

    resolver.register(terminal)

    assert resolver.get("T1") is terminal


def test_duplicate_terminal_registration_is_rejected(
    terminal_type,
):
    resolver = TerminalResolver()

    first = terminal_type("T1", "E1")
    second = terminal_type("T1", "E2")

    resolver.register(first)

    with pytest.raises(
        ValueError,
        match="Terminal already registered: T1",
    ):
        resolver.register(second)

    assert resolver.get("T1") is first
    assert len(resolver) == 1


def test_register_rejects_wrong_type():
    resolver = TerminalResolver()

    with pytest.raises(
        TypeError,
        match="terminal must be an EquipmentTerminal",
    ):
        resolver.register(object())


def test_register_rejects_empty_terminal_id(
    terminal_type,
):
    resolver = TerminalResolver()
    terminal = terminal_type("", "E1")

    with pytest.raises(
        ValueError,
        match="terminal.terminal_id must not be empty",
    ):
        resolver.register(terminal)


def test_register_rejects_whitespace_terminal_id(
    terminal_type,
):
    resolver = TerminalResolver()
    terminal = terminal_type("   ", "E1")

    with pytest.raises(
        ValueError,
        match="terminal.terminal_id must not be empty",
    ):
        resolver.register(terminal)


def test_register_rejects_empty_equipment_id(
    terminal_type,
):
    resolver = TerminalResolver()
    terminal = terminal_type("T1", "")

    with pytest.raises(
        ValueError,
        match="terminal.equipment_id must not be empty",
    ):
        resolver.register(terminal)


def test_register_normalizes_identifier_whitespace(
    terminal_type,
):
    resolver = TerminalResolver()

    terminal = terminal_type(
        "  T1  ",
        "E1",
    )

    resolver.register(terminal)

    assert resolver.contains("T1")
    assert resolver.get("T1") is terminal
    assert resolver.terminal_ids() == ("T1",)


# ============================================================
# LOOKUP
# ============================================================


def test_get_returns_none_for_unknown_terminal(
    terminal_type,
):
    resolver = TerminalResolver()
    resolver.register(
        terminal_type("T1", "E1")
    )

    assert resolver.get("UNKNOWN") is None


def test_require_returns_registered_terminal(
    terminal_type,
):
    resolver = TerminalResolver()
    terminal = terminal_type("T1", "E1")

    resolver.register(terminal)

    assert resolver.require("T1") is terminal


def test_require_raises_for_unknown_terminal():
    resolver = TerminalResolver()

    with pytest.raises(
        KeyError,
        match="Unknown terminal: UNKNOWN",
    ):
        resolver.require("UNKNOWN")


def test_contains_returns_correct_state(
    terminal_type,
):
    resolver = TerminalResolver()

    assert not resolver.contains("T1")

    resolver.register(
        terminal_type("T1", "E1")
    )

    assert resolver.contains("T1")
    assert not resolver.contains("T2")


def test_contains_operator_matches_contains(
    terminal_type,
):
    resolver = TerminalResolver()

    resolver.register(
        terminal_type("T1", "E1")
    )

    assert "T1" in resolver
    assert "T2" not in resolver
    assert 123 not in resolver
    assert "" not in resolver


# ============================================================
# UNREGISTER
# ============================================================


def test_unregister_returns_removed_terminal(
    terminal_type,
):
    resolver = TerminalResolver()
    terminal = terminal_type("T1", "E1")

    resolver.register(terminal)

    removed = resolver.unregister("T1")

    assert removed is terminal
    assert len(resolver) == 0
    assert resolver.get("T1") is None
    assert not resolver.contains("T1")


def test_unregister_unknown_terminal_raises():
    resolver = TerminalResolver()

    with pytest.raises(
        KeyError,
        match="UNKNOWN",
    ):
        resolver.unregister("UNKNOWN")


def test_unregister_does_not_destroy_terminal(
    terminal_type,
):
    resolver = TerminalResolver()
    terminal = terminal_type("T1", "E1")

    resolver.register(terminal)

    removed = resolver.unregister("T1")

    assert removed is terminal
    assert terminal.terminal_id == "T1"
    assert terminal.equipment_id == "E1"


# ============================================================
# TERMINAL ENUMERATION
# ============================================================


def test_terminals_returns_registration_order(
    terminals,
):
    resolver = TerminalResolver()

    for terminal in terminals:
        resolver.register(terminal)

    result = resolver.terminals()

    assert result == terminals
    assert isinstance(result, tuple)


def test_terminal_ids_returns_registration_order(
    terminals,
):
    resolver = TerminalResolver()

    for terminal in terminals:
        resolver.register(terminal)

    assert resolver.terminal_ids() == (
        "T1",
        "T2",
        "T3",
    )


def test_terminal_enumeration_is_snapshot(
    terminal_type,
):
    resolver = TerminalResolver()

    first = terminal_type("T1", "E1")
    second = terminal_type("T2", "E1")

    resolver.register(first)

    snapshot = resolver.terminals()

    resolver.register(second)

    assert snapshot == (first,)
    assert resolver.terminals() == (
        first,
        second,
    )


# ============================================================
# EQUIPMENT OWNERSHIP
# ============================================================


def test_get_equipment_id_returns_owner(
    terminal_type,
):
    resolver = TerminalResolver()

    terminal = terminal_type(
        "T1",
        "E1",
    )

    resolver.register(terminal)

    assert resolver.get_equipment_id("T1") == "E1"


def test_get_equipment_id_returns_none_for_unknown(
    terminal_type,
):
    resolver = TerminalResolver()

    resolver.register(
        terminal_type("T1", "E1")
    )

    assert resolver.get_equipment_id("UNKNOWN") is None


def test_require_equipment_id_returns_owner(
    terminal_type,
):
    resolver = TerminalResolver()

    resolver.register(
        terminal_type("T1", "E1")
    )

    assert resolver.require_equipment_id("T1") == "E1"


def test_require_equipment_id_raises_for_unknown():
    resolver = TerminalResolver()

    with pytest.raises(
        KeyError,
        match="Unknown terminal: T1",
    ):
        resolver.require_equipment_id("T1")


def test_terminals_for_equipment(
    terminals,
):
    resolver = TerminalResolver()

    for terminal in terminals:
        resolver.register(terminal)

    result = resolver.terminals_for_equipment("E1")

    assert result == (
        terminals[0],
        terminals[1],
    )


def test_terminals_for_equipment_returns_empty_for_unknown(
    terminals,
):
    resolver = TerminalResolver()

    for terminal in terminals:
        resolver.register(terminal)

    assert resolver.terminals_for_equipment(
        "UNKNOWN"
    ) == ()


def test_has_equipment(
    terminals,
):
    resolver = TerminalResolver()

    for terminal in terminals:
        resolver.register(terminal)

    assert resolver.has_equipment("E1")
    assert resolver.has_equipment("E2")
    assert not resolver.has_equipment("E3")


# ============================================================
# CLEAR
# ============================================================


def test_clear_removes_all_registered_terminals(
    terminals,
):
    resolver = TerminalResolver()

    for terminal in terminals:
        resolver.register(terminal)

    assert len(resolver) == 3

    resolver.clear()

    assert len(resolver) == 0
    assert resolver.terminals() == ()
    assert resolver.terminal_ids() == ()


def test_clear_is_idempotent():
    resolver = TerminalResolver()

    resolver.clear()
    resolver.clear()

    assert len(resolver) == 0


# ============================================================
# IDENTIFIER VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        1.0,
        True,
        False,
        [],
        {},
    ],
)
def test_get_rejects_invalid_terminal_id(
    value,
):
    resolver = TerminalResolver()

    with pytest.raises(TypeError):
        resolver.get(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "   ",
    ],
)
def test_get_rejects_empty_terminal_id(
    value,
):
    resolver = TerminalResolver()

    with pytest.raises(
        (TypeError, ValueError)
    ):
        resolver.get(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        1.0,
        True,
        False,
        [],
        {},
    ],
)
def test_unregister_rejects_invalid_terminal_id(
    value,
):
    resolver = TerminalResolver()

    with pytest.raises(TypeError):
        resolver.unregister(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        1.0,
        True,
        False,
        [],
        {},
    ],
)
def test_contains_rejects_no_error_for_invalid_type(
    value,
):
    resolver = TerminalResolver()

    assert not resolver.__contains__(value)


# ============================================================
# EQUIPMENT ID VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "equipment_id",
    [
        None,
        1,
        1.0,
        True,
        False,
        [],
        {},
    ],
)
def test_terminals_for_equipment_rejects_invalid_id(
    equipment_id,
):
    resolver = TerminalResolver()

    with pytest.raises(TypeError):
        resolver.terminals_for_equipment(
            equipment_id
        )


@pytest.mark.parametrize(
    "equipment_id",
    [
        "",
        "   ",
    ],
)
def test_terminals_for_equipment_rejects_empty_id(
    equipment_id,
):
    resolver = TerminalResolver()

    with pytest.raises(
        ValueError,
        match="equipment_id must not be empty",
    ):
        resolver.terminals_for_equipment(
            equipment_id
        )


# ============================================================
# EXTERNAL OWNERSHIP
# ============================================================


def test_resolver_does_not_copy_terminal(
    terminal_type,
):
    resolver = TerminalResolver()

    terminal = terminal_type(
        "T1",
        "E1",
    )

    resolver.register(terminal)

    assert resolver.get("T1") is terminal


def test_clear_only_removes_registry_reference(
    terminal_type,
):
    resolver = TerminalResolver()

    terminal = terminal_type(
        "T1",
        "E1",
    )

    resolver.register(terminal)
    resolver.clear()

    assert terminal.terminal_id == "T1"
    assert terminal.equipment_id == "E1"


# ============================================================
# REPRESENTATION
# ============================================================


def test_repr_empty():
    resolver = TerminalResolver()

    assert repr(resolver) == (
        "TerminalResolver(count=0)"
    )


def test_repr_reports_count(
    terminals,
):
    resolver = TerminalResolver()

    for terminal in terminals:
        resolver.register(terminal)

    assert repr(resolver) == (
        "TerminalResolver(count=3)"
    )
