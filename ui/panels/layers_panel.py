# ============================================================
# File: ui/panels/layers_panel.py
# GridForge V2 — Layers Panel
# ============================================================

"""
GridForge V2 — Layers Panel
===========================

Presentation panel for canvas/display layer state.

Responsibilities
----------------
LayersPanel:

    - display the available UI/canvas layers;
    - display layer visibility state;
    - allow the presentation layer to receive layer-state
      updates;
    - expose the currently displayed layer information;
    - provide diagnostic state.

LayersPanel does NOT:

    - own the renderer;
    - own RenderSystem;
    - modify Core model state;
    - perform rendering;
    - create QGraphicsItems;
    - determine electrical topology;
    - manage tools;
    - manage canvas interaction;
    - own authoritative layer state.

Architecture
------------

    Layer / Canvas State Owner
                │
                ▼
          LayersPanel
                │
                ▼
          Display / UI

The authoritative layer state belongs to the appropriate UI
rendering/canvas subsystem. LayersPanel is only a presentation
and user-interaction surface.

Layer Model
-----------

A layer is represented by:

    {
        "id": <stable layer identifier>,
        "name": <display name>,
        "visible": <bool>
    }

Additional layer metadata may be introduced later without
making LayersPanel the owner of that state.

Qt Rule
-------
All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ui.core.qt import (
    QCheckBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class LayersPanel(QWidget):
    """
    Presentation widget for canvas/display layers.

    The panel maintains only a UI snapshot of the supplied layer
    information. It does not become the authoritative owner of
    rendering or layer state.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the LayersPanel.

        Parameters
        ----------
        parent:
            Optional Qt parent widget.
        """

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # Presentation snapshot.
        #
        # layer_id -> layer metadata
        # ----------------------------------------------------

        self._layers: dict[
            str,
            dict[str, Any],
        ] = {}

        # ----------------------------------------------------
        # Header.
        # ----------------------------------------------------

        self._title = QLabel(
            "Layers",
            self,
        )

        # ----------------------------------------------------
        # Layer list.
        # ----------------------------------------------------

        self._list = QListWidget(
            self
        )

        # ----------------------------------------------------
        # Layout.
        # ----------------------------------------------------

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            self._title
        )

        layout.addWidget(
            self._list
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_layer_id(
        layer_id: str,
    ) -> str:
        """
        Validate and normalize a layer identifier.
        """

        if not isinstance(
            layer_id,
            str,
        ):
            raise TypeError(
                "layer_id must be a string."
            )

        layer_id = layer_id.strip()

        if not layer_id:
            raise ValueError(
                "layer_id must be a non-empty string."
            )

        return layer_id

    # ========================================================
    # LAYER DATA
    # ========================================================

    def set_layers(
        self,
        layers: Iterable[Mapping[str, Any]],
    ) -> None:
        """
        Replace the displayed layer list.

        Parameters
        ----------
        layers:
            Iterable of mappings containing at least:

                id
                name
                visible

        Notes
        -----
        The supplied data is copied into a presentation snapshot.
        The original layer objects are not retained.
        """

        if layers is None:
            raise ValueError(
                "layers must not be None."
            )

        new_layers: dict[
            str,
            dict[str, Any],
        ] = {}

        for layer in layers:

            if not isinstance(
                layer,
                Mapping,
            ):
                raise TypeError(
                    "Each layer must be a mapping."
                )

            if "id" not in layer:
                raise ValueError(
                    "Each layer must provide an 'id'."
                )

            layer_id = self._validate_layer_id(
                layer["id"]
            )

            name = layer.get(
                "name",
                layer_id,
            )

            if not isinstance(
                name,
                str,
            ):
                name = str(name)

            visible = bool(
                layer.get(
                    "visible",
                    True,
                )
            )

            if layer_id in new_layers:
                raise ValueError(
                    "Duplicate layer identifier: "
                    f"'{layer_id}'."
                )

            new_layers[
                layer_id
            ] = {
                "id": layer_id,
                "name": name,
                "visible": visible,
            }

        self._layers = new_layers

        self._refresh_list()

    # ========================================================
    # SINGLE LAYER UPDATE
    # ========================================================

    def set_layer_visibility(
        self,
        layer_id: str,
        visible: bool,
    ) -> None:
        """
        Update the displayed visibility state of one layer.

        This changes only the panel's presentation snapshot.

        The authoritative canvas/rendering layer must be updated
        separately through the appropriate application boundary.
        """

        layer_id = self._validate_layer_id(
            layer_id
        )

        if not isinstance(
            visible,
            bool,
        ):
            raise TypeError(
                "visible must be a bool."
            )

        if layer_id not in self._layers:
            raise KeyError(
                "Unknown layer: "
                f"'{layer_id}'."
            )

        self._layers[
            layer_id
        ]["visible"] = visible

        self._refresh_list()

    # ========================================================
    # REFRESH
    # ========================================================

    def _refresh_list(
        self,
    ) -> None:
        """
        Rebuild the visible layer list from the presentation
        snapshot.
        """

        self._list.clear()

        for layer in self._layers.values():

            item = QListWidgetItem(
                self._list
            )

            checkbox = QCheckBox(
                layer["name"],
                self._list,
            )

            checkbox.setChecked(
                layer["visible"]
            )

            # ------------------------------------------------
            # Layer identity is stored on the list item.
            #
            # No application object is stored in the widget.
            # ------------------------------------------------

            item.setData(
                32,
                layer["id"],
            )

            checkbox.stateChanged.connect(
                lambda state,
                layer_id=layer["id"]:
                self._on_visibility_changed(
                    layer_id,
                    state,
                )
            )

            self._list.setItemWidget(
                item,
                checkbox,
            )

    # ========================================================
    # VISIBILITY CALLBACK
    # ========================================================

    def _on_visibility_changed(
        self,
        layer_id: str,
        state: Any,
    ) -> None:
        """
        Update the presentation snapshot after a visibility
        checkbox changes.

        No rendering or application-layer mutation occurs here.
        """

        visible = bool(
            state
        )

        if layer_id not in self._layers:
            return

        self._layers[
            layer_id
        ]["visible"] = visible

    # ========================================================
    # LAYER ACCESS
    # ========================================================

    def get_layers(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return a detached snapshot of displayed layers.
        """

        return [
            dict(layer)
            for layer
            in self._layers.values()
        ]

    # --------------------------------------------------------

    def get_layer(
        self,
        layer_id: str,
    ) -> dict[str, Any] | None:
        """
        Return a detached layer snapshot.

        Returns None when the layer is not displayed.
        """

        layer_id = self._validate_layer_id(
            layer_id
        )

        layer = self._layers.get(
            layer_id
        )

        if layer is None:
            return None

        return dict(
            layer
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear all displayed layers.
        """

        self._layers.clear()

        self._list.clear()

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic panel state.
        """

        visible_count = sum(
            1
            for layer
            in self._layers.values()
            if layer["visible"]
        )

        return {
            "layer_count": len(
                self._layers
            ),
            "visible_count": visible_count,
            "layer_ids": list(
                self._layers.keys()
            ),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        state = self.get_state()

        return (
            "LayersPanel("
            f"layers={state['layer_count']}, "
            f"visible={state['visible_count']}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "LayersPanel",
]
