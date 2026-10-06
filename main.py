# ============================================================
# GridForge V2 — Application Composition Root
# ============================================================
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import sys
from collections.abc import Callable
from uuid import uuid4

from core.application.bootstrap import create_application
from core.application.events import ProjectLoaded
from core.application.services.sld_service import SLDService
from core.network.network import Network

from ui.canvas.canvas_composition import CanvasComposer
from ui.events.control_update_coordinator import ControlUpdateCoordinator
from ui.control.control_surface_host import ControlSurfaceHost
from ui.control.control_workspace import ControlWorkspace
from ui.protection.protection_workspace import ProtectionWorkspace
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.controllers.study_case_controller import StudyCaseController
from ui.core.controller import Controller
from ui.core.action_router import UIActionRouter
from ui.core.action_definition import ActionDefinition
from ui.core.action_catalog import build_action_definitions
from ui.core.tool_manager import ToolManager
from ui.bootstrap.presentation_bootstrap import PresentationBootstrap
from ui.core.qt import QApplication, QFileDialog, QMessageBox, QWidget, QGraphicsView, QVBoxLayout
from ui.events.sld_update_coordinator import SLDUpdateCoordinator
from ui.events.update_boundary import UIUpdateBoundary
from ui.lifecycle import UILifecycle
from ui.lifecycle.project_close_controller import ProjectCloseController
from ui.main_window import MainWindow
from ui.panels.panel_presentation_bridge import PanelPresentationBridge
from ui.plugins.plugin_context import PluginContext
from ui.styling.style_manager import StyleManager
from ui.plugins.plugin_manager import PluginManager
from ui.projection.element_list_projection import ElementListProjection
from ui.projection.application_event_messages import ApplicationEventMessagesProjection
from ui.projection.project_hierarchy_projection import ProjectHierarchyProjection
from ui.projection.study_projection import StudyProjection
from ui.projection.ui_projection_coordinator import UIProjectionCoordinator
from ui.projection.validation_projection import ValidationProjection
from ui.sld.sld_controller import SLDController
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_projection_manager import SLDProjectionManager
from ui.sld.sld_state import SLDState
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer
from ui.workspace.project_workspace import ProjectWorkspaceLifecycle
from ui.workspace.project_workspace_adapter import ProjectWorkspaceApplicationAdapter, ProjectWorkspaceChanged
from ui.workspace.workspace_controller import WorkspaceController
from ui.workspace.workspace_defaults import CONTROL_WORKSPACE_ID, PROTECTION_WORKSPACE_ID, SLD_WORKSPACE_ID, STUDY_WORKSPACE_ID, default_workspaces
from ui.workspace.workspace_manager import WorkspaceManager
from ui.workspace.workspace_realizer import WorkspaceRealizer
from ui.workspace.engineering_context import EngineeringContextStore
from ui.tools.default_tool_registry import create_default_tool_factories
from ui.tools.tool_definition import contextual_tool_definitions
from ui.tools.tool_mode import ToolMode
from ui.tools.tool_settings import ToolSettings
from ui.editors.study.study_tool_runtime import StudyToolRuntime
from ui.equipment.symbol.palette_symbol_adapter import PaletteSymbolAdapter
from ui.control.control_tool_palette import ControlToolRegistry