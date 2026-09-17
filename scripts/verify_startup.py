# ============================================================
# GridForge V2 — Deterministic Runtime Startup Verification
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import ast
import compileall
import importlib
from pathlib import Path

from ui.lifecycle import UILifecyclePhase
from ui.workspace.workspace_defaults import CANONICAL_PANEL_IDS

SOURCE_ROOTS = (Path("core"), Path("ui"))


def iter_python_files() -> list[Path]:
    files = [Path("main.py")]
    for root in SOURCE_ROOTS:
        files.extend(root.rglob("*.py"))
    return sorted(set(files))


def verify_source_integrity() -> None:
    corrupted: list[Path] = []
    for path in iter_python_files():
        text = path.read_text(encoding="utf-8")
        if text.startswith("```python\n") or text.startswith("```\n") or text.rstrip().endswith("\n```"):
            corrupted.append(path)
    if corrupted:
        names = ", ".join(str(path) for path in corrupted)
        raise SystemExit(f"Markdown fencing detected in Python source: {names}")


def verify_syntax() -> None:
    failures: list[Path] = []
    for path in iter_python_files():
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            failures.append(path)
    if failures:
        names = ", ".join(str(path) for path in failures)
        raise SystemExit(f"Python syntax verification failed: {names}")
    if not compileall.compile_dir("core", quiet=1, force=True):
        raise SystemExit("Python bytecode compilation failed for core/")
    if not compileall.compile_dir("ui", quiet=1, force=True):
        raise SystemExit("Python bytecode compilation failed for ui/")
    if not compileall.compile_file("main.py", quiet=1, force=True):
        raise SystemExit("Python bytecode compilation failed for main.py")


def verify_imports() -> None:
    importlib.import_module("main")


def verify_workspace_composition(window, plugin_manager, workspace_controller) -> None:
    root_widget = window.central_surface
    if root_widget is None:
        raise SystemExit("MainWindow has no central shell/root widget.")

    canvas_plugin = plugin_manager.get("canvas")
    if canvas_plugin is None:
        raise SystemExit("Canvas plugin is not registered.")

    canvas_widget = canvas_plugin.widget
    if canvas_widget is None:
        raise SystemExit("Canvas plugin did not expose a widget.")

    if root_widget is canvas_widget:
        raise SystemExit("Shell root widget must be distinct from GraphicsView canvas widget.")

    if canvas_widget.parentWidget() is not root_widget:
        raise SystemExit("GraphicsView canvas widget is not owned by the shell root widget.")

    panels_plugin = plugin_manager.get("panels")
    if panels_plugin is None:
        raise SystemExit("Panels plugin is not registered.")

    missing: list[str] = []
    for panel_id in CANONICAL_PANEL_IDS:
        dock = panels_plugin.get_dock(panel_id)
        if dock is None:
            missing.append(panel_id)
            continue
        if dock.parentWidget() is not window:
            raise SystemExit(
                f"Dock {panel_id!r} has incorrect Qt parent: "
                f"{type(dock.parentWidget()).__name__ if dock.parentWidget() is not None else None}."
            )

    if missing:
        raise SystemExit(f"Missing canonical docks: {', '.join(missing)}")

    realized_layout = workspace_controller.realized_layout
    if realized_layout is None:
        raise SystemExit("Canonical workspace has not been realized.")

    realized_ids = tuple(
        placement.panel_id for placement in realized_layout.placements
    )
    if realized_ids != CANONICAL_PANEL_IDS:
        raise SystemExit(
            f"Canonical workspace dock realization mismatch: {realized_ids!r}"
        )


def verify_application_lifecycle() -> None:
    import main

    app, window, plugin_manager, workspace_controller, ui_update_boundary, ui_lifecycle = main.build_application()
    try:
        if app is None or ui_lifecycle.phase is not UILifecyclePhase.DOCUMENT_READY:
            raise SystemExit(
                "Application composition did not establish a document-ready UI lifecycle."
            )
        verify_workspace_composition(window, plugin_manager, workspace_controller)
    finally:
        main._shutdown_components(
            ui_lifecycle=ui_lifecycle,
            workspace_controller=workspace_controller,
            ui_update_boundary=ui_update_boundary,
            plugin_manager=plugin_manager,
        )


def main() -> None:
    verify_source_integrity()
    verify_syntax()
    verify_imports()
    verify_application_lifecycle()
    print("startup verification: PASS")


if __name__ == "__main__":
    main()
