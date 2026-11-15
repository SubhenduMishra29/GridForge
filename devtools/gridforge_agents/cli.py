from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings
from .agent import AgentExecutionError
from .ollama import OllamaClient, OllamaError
from .workflow import (
    WorkflowError,
    audit_repository,
    doctor,
    repository_root,
    run_issue,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gridforge-agents",
        description="Run the GridForge autonomous local-agent workbench through Ollama.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Check Python, Git, Ollama and configured local models.")
    subparsers.add_parser("audit", help="Run a read-only model-assisted repository audit.")
    run_parser = subparsers.add_parser("run", help="Implement one open GitHub issue in an isolated Git worktree.")
    run_parser.add_argument("--issue", type=int, required=True, help="Open GridForge GitHub issue number.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if sys.version_info < (3, 10):
        print("GridForge local agents require Python 3.10 or newer.", file=sys.stderr)
        return 2

    settings = Settings.from_environment()
    client = OllamaClient(settings)
    try:
        root = repository_root(Path.cwd())
        if args.command == "doctor":
            status = doctor(root, settings, client)
            print(json.dumps(status, indent=2))
            if status.get("status") != "ready":
                return 1
            print("\nReady. The local agent runtime is independent of GridForge's application dependencies.")
            return 0
        if args.command == "audit":
            report, path = audit_repository(root, settings, client)
            print("\n" + report)
            print("\nAudit report saved to: %s" % path)
            return 0
        if args.command == "run":
            result = run_issue(root, args.issue, settings, client)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result.get("status") == "committed_local" else 1
    except (WorkflowError, OllamaError, AgentExecutionError) as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped by user. Existing worktree and changes were preserved.", file=sys.stderr)
        return 130
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
