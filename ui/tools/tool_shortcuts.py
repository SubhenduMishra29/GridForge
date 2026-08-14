# ============================================================
# File: ui/tools/tool_shortcuts.py
# GridForge V2 — Tool Shortcuts
# ============================================================
"""
Keyboard shortcut definitions for GridForge V2 UI tools.

This module defines the semantic shortcut contract for the frozen
tool set. It does not create QAction/QShortcut objects and does
not depend on Qt.

Frozen concrete tools
------------------------
    SelectTool
    BusTool
    LineTool

Shortcut ownership
------------------
Tool shortcuts express tool-selection intent.

Actual Qt shortcut registration belongs to the UI composition
layer/controller layer. ToolManager remains the authority for
activating the selected tool.

No shortcut handler in this module mutates Core.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class ToolShortcutAction(str, Enum):
    """
    Semantic actions produced by tool shortcuts.
    """

    SELECT_TOOL = "select_tool"
    BUS_TOOL = "bus_tool"
    LINE_TOOL = "line_tool"


@dataclass(frozen=True, slots=True)
class ToolShortcut:
    """
    Immutable semantic keyboard shortcut definition.

    Parameters
    ----------
    sequence:
        Normalized shortcut sequence, e.g. ``"S"``.

    action:
        Semantic action represented by the shortcut.

    tool_id:
        Stable tool identifier.

    description:
        Human-readable description.
    """

    sequence: str
    action: ToolShortcutAction
    tool_id: str
    description: str

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the shortcut definition.
        """

        if not isinstance(
            self.sequence,
            str,
        ) or not self.sequence.strip():
            raise ValueError(
                "sequence must be a non-empty string."
            )

        if not isinstance(
            self.action,
            ToolShortcutAction,
        ):
            raise TypeError(
                "action must be a ToolShortcutAction."
            )

        if not isinstance(
            self.tool_id,
            str,
        ) or not self.tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        if not isinstance(
            self.description,
            str,
        ) or not self.description.strip():
            raise ValueError(
                "description must be a non-empty string."
            )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, str]:
        """
        Return a serializable diagnostic representation.
        """

        return {
            "sequence": self.sequence,
            "action": self.action.value,
            "tool_id": self.tool_id,
            "description": self.description,
        }


