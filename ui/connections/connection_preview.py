# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/connection_preview.py
#
# Purpose:
#     Stores temporary state while the user is interactively
#     creating an SLD connection.
#
# Architectural Role:
#     Keeps incomplete connection state outside LineTool and
#     outside QGraphicsScene.
#
# Responsibilities:
#     - store source terminal;
#     - store current target terminal;
#     - store pointer/cursor position;
#     - store validation state;
#     - provide preview lifecycle;
#     - provide commit-readiness diagnostics.
#
# Does NOT:
#     - create Connection objects;
#     - commit connections;
#     - render graphics;
#     - perform terminal resolution;
#     - perform topology validation;
#     - mutate Core;
#     - mutate the electrical network.
#
# ============================================================

"""
GridForge V2 — Connection Preview.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


Point = tuple[float, float]


@dataclass
class ConnectionPreview:
    """
    Temporary state for an in-progress SLD connection.

    This object is deliberately transient.

    It represents interaction state only and must never become
    the authoritative source of committed connection state.
    """

    active: bool = False

    source_terminal_id: Optional[str] = None

    target_terminal_id: Optional[str] = None

    cursor_position: Optional[Point] = None

    valid: bool = False

    validation_reason: str = ""

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def begin(
        self,
        source_terminal_id: str,
    ) -> None:
        """
        Begin a new connection-preview operation.

        Any previous preview state is replaced.

        Parameters
        ----------
        source_terminal_id:
            Logical ID of the source terminal.
        """

        source_terminal_id = (
            self._validate_terminal_id(
                source_terminal_id,
                "source_terminal_id",
            )
        )

        self.active = True

        self.source_terminal_id = (
            source_terminal_id
        )

        self.target_terminal_id = None

        self.cursor_position = None

        self.valid = False

        self.validation_reason = ""

    # --------------------------------------------------------

    def update_target(
        self,
        target_terminal_id: Optional[str],
        *,
        valid: bool,
        reason: str = "",
    ) -> None:
        """
        Update the current target and validation state.

        Parameters
        ----------
        target_terminal_id:
            Current logical target terminal, or None when the
            cursor is not currently over a terminal.

        valid:
            Whether the current candidate is structurally valid.

        reason:
            Validation diagnostic supplied by the validator.
        """

        self._ensure_active()

        if target_terminal_id is not None:
            target_terminal_id = (
                self._validate_terminal_id(
                    target_terminal_id,
                    "target_terminal_id",
                )
            )

        if not isinstance(
            valid,
            bool,
        ):
            raise TypeError(
                "valid must be a bool."
            )

        if not isinstance(
            reason,
            str,
        ):
            raise TypeError(
                "reason must be a string."
            )

        reason = reason.strip()

        # ----------------------------------------------------
        # A preview cannot be commit-valid without a target.
        # ----------------------------------------------------

        if valid and target_terminal_id is None:
            raise ValueError(
                "A valid preview requires "
                "target_terminal_id."
            )

        # ----------------------------------------------------
        # An invalid preview may optionally carry a diagnostic
        # reason.
        # ----------------------------------------------------

        self.target_terminal_id = (
            target_terminal_id
        )

        self.valid = valid

        self.validation_reason = reason

    # --------------------------------------------------------

    def update_cursor(
        self,
        position: Point,
    ) -> None:
        """
        Update the current cursor position.

        Parameters
        ----------
        position:
            Two-dimensional canvas/view position.

        Notes
        -----
        The preview stores plain numeric coordinates and does
        not retain Qt QPoint/QPointF objects.
        """

        self._ensure_active()

        self.cursor_position = (
            self._validate_point(
                position
            )
        )

    # --------------------------------------------------------

    def cancel(
        self,
    ) -> None:
        """
        Cancel the current connection-preview operation.
        """

        self.reset()

    # --------------------------------------------------------

    def reset(
        self,
    ) -> None:
        """
        Clear all transient preview state.
        """

        self.active = False

        self.source_terminal_id = None

        self.target_terminal_id = None

        self.cursor_position = None

        self.valid = False

        self.validation_reason = ""

    # ========================================================
    # STATE
    # ========================================================

    @property
    def can_commit(
        self,
    ) -> bool:
        """
        Return True when the preview represents a valid complete
        connection candidate.
        """

        return (
            self.active
            and self.valid
            and self.source_terminal_id is not None
            and self.target_terminal_id is not None
        )

    # --------------------------------------------------------

    @property
    def has_source(
        self,
    ) -> bool:
        """
        Return True when a source terminal is selected.
        """

        return (
            self.source_terminal_id is not None
        )

    # --------------------------------------------------------

    @property
    def has_target(
        self,
    ) -> bool:
        """
        Return True when a target terminal is currently selected.
        """

        return (
            self.target_terminal_id is not None
        )

    # --------------------------------------------------------

    @property
    def has_cursor_position(
        self,
    ) -> bool:
        """
        Return True when a cursor position is available.
        """

        return (
            self.cursor_position is not None
        )

    # --------------------------------------------------------

    def get_endpoint_ids(
        self,
    ) -> Optional[tuple[str, str]]:
        """
        Return the current source/target pair when complete.

        Returns
        -------
        tuple[str, str] | None
            Endpoint pair when both terminals exist.
        """

        if (
            self.source_terminal_id is None
            or self.target_terminal_id is None
        ):
            return None

        return (
            self.source_terminal_id,
            self.target_terminal_id,
        )

    # --------------------------------------------------------

    def get_state(
        self,
    ) -> dict[str, object]:
        """
        Return a diagnostic snapshot of preview state.

        The returned dictionary is independent of the preview's
        internal mutable state.
        """

        return {
            "active": self.active,
            "source_terminal_id": (
                self.source_terminal_id
            ),
            "target_terminal_id": (
                self.target_terminal_id
            ),
            "cursor_position": (
                self.cursor_position
            ),
            "valid": self.valid,
            "validation_reason": (
                self.validation_reason
            ),
            "can_commit": self.can_commit,
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_terminal_id(
        terminal_id: str,
        name: str,
    ) -> str:
        """
        Validate a logical terminal identifier.
        """

        if not isinstance(
            terminal_id,
            str,
        ):
            raise TypeError(
                f"{name} must be a string."
            )

        if not terminal_id.strip():
            raise ValueError(
                f"{name} must not be empty."
            )

        return terminal_id

    # --------------------------------------------------------

    @staticmethod
    def _validate_point(
        position: Point,
    ) -> Point:
        """
        Validate and normalize a two-dimensional point.
        """

        if position is None:
            raise ValueError(
                "position must not be None."
            )

        if (
            isinstance(position, (str, bytes))
            or not hasattr(position, "__len__")
        ):
            raise TypeError(
                "position must contain two coordinates."
            )

        try:
            if len(position) != 2:
                raise ValueError(
                    "position must contain exactly "
                    "two coordinates."
                )

            x = position[0]
            y = position[1]

        except (TypeError, IndexError) as exc:
            raise TypeError(
                "position must contain two coordinates."
            ) from exc

        if isinstance(x, bool) or not isinstance(
            x,
            (int, float),
        ):
            raise TypeError(
                "position.x must be numeric."
            )

        if isinstance(y, bool) or not isinstance(
            y,
            (int, float),
        ):
            raise TypeError(
                "position.y must be numeric."
            )

        return (
            float(x),
            float(y),
        )

    # --------------------------------------------------------

    def _ensure_active(
        self,
    ) -> None:
        """
        Reject state updates when no preview is active.
        """

        if not self.active:
            raise RuntimeError(
                "Connection preview is not active."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "ConnectionPreview("
            f"active={self.active}, "
            f"source={self.source_terminal_id!r}, "
            f"target={self.target_terminal_id!r}, "
            f"valid={self.valid}, "
            f"can_commit={self.can_commit}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ConnectionPreview",
    "Point",
]
