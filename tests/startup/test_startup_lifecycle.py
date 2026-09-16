# ============================================================
# GridForge V2 — Runtime Startup Regression Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

import main
from ui.lifecycle import UILifecyclePhase


def test_import_main() -> None:
    assert main.build_application is not None


def test_application_composition_and_shutdown() -> None:
    app, _window, plugin_manager, workspace_controller, ui_update_boundary, ui_lifecycle = main.build_application()
    assert app is not None
    assert ui_lifecycle.phase is UILifecyclePhase.DOCUMENT_READY
    main._shutdown_components(
        ui_lifecycle=ui_lifecycle,
        workspace_controller=workspace_controller,
        ui_update_boundary=ui_update_boundary,
        plugin_manager=plugin_manager,
    )
    assert ui_lifecycle.closed


def test_startup_failure_uses_existing_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_initialize(self) -> None:
        raise RuntimeError("intentional startup failure")

    monkeypatch.setattr(main.PluginManager, "initialize_all", fail_initialize)
    with pytest.raises(RuntimeError, match="intentional startup failure"):
        main.build_application()
