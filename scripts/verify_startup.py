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


def verify_application_lifecycle() -> None:
    import main

    app, _window, plugin_manager, workspace_controller, ui_update_boundary, ui_lifecycle = main.build_application()
    try:
        if app is None or ui_lifecycle.phase is not UILifecyclePhase.DOCUMENT_READY:
            raise SystemExit(
                "Application composition did not establish a document-ready UI lifecycle."
            )
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
