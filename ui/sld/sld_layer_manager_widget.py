"""Explorer-region manager for non-destructive SLD presentation layers."""

from __future__ import annotations

from uuid import uuid4

from ui.core.qt import (
    QCheckBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)


class SLDLayerManagerWidget(QWidget):
    """Thin UI over the canonical SLDController layer-command API."""

    def __init__(self, *, sld_controller, parent=None) -> None:
        super().__init__(parent)
        self._controller = sld_controller
        self.setObjectName("SLDLayerManager")
        self._layers: tuple = ()

        root = QVBoxLayout(self)
        self._list = QListWidget(self)
        self._list.setObjectName("SLDLayerList")
        root.addWidget(self._list)

        self._name = QLineEdit(self)
        self._name.setObjectName("SLDLayerName")
        self._name.setPlaceholderText("Layer name")
        root.addWidget(self._name)

        self._visible = QCheckBox("Visible", self)
        self._locked = QCheckBox("Locked", self)
        checks = QHBoxLayout()
        checks.addWidget(self._visible)
        checks.addWidget(self._locked)
        root.addLayout(checks)

        self._opacity = QDoubleSpinBox(self)
        self._opacity.setObjectName("SLDLayerOpacity")
        self._opacity.setRange(0.0, 1.0)
        self._opacity.setDecimals(2)
        self._opacity.setSingleStep(0.05)
        self._opacity.setPrefix("Opacity ")
        root.addWidget(self._opacity)

        actions = QHBoxLayout()
        self._add = QPushButton("Add", self)
        self._rename = QPushButton("Rename", self)
        self._delete = QPushButton("Delete", self)
        self._up = QPushButton("Up", self)
        self._down = QPushButton("Down", self)
        for button in (self._add, self._rename, self._delete, self._up, self._down):
            actions.addWidget(button)
        root.addLayout(actions)

        self._status = QLabel(self)
        self._status.setObjectName("SLDLayerStatus")
        root.addWidget(self._status)

        self._list.currentRowChanged.connect(self._selection_changed)
        self._visible.toggled.connect(lambda value: self._update_selected(visible=value))
        self._locked.toggled.connect(lambda value: self._update_selected(locked=value))
        self._opacity.valueChanged.connect(lambda value: self._update_selected(opacity=value))
        self._add.clicked.connect(self._create_layer)
        self._rename.clicked.connect(self._rename_layer)
        self._delete.clicked.connect(self._delete_layer)
        self._up.clicked.connect(lambda: self._move_layer(-1))
        self._down.clicked.connect(lambda: self._move_layer(1))
        self.refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        document = self._controller.active_document
        self._layers = () if document is None else document.layers
        active_id = None
        if document is not None:
            try:
                active_id = self._controller.active_layer_id
            except Exception:
                active_id = document.default_layer_id
        self._list.blockSignals(True)
        self._list.clear()
        selected = 0
        for index, layer in enumerate(self._layers):
            flags = []
            if not layer.visible:
                flags.append("hidden")
            if layer.locked:
                flags.append("locked")
            suffix = f" ({', '.join(flags)})" if flags else ""
            item = QListWidgetItem(f"{layer.name}{suffix}")
            self._list.addItem(item)
            if layer.layer_id == active_id:
                selected = index
        self._list.setCurrentRow(selected if self._layers else -1)
        self._list.blockSignals(False)
        self._selection_changed(self._list.currentRow())

    def _selected(self):
        row = self._list.currentRow()
        return self._layers[row] if 0 <= row < len(self._layers) else None

    def _selection_changed(self, row: int) -> None:
        layer = self._selected()
        controls = layer is not None
        for widget in (self._name, self._visible, self._locked, self._opacity,
                       self._rename, self._delete, self._up, self._down):
            widget.setEnabled(controls)
        if layer is None:
            self._name.clear()
            return
        self._name.setText(layer.name)
        for widget in (self._visible, self._locked, self._opacity):
            widget.blockSignals(True)
        self._visible.setChecked(layer.visible)
        self._locked.setChecked(layer.locked)
        self._opacity.setValue(layer.opacity)
        for widget in (self._visible, self._locked, self._opacity):
            widget.blockSignals(False)
        try:
            if not layer.locked:
                self._controller.set_active_layer(layer.layer_id)
        except Exception as exc:
            self._status.setText(str(exc))

    def _apply(self, action) -> None:
        try:
            action()
            self._status.setText("")
        except Exception as exc:
            self._status.setText(str(exc))
        self.refresh()

    def _update_selected(self, **changes) -> None:
        layer = self._selected()
        if layer is None:
            return
        self._apply(lambda: self._controller.update_layer(layer.layer_id, **changes))

    def _create_layer(self) -> None:
        name = f"Layer {len(self._layers) + 1}"
        self._apply(lambda: self._controller.create_layer(
            layer_id=f"layer-{uuid4().hex}", name=name
        ))

    def _rename_layer(self) -> None:
        layer = self._selected()
        name = self._name.text().strip()
        if layer is None or not name:
            return
        self._apply(lambda: self._controller.update_layer(layer.layer_id, name=name))

    def _delete_layer(self) -> None:
        layer = self._selected()
        if layer is None or layer.layer_id == "default":
            self._status.setText("The Default layer cannot be deleted.")
            return
        self._apply(lambda: self._controller.delete_layer(layer.layer_id, reassign_to="default"))

    def _move_layer(self, offset: int) -> None:
        row = self._list.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= len(self._layers):
            return
        ordered = [item.layer_id for item in self._layers]
        ordered[row], ordered[target] = ordered[target], ordered[row]
        self._apply(lambda: self._controller.reorder_layers(ordered))
        self._list.setCurrentRow(target)


__all__ = ["SLDLayerManagerWidget"]
