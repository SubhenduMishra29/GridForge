# ============================================================
# Author: Subhendu Mishra
# File: ui/canvas/canvas_composition.py
# GridForge V2 — Canvas Composition
# ============================================================
"""GridForge V2 application-owned Canvas composition boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ui.canvas.coordinate_system import CoordinateSystem
from ui.canvas.grid_scene import GridScene
from ui.canvas.grid_system import GridSystem
from ui.canvas.graphics_view import GraphicsView
from ui.canvas.interaction_manager import InteractionManager
from ui.canvas.mouse_event_adapter import MouseEventAdapter
from ui.canvas.navigation_controller import NavigationController
from ui.canvas.engineering_canvas_contract import CanvasInteractionContract
from ui.canvas.preview_layer import PreviewLayer
from ui.core.controller import Controller
from ui.core.qt import QComboBox, QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget
from ui.core.selection_manager import SelectionManager
from ui.core.snap_system import SnapSystem
from ui.core.tool_manager import ToolManager
from ui.projection.selection_projection_coordinator import SelectionProjectionCoordinator
from ui.canvas.sld_canvas_projection import SLDCanvasProjection, SLDCanvasSnapshot
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.sld.sld_document import SLDDocument


@dataclass(frozen=True)
class CanvasCompositionPreparation:
    """Canvas services that must exist before ToolManager construction."""

    selection_manager: SelectionManager
    grid_system: GridSystem
    scene: GridScene
    snap_system: SnapSystem
    preview_layer: PreviewLayer


@dataclass
class SLDCanvasSurface(QWidget):
    """Presentation-only SLD editor surface around the canonical GraphicsView.

    This container adds the engineering document/tab chrome visible to the
    user while keeping GraphicsView, ToolManager, SLD projection and render
    synchronization unchanged. It owns no electrical or document state.
    """

    def __init__(
        self,
        view: GraphicsView,
        navigation_controller: NavigationController,
        *,
        sld_canvas_projection: SLDCanvasProjection,
        sld_canvas_render_system: SLDCanvasRenderSystem,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not isinstance(sld_canvas_projection, SLDCanvasProjection):
            raise TypeError("sld_canvas_projection must be an SLDCanvasProjection.")
        if not isinstance(sld_canvas_render_system, SLDCanvasRenderSystem):
            raise TypeError("sld_canvas_render_system must be an SLDCanvasRenderSystem.")
        if sld_canvas_render_system.scene is not view.scene():
            raise ValueError("sld_canvas_render_system must target the canonical GraphicsView scene.")
        self._sld_canvas_projection = sld_canvas_projection
        self._sld_canvas_render_system = sld_canvas_render_system
        self._document_id: str | None = None
        self._sld_canvas_snapshot = SLDCanvasSnapshot(nodes=(), connections=())
        self.setObjectName("SLDCanvasSurface")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget(self)
        header.setObjectName("SLDCanvasHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 5, 8, 5)
        header_layout.setSpacing(5)

        title = QLabel("SLD (Main)", header)
        title.setObjectName("SLDDocumentTitle")
        self._title_label = title
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        mode = QComboBox(header)
        mode.addItems(("Normal Mode", "Placement Mode", "Connection Mode"))
        mode.setObjectName("SLDModeSelector")
        mode.setToolTip("Presentation mode for the active SLD canvas.")
        header_layout.addWidget(mode)

        zoom_out = QPushButton("−", header)
        zoom_out.setObjectName("SLDZoomOut")
        zoom_out.setToolTip("Zoom out")
        zoom_out.clicked.connect(navigation_controller.zoom_out)
        header_layout.addWidget(zoom_out)

        zoom_label = QLabel("100%", header)
        zoom_label.setObjectName("SLDZoomValue")
        header_layout.addWidget(zoom_label)

        zoom_in = QPushButton("+", header)
        zoom_in.setObjectName("SLDZoomIn")
        zoom_in.setToolTip("Zoom in")
        zoom_in.clicked.connect(navigation_controller.zoom_in)
        header_layout.addWidget(zoom_in)

        fit = QPushButton("Fit", header)
        fit.setObjectName("SLDFit")
        fit.setToolTip("Fit the SLD content in the viewport")
        # QPushButton.clicked emits a bool; do not pass that signal payload as
        # the numeric fit margin.
        fit.clicked.connect(
            lambda _checked=False: navigation_controller.fit_content()
        )
        header_layout.addWidget(fit)

        root.addWidget(header)

        tabs = QTabWidget(self)
        tabs.setObjectName("SLDDocumentTabs")
        tabs.setTabsClosable(False)
        page = QWidget(tabs)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(view)
        tabs.addTab(page, "SLD (Main)")
        plus = QPushButton("+", tabs)
        plus.setObjectName("SLDNewDocumentButton")
        plus.setEnabled(False)
        plus.setToolTip("Additional SLD documents are managed by the project/document lifecycle.")
        tabs.setCornerWidget(plus)
        root.addWidget(tabs, 1)

    def present_document(self, document: SLDDocument) -> SLDCanvasSnapshot:
        """Present the Application-authoritative SLD document on this surface."""
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument.")
        snapshot = self._sld_canvas_projection.project(document.model)
        self._sld_canvas_render_system.synchronize(snapshot)
        self._document_id = document.document_id
        self._sld_canvas_snapshot = snapshot
        return snapshot

    def clear_document(self) -> None:
        """Clear canonical SLD graphics without mutating Core/Application state."""
        self._sld_canvas_render_system.clear()
        self._document_id = None
        self._sld_canvas_snapshot = SLDCanvasSnapshot(nodes=(), connections=())

    @property
    def document_id(self) -> str | None:
        return self._document_id

    @property
    def sld_canvas_snapshot(self) -> SLDCanvasSnapshot:
        return self._sld_canvas_snapshot

    def set_document_title(self, title: str | None) -> None:
        """Update only the visible document-tab title from projected application state."""
        value = str(title).strip() if title is not None else ""
        display = f"{value} SLD (Main)" if value else "SLD (Main)"
        self._title_label.setText(display)


@dataclass
class CanvasComposition:
    """Fully composed Canvas viewport and interaction services."""

    view: GraphicsView
    surface: SLDCanvasSurface
    scene: GridScene
    selection_manager: SelectionManager
    grid_system: GridSystem
    interaction_manager: InteractionManager
    navigation_controller: NavigationController
    coordinate_system: CoordinateSystem
    snap_system: SnapSystem
    preview_layer: PreviewLayer
    application: Any
    sld_canvas_projection: SLDCanvasProjection
    sld_canvas_render_system: SLDCanvasRenderSystem
    selection_projection: SelectionProjectionCoordinator
    interaction_contract: CanvasInteractionContract

    @property
    def widget(self) -> QWidget:
        return self.surface


class CanvasComposer:
    """Application-level constructor for the Canvas service graph."""

    def prepare(self, *, controller: Controller) -> CanvasCompositionPreparation:
        """Create the shared Canvas interaction dependencies."""
        if controller is None:
            raise ValueError("controller must not be None.")

        selection_manager = SelectionManager()
        grid_system = GridSystem()
        scene = GridScene()
        snap_system = SnapSystem(
            controller=controller,
            grid_system=grid_system,
            scene=scene,
        )
        preview_layer = PreviewLayer(scene=scene)

        return CanvasCompositionPreparation(
            selection_manager=selection_manager,
            grid_system=grid_system,
            scene=scene,
            snap_system=snap_system,
            preview_layer=preview_layer,
        )

    def compose(
        self,
        *,
        controller: Controller,
        tool_manager: ToolManager,
        preparation: CanvasCompositionPreparation,
        parent: Optional[QWidget] = None,
        workspace_id: str = "sld",
        discipline: str | None = None,
        properties_panel: Any = None,
        sld_canvas_projection: SLDCanvasProjection | None = None,
        sld_canvas_render_system: SLDCanvasRenderSystem | None = None,
    ) -> CanvasComposition:
        """Construct one complete Canvas service graph.

        The SelectionProjectionCoordinator is always composed with the
        Canvas service graph. Its PropertiesPanel target may be bound later
        through the same coordinator instance when the PanelsPlugin presents
        the canonical PropertiesPanel.
        """
        if controller is None:
            raise ValueError("controller must not be None.")
        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")
        if not isinstance(preparation, CanvasCompositionPreparation):
            raise TypeError("preparation must be CanvasCompositionPreparation.")
        if not isinstance(sld_canvas_projection, SLDCanvasProjection):
            raise TypeError("sld_canvas_projection must be an SLDCanvasProjection.")
        if not isinstance(sld_canvas_render_system, SLDCanvasRenderSystem):
            raise TypeError("sld_canvas_render_system must be an SLDCanvasRenderSystem.")

        application = tool_manager.application
        interaction_contract = CanvasInteractionContract()
        if application is None:
            raise ValueError("tool_manager must retain the canonical Application.")

        selection_manager = preparation.selection_manager
        grid_system = preparation.grid_system
        scene = preparation.scene
        snap_system = preparation.snap_system
        preview_layer = preparation.preview_layer

        if tool_manager.selection_manager is not selection_manager:
            raise ValueError("ToolManager must use the prepared SelectionManager.")
        if tool_manager.snap_system is not snap_system:
            raise ValueError("ToolManager must use the prepared SnapSystem.")
        if tool_manager.preview_layer is not preview_layer:
            raise ValueError("ToolManager must use the prepared PreviewLayer.")

        view = GraphicsView(
            controller=controller,
            tool_manager=tool_manager,
            scene=scene,
            parent=parent,
        )
        coordinate_system = CoordinateSystem(view=view, grid_system=grid_system)
        input_adapter = MouseEventAdapter(view=view, scene=scene)
        interaction_manager = InteractionManager(
            view=view,
            controller=controller,
            tool_manager=tool_manager,
            coordinate_system=coordinate_system,
            snap_system=snap_system,
            preview_layer=preview_layer,
            selection_manager=selection_manager,
            workspace_id=workspace_id,
            discipline=discipline or workspace_id,
            input_adapter=input_adapter,
        )
        navigation_controller = NavigationController(view=view)

        view.bind_services(
            interaction_manager=interaction_manager,
            navigation_controller=navigation_controller,
        )
        surface = SLDCanvasSurface(
            view=view,
            navigation_controller=navigation_controller,
            sld_canvas_projection=sld_canvas_projection,
            sld_canvas_render_system=sld_canvas_render_system,
            parent=parent,
        )
        selection_manager.set_scene(scene)

        selection_projection = SelectionProjectionCoordinator(
            selection_manager=selection_manager,
            application=application,
            properties_panel=properties_panel,
        )

        return CanvasComposition(
            view=view,
            surface=surface,
            scene=scene,
            selection_manager=selection_manager,
            grid_system=grid_system,
            interaction_manager=interaction_manager,
            navigation_controller=navigation_controller,
            coordinate_system=coordinate_system,
            snap_system=snap_system,
            preview_layer=preview_layer,
            application=application,
            sld_canvas_projection=sld_canvas_projection,
            sld_canvas_render_system=sld_canvas_render_system,
            selection_projection=selection_projection,
            interaction_contract=interaction_contract,
        )

    def bind_selection_projection(
        self,
        *,
        composition: CanvasComposition,
        properties_panel: Any,
    ) -> SelectionProjectionCoordinator:
        """Bind the real PropertiesPanel after panel plugin composition."""
        if not isinstance(composition, CanvasComposition):
            raise TypeError("composition must be CanvasComposition.")
        if properties_panel is None:
            raise ValueError("properties_panel must not be None.")
        coordinator = composition.selection_projection
        coordinator.set_properties_panel(properties_panel)
        return coordinator


__all__ = [
    "CanvasCompositionPreparation",
    "CanvasComposition",
    "SLDCanvasSurface",
    "CanvasComposer",
]
