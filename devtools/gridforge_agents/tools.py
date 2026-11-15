from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path
from typing import Any


PROTECTED_PARTS = {
    ".git", ".venv", ".venv-gridforge-agents", "venv", "node_modules",
    "__pycache__", ".gridforge-agent", ".pytest_cache", ".mypy_cache",
}
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".ini",
    ".cfg", ".xml", ".qss", ".ui", ".sql", ".ps1", ".bat", ".cmd",
}


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


READ_TOOLS = [
    _tool("list_files", "List repository files matching a glob pattern. Paths are relative to the repository root.", {
        "pattern": {"type": "string", "description": "For example **/*.py or core/**/*.py"},
        "limit": {"type": "integer", "description": "Maximum results, up to 300"},
    }, ["pattern"]),
    _tool("read_file", "Read a UTF-8 text file with optional 1-based line bounds.", {
        "path": {"type": "string"},
        "start_line": {"type": "integer"},
        "end_line": {"type": "integer"},
        "tail_lines": {"type": "integer", "description": "Return only the last N lines; useful for append-only registers."},
    }, ["path"]),
    _tool("search_text", "Search text files for a literal, case-insensitive phrase.", {
        "query": {"type": "string"},
        "pattern": {"type": "string", "description": "Optional glob filter such as **/*.py"},
        "limit": {"type": "integer"},
    }, ["query"]),
    _tool("git_status", "Return the current worktree status and branch.", {}, []),
    _tool("git_diff", "Return the current tracked diff, optionally including staged changes.", {
        "staged": {"type": "boolean"},
    }, []),
]

WRITE_TOOLS = [
    _tool("write_file", "Create or replace one UTF-8 repository file. The path must remain inside the isolated agent worktree.", {
        "path": {"type": "string"},
        "content": {"type": "string"},
    }, ["path", "content"]),
    _tool("replace_text", "Replace one exact text occurrence in a repository file. Fails unless the old text occurs exactly once.", {
        "path": {"type": "string"},
        "old_text": {"type": "string"},
        "new_text": {"type": "string"},
    }, ["path", "old_text", "new_text"]),
    _tool("static_check", "Run git diff --check and Python compile checks for changed Python files. Does not run the test suite.", {}, []),
]


class ToolError(RuntimeError):
    """Raised for an invalid or unsafe agent tool request."""


