"""
GridForge V2 — Workspace Layout.

Pure logical layout representation.

No Qt dependencies.
No QWidget creation.
No MainWindow access.
No panel creation.
"""
# ui/workspace/workspace_layout.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Tuple

from .panel_area import PanelArea
from .workspace_definition import WorkspacePlacement


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    """
    Immutable logical arrangement of workspace content.
    """

    placements: Tuple[WorkspacePlacement, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not isinstance(self.placements, tuple):
            raise TypeError(
                "placements must be a tuple."
            )

        seen: set[str] = set()

        for placement in self.placements:
            if not isinstance(
                placement,
                WorkspacePlacement,
            ):
                raise TypeError(
                    "placements must contain "
                    "WorkspacePlacement objects."
                )

            if placement.panel_id in seen:
                raise ValueError(
                    f"Duplicate workspace placement: "
                    f"{placement.panel_id!r}"
                )

            seen.add(placement.panel_id)

    @classmethod
    def from_placements(
        cls,
        placements: Iterable[WorkspacePlacement],
    ) -> "WorkspaceLayout":
        """
        Create a layout from an iterable of placements.
        """

        return cls(
            placements=tuple(placements)
        )

    def get_area(
        self,
        panel_id: str,
    ) -> PanelArea | None:
        """
        Return the logical area assigned to a panel.
        """

        for placement in self.placements:
            if placement.panel_id == panel_id:
                return placement.area

        return None

    def get_placement(
        self,
        panel_id: str,
    ) -> WorkspacePlacement | None:
        """
        Return a panel's logical placement.
        """

        for placement in self.placements:
            if placement.panel_id == panel_id:
                return placement

        return None

    def panels_in_area(
        self,
        area: PanelArea,
    ) -> tuple[WorkspacePlacement, ...]:
        """
        Return placements belonging to one logical area.
        """

        return tuple(
            placement
            for placement in self.placements
            if placement.area == area
        )

    def visible_panels(
        self,
    ) -> tuple[WorkspacePlacement, ...]:
        """
        Return currently visible placements.
        """

        return tuple(
            placement
            for placement in self.placements
            if placement.visible
        )

    def with_placement(
        self,
        placement: WorkspacePlacement,
    ) -> "WorkspaceLayout":
        """
        Return a new layout with a placement inserted/replaced.
        """

        updated = [
            item
            for item in self.placements
            if item.panel_id != placement.panel_id
        ]

        updated.append(placement)

        return WorkspaceLayout(
            placements=tuple(updated)
        )

    def without_panel(
        self,
        panel_id: str,
    ) -> "WorkspaceLayout":
        """
        Return a new layout without the specified panel.
        """

        return WorkspaceLayout(
            placements=tuple(
                placement
                for placement in self.placements
                if placement.panel_id != panel_id
            )
        )


__all__ = [
    "WorkspaceLayout",
]
