# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_instance.py
#
# Purpose:
#     Represents a runtime instance of a registered panel.
#
# Architectural Role:
#     Couples a PanelBase implementation with runtime lifecycle
#     state without coupling the panel to Qt docking.
#
# Responsibilities:
#     - panel object;
#     - creation;
#     - visibility lifecycle;
#     - activation lifecycle;
#     - destruction lifecycle.
#
# Does NOT:
#     - decide workspace placement;
#     - own dock area;
#     - own floating state;
#     - create QDockWidget;
#     - directly alter MainWindow.
#
# Workspace placement is owned by WorkspaceLayout.
#
# ============================================================

"""
GridForge V2 — Panel Instance.
"""

from __future__ import annotations

from .panel_base import PanelBase
from .panel_descriptor import PanelDescriptor
from .panel_state import PanelState


class PanelInstance:
    """
    Runtime instance of a registered panel.

    PanelInstance owns lifecycle state only.

    Workspace placement is deliberately outside this class.
    """

    def __init__(
        self,
        descriptor: PanelDescriptor,
        panel: PanelBase,
    ) -> None:
        if descriptor is None:
            raise ValueError(
                "descriptor must not be None"
            )

        if not isinstance(
            descriptor,
            PanelDescriptor,
        ):
            raise TypeError(
                "descriptor must be a PanelDescriptor"
            )

        if panel is None:
            raise ValueError(
                "panel must not be None"
            )

        if not isinstance(
            panel,
            PanelBase,
        ):
            raise TypeError(
                "panel must be a PanelBase"
            )

        if panel.panel_id != descriptor.panel_id:
            raise ValueError(
                "Panel ID does not match descriptor"
            )

        self._descriptor = descriptor
        self._panel = panel

        self._state = PanelState(
            visible=descriptor.visible_by_default,
        )

        self._created = False
        self._destroyed = False

    # ========================================================
    # Properties
    # ========================================================

    @property
    def descriptor(self) -> PanelDescriptor:
        """Return the immutable panel descriptor."""
        return self._descriptor

    # --------------------------------------------------------

    @property
    def panel(self) -> PanelBase:
        """Return the underlying logical panel."""
        return self._panel

    # --------------------------------------------------------

    @property
    def state(self) -> PanelState:
        """
        Return runtime lifecycle state.

        Workspace placement is intentionally not represented here.
        """
        return self._state

    # --------------------------------------------------------

    @property
    def created(self) -> bool:
        """Return whether the panel has been created."""
        return self._created

    # --------------------------------------------------------

    @property
    def destroyed(self) -> bool:
        """Return whether the panel has been destroyed."""
        return self._destroyed

    # ========================================================
    # Lifecycle
    # ========================================================

    def create(self) -> None:
        """
        Create the logical panel lifecycle state.

        Actual Qt widget creation belongs to the composition layer.
        """

        if self._destroyed:
            raise RuntimeError(
                "Cannot create a destroyed panel"
            )

        if self._created:
            return

        self._panel.on_create()
        self._created = True

        if self._state.visible:
            self._panel.on_show()

    # --------------------------------------------------------

    def show(self) -> None:
        """
        Show the panel at the lifecycle level.

        Workspace/MainWindow remains responsible for actual
        workspace/dock placement.
        """

        self.create()

        if not self._state.visible:
            self._state.show()
            self._panel.on_show()

    # --------------------------------------------------------

    def hide(self) -> None:
        """
        Hide the panel at the lifecycle level.
        """

        if not self._created:
            return

        if self._state.visible:
            self._state.hide()
            self._panel.on_hide()

    # --------------------------------------------------------

    def activate(self) -> None:
        """
        Activate the panel logically.
        """

        self.create()

        self._state.activate()
        self._panel.on_activate()

    # --------------------------------------------------------

    def deactivate(self) -> None:
        """
        Deactivate the panel logically.
        """

        if not self._created:
            return

        if self._state.active:
            self._state.deactivate()
            self._panel.on_deactivate()

    # --------------------------------------------------------

    def reset(self) -> None:
        """
        Reset panel content/state through its panel contract.
        """

        self._panel.reset()

    # --------------------------------------------------------

    def destroy(self) -> None:
        """
        Destroy the logical panel lifecycle.

        Ownership of any Qt widget remains outside this class.
        """

        if self._destroyed:
            return

        if self._created:
            self._panel.on_destroy()

        self._created = False
        self._destroyed = True