class ToolShortcutRegistry:
    """
    Registry of the frozen GridForge tool shortcuts.

    Shortcut definitions are explicit and deterministic.

    This class does not interact with Qt's shortcut system.
    """

    SELECT_TOOL_ID = "select"
    BUS_TOOL_ID = "bus"
    LINE_TOOL_ID = "line"

    # --------------------------------------------------------
    # Frozen default shortcuts
    # --------------------------------------------------------

    SELECT_SHORTCUT = "S"
    BUS_SHORTCUT = "B"
    LINE_SHORTCUT = "L"

    def __init__(
        self,
        shortcuts: Optional[
            Iterable[ToolShortcut]
        ] = None,
    ) -> None:
        """
        Initialize the shortcut registry.

        When no custom iterable is supplied, the frozen default
        shortcut set is installed.
        """

        self._shortcuts: dict[
            str,
            ToolShortcut,
        ] = {}

        if shortcuts is None:
            shortcuts = self._default_shortcuts()

        for shortcut in shortcuts:
            self.register(
                shortcut
            )

    # ========================================================
    # DEFAULTS
    # ========================================================

    @classmethod
    def _default_shortcuts(
        cls,
    ) -> tuple[ToolShortcut, ...]:
        """
        Return the frozen default tool shortcut definitions.
        """

        return (
            ToolShortcut(
                sequence=cls.SELECT_SHORTCUT,
                action=ToolShortcutAction.SELECT_TOOL,
                tool_id=cls.SELECT_TOOL_ID,
                description="Activate Select Tool",
            ),
            ToolShortcut(
                sequence=cls.BUS_SHORTCUT,
                action=ToolShortcutAction.BUS_TOOL,
                tool_id=cls.BUS_TOOL_ID,
                description="Activate Bus Tool",
            ),
            ToolShortcut(
                sequence=cls.LINE_SHORTCUT,
                action=ToolShortcutAction.LINE_TOOL,
                tool_id=cls.LINE_TOOL_ID,
                description="Activate Line Tool",
            ),
        )

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        shortcut: ToolShortcut,
    ) -> None:
        """
        Register a shortcut definition.

        Shortcut sequences must be unique.
        """

        if not isinstance(
            shortcut,
            ToolShortcut,
        ):
            raise TypeError(
                "shortcut must be a ToolShortcut."
            )

        sequence = self.normalize(
            shortcut.sequence
        )

        if sequence in self._shortcuts:
            raise ValueError(
                f"Shortcut {sequence!r} is already registered."
            )

        self._shortcuts[
            sequence
        ] = ToolShortcut(
            sequence=sequence,
            action=shortcut.action,
            tool_id=shortcut.tool_id,
            description=shortcut.description,
        )

    # --------------------------------------------------------

    def unregister(
        self,
        sequence: str,
    ) -> ToolShortcut:
        """
        Remove and return a shortcut definition.
        """

        key = self.normalize(
            sequence
        )

        try:
            return self._shortcuts.pop(
                key
            )
        except KeyError as exc:
            raise KeyError(
                f"Shortcut {key!r} is not registered."
            ) from exc

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        sequence: str,
    ) -> ToolShortcut:
        """
        Return the shortcut associated with a sequence.
        """

        key = self.normalize(
            sequence
        )

        try:
            return self._shortcuts[
                key
            ]
        except KeyError as exc:
            raise KeyError(
                f"Shortcut {key!r} is not registered."
            ) from exc

    # --------------------------------------------------------

    def get_optional(
        self,
        sequence: str,
    ) -> Optional[ToolShortcut]:
        """
        Return a shortcut or None.
        """

        return self._shortcuts.get(
            self.normalize(sequence)
        )

    # --------------------------------------------------------

    def has(
        self,
        sequence: str,
    ) -> bool:
        """
        Return whether a shortcut is registered.
        """

        return (
            self.normalize(sequence)
            in self._shortcuts
        )

    # ========================================================
    # TOOL LOOKUP
    # ========================================================

    def for_tool(
        self,
        tool_id: str,
    ) -> Optional[ToolShortcut]:
        """
        Return the shortcut assigned to a tool.

        Returns None when no shortcut is registered.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        for shortcut in self._shortcuts.values():
            if shortcut.tool_id == tool_id:
                return shortcut

        return None

    # --------------------------------------------------------

    def sequence_for_tool(
        self,
        tool_id: str,
    ) -> Optional[str]:
        """
        Return the normalized shortcut sequence for a tool.
        """

        shortcut = self.for_tool(
            tool_id
        )

        if shortcut is None:
            return None

        return shortcut.sequence

    # ========================================================
    # ITERATION
    # ========================================================

    def shortcuts(
        self,
    ) -> tuple[ToolShortcut, ...]:
        """
        Return all shortcuts in deterministic insertion order.
        """

        return tuple(
            self._shortcuts.values()
        )

    # --------------------------------------------------------

    def sequences(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered shortcut sequences.
        """

        return tuple(
            self._shortcuts.keys()
        )

    # --------------------------------------------------------

    def __iter__(
        self,
    ):
        """
        Iterate over registered shortcut definitions.
        """

        return iter(
            self.shortcuts()
        )

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered shortcuts.
        """

        return len(
            self._shortcuts
        )

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def normalize(
        sequence: str,
    ) -> str:
        """
        Normalize a shortcut sequence.

        Normalization currently:

            - strips surrounding whitespace;
            - converts to uppercase.

        Qt-specific key-sequence parsing is intentionally outside
        this module.
        """

        if not isinstance(
            sequence,
            str,
        ):
            raise TypeError(
                "Shortcut sequence must be a string."
            )

        normalized = sequence.strip().upper()

        if not normalized:
            raise ValueError(
                "Shortcut sequence must not be empty."
            )

        return normalized

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_unique(
        self,
    ) -> None:
        """
        Validate that no duplicate normalized sequences exist.

        Duplicate sequences are prevented during registration;
        this method exists as an explicit architectural assertion.
        """

        sequences = [
            shortcut.sequence
            for shortcut in self._shortcuts.values()
        ]

        if len(sequences) != len(
            set(sequences)
        ):
            raise RuntimeError(
                "Tool shortcut registry contains duplicate "
                "shortcut sequences."
            )

    # --------------------------------------------------------

    def validate_frozen_tool_set(
        self,
    ) -> None:
        """
        Validate that the default three tools have shortcuts.

        This prevents accidental omission of a concrete tool from
        the standard shortcut surface.
        """

        required = {
            self.SELECT_TOOL_ID,
            self.BUS_TOOL_ID,
            self.LINE_TOOL_ID,
        }

        registered = {
            shortcut.tool_id
            for shortcut in self._shortcuts.values()
        }

        missing = required - registered

        if missing:
            raise RuntimeError(
                "Tool shortcut registry is incomplete. "
                f"Missing tool shortcuts: "
                f"{tuple(sorted(missing))!r}."
            )

    # ========================================================
    # ACTION RESOLUTION
    # ========================================================

    def action_for(
        self,
        sequence: str,
    ) -> Optional[ToolShortcutAction]:
        """
        Return the semantic action for a shortcut.
        """

        shortcut = self.get_optional(
            sequence
        )

        if shortcut is None:
            return None

        return shortcut.action

    # --------------------------------------------------------

    def tool_id_for(
        self,
        sequence: str,
    ) -> Optional[str]:
        """
        Return the tool ID associated with a shortcut.
        """

        shortcut = self.get_optional(
            sequence
        )

        if shortcut is None:
            return None

        return shortcut.tool_id

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, object]:
        """
        Return a deterministic diagnostic snapshot.
        """

        return {
            "count": len(
                self._shortcuts
            ),
            "sequences": self.sequences(),
            "tools": tuple(
                shortcut.tool_id
                for shortcut in self.shortcuts()
            ),
        }

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            f"{type(self).__name__}("
            f"shortcuts={self.sequences()!r}"
            ")"
        )


__all__ = [
    "ToolShortcutAction",
    "ToolShortcut",
    "ToolShortcutRegistry",
]