class ToolRunner:
    def __init__(self, root: Path, *, writable: bool = False) -> None:
        self.root = root.resolve()
        self.writable = writable
        self.schemas = READ_TOOLS + (WRITE_TOOLS if writable else [])
        self._handlers = {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "search_text": self.search_text,
            "git_status": self.git_status,
            "git_diff": self.git_diff,
        }
        if writable:
            self._handlers.update({
                "write_file": self.write_file,
                "replace_text": self.replace_text,
                "static_check": self.static_check,
            })

    def _path(self, value: str) -> Path:
        raw = Path(value)
        if raw.is_absolute():
            raise ToolError("Absolute paths are not permitted.")
        target = (self.root / raw).resolve()
        try:
            relative = target.relative_to(self.root)
        except ValueError as exc:
            raise ToolError("Path escapes the isolated repository worktree.") from exc
        if any(part in PROTECTED_PARTS for part in relative.parts):
            raise ToolError("Access to protected runtime, cache or Git directories is denied.")
        if relative.name.lower() == ".env" or relative.name.lower().startswith(".env."):
            raise ToolError("Environment and secret files are not accessible to agents.")
        if relative.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".p8", ".keystore"}:
            raise ToolError("Private key and certificate files are not accessible to agents.")
        if any(part.casefold() in {"secrets", "credentials"} for part in relative.parts):
            raise ToolError("Secret and credential directories are not accessible to agents.")
        if relative.parts and relative.parts[0] == ".vscode":
            raise ToolError("VS Code workspace configuration is protected from agent edits.")
        return target

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        handler = self._handlers.get(name)
        if handler is None:
            raise ToolError("Tool is unavailable in this agent role: %s" % name)
        try:
            result = handler(**arguments)
        except TypeError as exc:
            raise ToolError("Invalid arguments for %s: %s" % (name, exc)) from exc
        return str(result)

    def list_files(self, pattern: str = "**/*", limit: int = 150) -> str:
        limit = max(1, min(int(limit), 300))
        matches: list[str] = []
        for path in self.root.glob(pattern):
            if not path.is_file():
                continue
            try:
                relative = path.relative_to(self.root)
            except ValueError:
                continue
            if any(part in PROTECTED_PARTS for part in relative.parts):
                continue
            if relative.parts and relative.parts[0] == ".vscode":
                continue
            matches.append(relative.as_posix())
            if len(matches) >= limit:
                break
        return "\n".join(matches) if matches else "(no matching files)"

    def read_file(
        self, path: str, start_line: int = 1, end_line: int | None = None,
        tail_lines: int | None = None,
    ) -> str:
        target = self._path(path)
        if not target.is_file():
            raise ToolError("File does not exist: %s" % path)
        if target.stat().st_size > 1_000_000 and tail_lines is None and end_line is None:
            raise ToolError("File exceeds the 1 MB read limit; request a bounded line range or tail_lines.")
        try:
            if tail_lines is not None:
                count = max(1, min(int(tail_lines), 500))
                recent: deque[tuple[int, str]] = deque(maxlen=count)
                with target.open("r", encoding="utf-8") as stream:
                    for number, line in enumerate(stream, 1):
                        recent.append((number, line.rstrip("\r\n")))
                return "\n".join("%d: %s" % item for item in recent)

            if target.stat().st_size > 180_000 and end_line is None:
                raise ToolError("Large file reads require end_line or tail_lines.")
            start = max(1, int(start_line))
            end = None if end_line is None else max(start, int(end_line))
            selected: list[str] = []
            with target.open("r", encoding="utf-8") as stream:
                for number, line in enumerate(stream, 1):
                    if number < start:
                        continue
                    if end is not None and number > end:
                        break
                    selected.append("%d: %s" % (number, line.rstrip("\r\n")))
            return "\n".join(selected)
        except UnicodeDecodeError as exc:
            raise ToolError("File is not UTF-8 text: %s" % path) from exc

    def search_text(self, query: str, pattern: str = "**/*", limit: int = 60) -> str:
        if not query.strip():
            raise ToolError("Search query cannot be empty.")
        limit = max(1, min(int(limit), 100))
        matches: list[str] = []
        needle = query.casefold()
        for path in self.root.glob(pattern):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                relative = path.relative_to(self.root)
            except ValueError:
                continue
            if any(part in PROTECTED_PARTS for part in relative.parts):
                continue
            if relative.parts and relative.parts[0] == ".vscode":
                continue
            if relative.name.lower() == ".env" or relative.name.lower().startswith(".env."):
                continue
            if relative.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".p8", ".keystore"}:
                continue
            if any(part.casefold() in {"secrets", "credentials"} for part in relative.parts):
                continue
            try:
                if path.stat().st_size > 1_000_000:
                    continue
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for number, line in enumerate(lines, 1):
                if needle in line.casefold():
                    matches.append("%s:%d: %s" % (relative.as_posix(), number, line[:500]))
                    if len(matches) >= limit:
                        return "\n".join(matches)
        return "\n".join(matches) if matches else "(no matches)"

    def git_status(self) -> str:
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=str(self.root), capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise ToolError(result.stderr.strip() or "git status failed")
        return result.stdout.strip() or "(clean worktree)"

    def git_diff(self, staged: bool = False) -> str:
        command = ["git", "diff", "--no-ext-diff"]
        if staged:
            command.append("--cached")
        result = subprocess.run(
            command, cwd=str(self.root), capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise ToolError(result.stderr.strip() or "git diff failed")
        return result.stdout[-35_000:] if result.stdout else "(no diff)"

    def _atomic_write(self, target: Path, content: str) -> str:
        encoded = content.encode("utf-8")
        if len(encoded) > 500_000:
            raise ToolError("A single agent write is limited to 500 KB.")
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix="." + target.name + ".", suffix=".agent-tmp", dir=str(target.parent))
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(str(temporary), str(target))
        finally:
            if temporary.exists():
                temporary.unlink()
        return "Wrote %s (%d bytes)." % (target.relative_to(self.root).as_posix(), len(encoded))

    def write_file(self, path: str, content: str) -> str:
        if not self.writable:
            raise ToolError("This agent is read-only.")
        return self._atomic_write(self._path(path), content)

    def replace_text(self, path: str, old_text: str, new_text: str) -> str:
        if not self.writable:
            raise ToolError("This agent is read-only.")
        if not old_text:
            raise ToolError("old_text cannot be empty.")
        target = self._path(path)
        if not target.is_file():
            raise ToolError("File does not exist: %s" % path)
        original = target.read_text(encoding="utf-8")
        count = original.count(old_text)
        if count != 1:
            raise ToolError("Expected exactly one old_text match; found %d. No change made." % count)
        return self._atomic_write(target, original.replace(old_text, new_text, 1))

    def static_check(self) -> str:
        if not self.writable:
            raise ToolError("Static checks are only available in an implementation worktree.")
        diff_check = subprocess.run(
            ["git", "diff", "--check"], cwd=str(self.root),
            capture_output=True, text=True, timeout=60,
        )
        if diff_check.returncode:
            return "git diff --check FAILED:\n" + (diff_check.stdout + diff_check.stderr)
        changed = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR"],
            cwd=str(self.root), capture_output=True, text=True, timeout=30,
        )
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(self.root), capture_output=True, text=True, timeout=30,
        )
        if changed.returncode or untracked.returncode:
            raise ToolError((changed.stderr + untracked.stderr).strip() or "Could not list changed files.")
        names = set(changed.stdout.splitlines()) | set(untracked.stdout.splitlines())
        python_files = [
            name for name in sorted(names)
            if name.lower().endswith(".py") and (self.root / name).is_file()
        ]
        if not python_files:
            return "PASS: git diff --check. No changed Python files to compile."
        compile_result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q"] + python_files,
            cwd=str(self.root), capture_output=True, text=True, timeout=120,
        )
        if compile_result.returncode:
            return "Python compile check FAILED:\n" + (compile_result.stdout + compile_result.stderr)
        return "PASS: git diff --check and compileall for %d changed Python file(s)." % len(python_files)
