"""
GridForge V2 - Logic Contacts
==============================

Author:
    Subhendu Mishra

File:
    core/control/logic/contacts.py

Purpose
-------
Headless industrial contact elements for the Logic Control domain.

Supported contact types:

    - Normally Open (NO)
    - Normally Closed (NC)

A contact is a discrete logic element. Its graphical symbol, placement,
wiring appearance, and editing behavior belong to the UI logic-layout
canvas and are deliberately absent from this module.

Domain semantics
----------------
NO:
    OUT = IN

NC:
    OUT = NOT IN

The contact itself is stateless and deterministic.
"""

from __future__ import annotations

from enum import Enum
from typing import Sequence

from ..base import (
    LogicControlComponent,
    LogicControlResult,
)
from ...base import (
    ControlSignal,
    Inputs,
    SignalRole,
    State,
)


class ContactType(str, Enum):
    """Electrical/control-logic contact state."""

    NORMALLY_OPEN = "normally_open"
    NORMALLY_CLOSED = "normally_closed"


class LogicContact(LogicControlComponent):
    """
    Base headless contact implementation.

    A LogicContact provides one Boolean input and one Boolean output.
    The output behavior is determined by ``contact_type``.
    """

    def __init__(
        self,
        component_id: str,
        contact_type: ContactType,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicContact component_id cannot be empty."
            )

        if not isinstance(
            contact_type,
            ContactType,
        ):
            try:
                contact_type = ContactType(
                    contact_type
                )
            except ValueError as exc:
                raise ValueError(
                    f"Invalid contact type: "
                    f"{contact_type!r}."
                ) from exc

        self._component_id = component_id
        self._contact_type = contact_type

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return (
            "normally_open_contact"
            if self._contact_type
            is ContactType.NORMALLY_OPEN
            else "normally_closed_contact"
        )

    @property
    def contact_type(self) -> ContactType:
        return self._contact_type

    @property
    def is_normally_open(self) -> bool:
        return (
            self._contact_type
            is ContactType.NORMALLY_OPEN
        )

    @property
    def is_normally_closed(self) -> bool:
        return (
            self._contact_type
            is ContactType.NORMALLY_CLOSED
        )

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="IN",
                role=SignalRole.INPUT,
                description="Boolean contact command/state.",
                value_type=bool,
            ),
        )

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="OUT",
                role=SignalRole.OUTPUT,
                description="Boolean contact output.",
                value_type=bool,
            ),
        )

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized = self.validate_logic_inputs(
            inputs
        )

        input_value = normalized["IN"]

        if self._contact_type is ContactType.NORMALLY_OPEN:
            output = input_value
        else:
            output = not input_value

        return LogicControlResult(
            outputs={
                "OUT": output,
            },
            state={},
            time=time,
        )


class NormallyOpenContact(LogicContact):
    """
    Normally Open (NO) contact.

    The contact conducts when its Boolean input is True.

        OUT = IN
    """

    def __init__(
        self,
        component_id: str,
    ) -> None:
        super().__init__(
            component_id=component_id,
            contact_type=ContactType.NORMALLY_OPEN,
        )


class NormallyClosedContact(LogicContact):
    """
    Normally Closed (NC) contact.

    The contact conducts when its Boolean input is False.

        OUT = NOT IN
    """

    def __init__(
        self,
        component_id: str,
    ) -> None:
        super().__init__(
            component_id=component_id,
            contact_type=ContactType.NORMALLY_CLOSED,
        )


# Convenient aliases for engineering/control terminology.
NOContact = NormallyOpenContact
NCContact = NormallyClosedContact


__all__ = [
    "ContactType",
    "LogicContact",
    "NormallyOpenContact",
    "NormallyClosedContact",
    "NOContact",
    "NCContact",
]
