from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .agent import run_agent
from .config import Settings, application_data_dir
from .ollama import OllamaClient
from .prompts import DOMAIN_GUIDANCE, classify_issue, system_prompt
from .tools import ToolRunner


class WorkflowError(RuntimeError):
    """Raised when a local agent workflow cannot safely continue."""


def run_git(root: Path, arguments: list[str], timeout: int = 120) -> str:
    result = subprocess.run(
        ["git"] + arguments,
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode:
        raise WorkflowError(
            "git %s failed:\n%s" % (" ".join(arguments), (result.stdout + result.stderr).strip())
        )
    return result.stdout.strip()


def repository_root(start: Path | None = None) -> Path:
    cwd = start or Path.cwd()
    try:
        value = run_git(cwd, ["rev-parse", "--show-toplevel"])
    except WorkflowError as exc:
        raise WorkflowError("Open the GridForge repository folder in VS Code before running agents.") from exc
    return Path(value).resolve()


def check_models(client: OllamaClient, settings: Settings) -> list[str]:
    installed = client.installed_models()
    required = [settings.planner_model, settings.implementer_model, settings.reviewer_model]
    missing = [model for model in required if model not in installed]
    if missing:
        commands = "\n".join("  ollama pull %s" % model for model in sorted(set(missing)))
        raise WorkflowError(
            "Required Ollama model(s) are not installed: %s\nInstall with:\n%s\n"
            "Or override GRIDFORGE_PLANNER_MODEL / GRIDFORGE_CODER_MODEL / GRIDFORGE_REVIEWER_MODEL."
            % (", ".join(sorted(set(missing))), commands)
        )
    return installed


def _version_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", value)
    return tuple(int(part) for part in match.groups()) if match else None


def ensure_tool_runtime(client: OllamaClient, settings: Settings) -> str:
    version = client.version()
    parsed = _version_tuple(version)
    if parsed is None or parsed < (0, 3, 0):
        raise WorkflowError(
            "Ollama %s is too old or unrecognized for native tool calling. Upgrade Ollama to 0.3.0 or newer, "
            "restart Ollama, then run the VS Code Doctor task again." % version
        )
    for model in sorted(set([settings.planner_model, settings.implementer_model, settings.reviewer_model])):
        if not client.probe_tool_calling(model):
            client.unload(model)
            raise WorkflowError(
                "Model %s did not return a structured tool call. Select a tool-capable model or update its Ollama template. "
                "Qwen3 8B is the recommended local default." % model
            )
        client.unload(model)
    return version


def doctor(root: Path, settings: Settings, client: OllamaClient) -> dict[str, Any]:
    models = check_models(client, settings)
    version = client.version()
    parsed = _version_tuple(version)
    tool_probe: dict[str, bool] = {}
    if parsed is not None and parsed >= (0, 3, 0):
        for model in sorted(set([settings.planner_model, settings.implementer_model, settings.reviewer_model])):
            tool_probe[model] = client.probe_tool_calling(model)
            client.unload(model)
    branch = run_git(root, ["branch", "--show-current"])
    remote = run_git(root, ["remote", "get-url", "origin"])
    ready = parsed is not None and parsed >= (0, 3, 0) and all(tool_probe.values())
    return {
        "status": "ready" if ready else "needs_attention",
        "ollama_version": version,
        "tool_calling": tool_probe,
        "setup_note": "" if ready else "Upgrade Ollama to 0.3.0+ and confirm each selected model returns structured tool_calls.",
        "python": os.sys.version.split()[0],
        "repository": str(root),
        "branch": branch,
        "origin": remote,
        "ollama_url": settings.ollama_url,
        "models": models,
        "planner": settings.planner_model,
        "implementer": settings.implementer_model,
        "reviewer": settings.reviewer_model,
        "context_size": settings.context_size,
    }


def _save_report(name: str, payload: dict[str, Any]) -> Path:
    directory = application_data_dir() / "runs"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (name + ".json")
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    return path


def _github_json(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GridForge-Local-Agent-Workbench",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise WorkflowError("GitHub API lookup failed (HTTP %s): %s" % (exc.code, detail)) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise WorkflowError("Could not reach GitHub API: %s" % exc) from exc


def fetch_open_issues(repo: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in range(1, 6):
        url = "https://api.github.com/repos/%s/issues?state=open&sort=updated&direction=desc&per_page=100&page=%d" % (repo, page)
        batch = _github_json(url)
        if not isinstance(batch, list):
            raise WorkflowError("GitHub returned an unexpected open-issues response.")
        items.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break
    return items


def fetch_open_pull_requests(repo: str) -> list[dict[str, Any]]:
    url = "https://api.github.com/repos/%s/pulls?state=open&per_page=100" % repo
    items = _github_json(url)
    if not isinstance(items, list):
        raise WorkflowError("GitHub returned an unexpected open-PR response.")
    return items


def audit_repository(root: Path, settings: Settings, client: OllamaClient) -> tuple[str, Path]:
    check_models(client, settings)
    ensure_tool_runtime(client, settings)
    open_issues = fetch_open_issues(settings.github_repo)
    open_prs = fetch_open_pull_requests(settings.github_repo)
    issue_index = "\n".join(
        "- #%s %s [%s]" % (
            item.get("number"), item.get("title", ""),
            ", ".join(label.get("name", "") for label in item.get("labels", [])),
        )
        for item in open_issues
    )
    pr_index = "\n".join(
        "- PR #%s %s (%s -> %s)" % (
            item.get("number"), item.get("title", ""),
            item.get("head", {}).get("ref", ""), item.get("base", {}).get("ref", ""),
        )
        for item in open_prs
    )
    print("[AUDIT] Read-only source and GitHub backlog inspection with %s" % settings.planner_model, flush=True)
    prompt = (
        "Audit this current GridForge repository against the frozen V2 architecture. "
        "Start by inspecting git status, root file layout, README.md, pyproject.toml, Modification_Register.txt, "
        "and relevant docs. Then trace the current implementation for the highest-impact open engineering gaps you can substantiate. "
        "Do not assume issue descriptions are current. Do not edit files.\n\n"
        "Prioritize persistence/project activation, instrumentation/MeasurementChannel, protection/control integration, "
        "SLD/UI interaction and numerical correctness. Distinguish verified code defects from incomplete evidence and stale backlog. "
        "Return a prioritized report with exact repository-relative paths and symbols, dependencies, likely specialist ownership, "
        "and the next three bounded issue investigations. Identify duplicate/overlapping issue clusters and PRs that may already address them.\n\n"
        "Current open GitHub issues (number, title, labels):\n%s\n\n"
        "Current open pull requests (number, title, branch direction):\n%s"
        % (issue_index, pr_index)
    )
    report = run_agent(
        client=client,
        settings=settings,
        model=settings.planner_model,
        system_prompt=system_prompt(root, "coordinator"),
        user_prompt=prompt,
        root=root,
        writable=False,
        temperature=0.1,
    )
    stamp = datetime.now(timezone.utc).strftime("audit-%Y%m%d-%H%M%S")
    path = _save_report(stamp, {
        "kind": "repository_audit",
        "repository": str(root),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": settings.planner_model,
        "open_issue_count": len(open_issues),
        "open_pr_count": len(open_prs),
        "report": report,
    })
    client.unload(settings.planner_model)
    return report, path


def fetch_issue(repo: str, issue_number: int) -> dict[str, Any]:
    url = "https://api.github.com/repos/%s/issues/%d" % (repo, issue_number)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GridForge-Local-Agent-Workbench",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise WorkflowError("GitHub issue lookup failed (HTTP %s): %s" % (exc.code, detail)) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise WorkflowError("Could not reach GitHub to fetch issue #%d: %s" % (issue_number, exc)) from exc
    if "pull_request" in data:
        raise WorkflowError("#%d is a pull request, not an issue." % issue_number)
    return data


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result[:36] or "task"


def _parse_review(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end <= start:
        raise WorkflowError("Reviewer did not return the required JSON verdict. Changes were not committed.")
    try:
        result = json.loads(candidate[start:end + 1])
    except json.JSONDecodeError as exc:
        raise WorkflowError("Reviewer returned malformed JSON. Changes were not committed.") from exc
    if not isinstance(result, dict) or result.get("verdict") not in {"APPROVE", "REQUEST_CHANGES", "BLOCKED"}:
        raise WorkflowError("Reviewer verdict is missing or invalid. Changes were not committed.")
    return result


def _static_check(root: Path) -> str:
    runner = ToolRunner(root, writable=True)
    return runner.static_check()


def run_issue(
    root: Path,
    issue_number: int,
    settings: Settings,
    client: OllamaClient,
) -> dict[str, Any]:
    check_models(client, settings)
    ensure_tool_runtime(client, settings)
    issue = fetch_issue(settings.github_repo, issue_number)
    if issue.get("state") != "open":
        raise WorkflowError("Issue #%d is not open (state: %s)." % (issue_number, issue.get("state")))
    title = issue.get("title", "GridForge issue %d" % issue_number)
    body = issue.get("body") or "(No issue description supplied.)"
    domain = classify_issue(title, body)
    print("[ISSUE] #%d %s" % (issue_number, title), flush=True)
    print("[OWNER] %s" % domain, flush=True)

    print("[GIT] Fetching origin/main; active working tree will not be modified.", flush=True)
    run_git(root, ["fetch", "origin", "main"], timeout=180)
    base_sha = run_git(root, ["rev-parse", "origin/main"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch = "agents/ollama/issue-%d-%s" % (issue_number, stamp)
    worktree = application_data_dir() / "worktrees" / ("issue-%d-%s" % (issue_number, stamp))
    worktree.parent.mkdir(parents=True, exist_ok=True)
    run_git(root, ["worktree", "add", "-b", branch, str(worktree), "origin/main"], timeout=180)

    result: dict[str, Any] = {
        "kind": "issue_implementation",
        "issue": issue_number,
        "title": title,
        "issue_url": issue.get("html_url"),
        "domain_agent": domain,
        "base_sha": base_sha,
        "branch": branch,
        "worktree": str(worktree),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "started",
    }

    try:
        issue_context = (
            "GitHub issue #%d: %s\nURL: %s\nLabels: %s\n\nIssue description:\n%s\n\n"
            "Current base commit: %s\nAssigned domain specialist: %s\n\n"
            "First inspect current source, related docs and callers. Identify already-implemented parts and exact gaps. "
            "Produce a concrete plan with acceptance criteria and expected touched files. Do not edit."
            % (
                issue_number, title, issue.get("html_url", ""),
                ", ".join(label.get("name", "") for label in issue.get("labels", [])),
                body, base_sha, DOMAIN_GUIDANCE.get(domain, DOMAIN_GUIDANCE["general"]),
            )
        )
        print("[PLAN] Read-only issue analysis...", flush=True)
        plan = run_agent(
            client=client,
            settings=settings,
            model=settings.planner_model,
            system_prompt=system_prompt(worktree, "coordinator"),
            user_prompt=issue_context,
            root=worktree,
            writable=False,
        )
        result["plan"] = plan
        client.unload(settings.planner_model)

        implementation_prompt = (
            "Implement GitHub issue #%d in this isolated worktree.\n\nISSUE:\n%s\n\nDESCRIPTION:\n%s\n\n"
            "APPROVED EXECUTION PLAN:\n%s\n\nDOMAIN OWNERSHIP:\n%s\n\n"
            "You are authorized to edit files in this worktree without asking for confirmation. "
            "Do not modify .vscode settings, secrets, Git metadata, or files outside the issue scope. "
            "Do not push or merge. Inspect git status before editing and inspect the complete diff before finishing."
            % (issue_number, title, body, plan, DOMAIN_GUIDANCE.get(domain, DOMAIN_GUIDANCE["general"]))
        )
        print("[IMPLEMENT] %s using %s..." % (domain, settings.implementer_model), flush=True)
        implementation = run_agent(
            client=client,
            settings=settings,
            model=settings.implementer_model,
            system_prompt=system_prompt(worktree, "implementer") + "\n\nDomain owner: " + DOMAIN_GUIDANCE.get(domain, ""),
            user_prompt=implementation_prompt,
            root=worktree,
            writable=True,
            temperature=0.05,
        )
        result["implementation"] = implementation
        client.unload(settings.implementer_model)

        check = _static_check(worktree)
        result["static_check"] = check
        if "FAILED" in check:
            result["status"] = "static_check_failed"
            return result

        print("[REVIEW] Independent read-only review...", flush=True)
        review_text = run_agent(
            client=client,
            settings=settings,
            model=settings.reviewer_model,
            system_prompt=system_prompt(worktree, "reviewer"),
            user_prompt=(
                "Review the actual working tree for issue #%d.\nISSUE:\n%s\n\n"
                "Approved plan:\n%s\n\nImplementation summary (untrusted; verify against files):\n%s\n\n"
                "Static check result:\n%s\n\nInspect git status, git diff and affected files. Return the required JSON verdict only."
                % (issue_number, body, plan, implementation, check)
            ),
            root=worktree,
            writable=False,
            temperature=0.0,
        )
        review = _parse_review(review_text)
        result["review"] = review
        client.unload(settings.reviewer_model)

        if review["verdict"] == "REQUEST_CHANGES":
            print("[CORRECT] One bounded correction pass from reviewer findings...", flush=True)
            correction = run_agent(
                client=client,
                settings=settings,
                model=settings.implementer_model,
                system_prompt=system_prompt(worktree, "implementer") + "\n\nDomain owner: " + DOMAIN_GUIDANCE.get(domain, ""),
                user_prompt=(
                    "Address only the valid findings below for issue #%d. Re-read the affected source and verify each finding before editing. "
                    "Do not broaden scope.\n\nReviewer findings:\n%s\n\nAfter corrections inspect the full diff and run static_check."
                    % (issue_number, json.dumps(review.get("findings", []), indent=2))
                ),
                root=worktree,
                writable=True,
                temperature=0.05,
            )
            result["correction"] = correction
            client.unload(settings.implementer_model)
            result["static_check"] = _static_check(worktree)
            if "FAILED" not in result["static_check"]:
                review_text = run_agent(
                    client=client,
                    settings=settings,
                    model=settings.reviewer_model,
                    system_prompt=system_prompt(worktree, "reviewer"),
                    user_prompt=(
                        "Re-review issue #%d after one correction pass. Inspect the actual complete diff and files. "
                        "Previous findings:\n%s\nCorrection summary:\n%s\nStatic check:\n%s\n"
                        "Return the required JSON verdict only."
                        % (issue_number, json.dumps(review.get("findings", []), indent=2), correction, result["static_check"])
                    ),
                    root=worktree,
                    writable=False,
                    temperature=0.0,
                )
                review = _parse_review(review_text)
                result["review"] = review
                client.unload(settings.reviewer_model)

        if review["verdict"] != "APPROVE":
            result["status"] = "review_blocked"
            return result

        pending = run_git(worktree, ["status", "--porcelain"])
        if not pending:
            result["status"] = "no_changes"
            return result
        run_git(worktree, ["add", "-A"])
        diff = run_git(worktree, ["diff", "--cached", "--stat"])
        if not diff:
            result["status"] = "no_changes"
            return result
        run_git(worktree, ["commit", "-m", "fix(issue #%d): %s" % (issue_number, _slug(title))], timeout=180)
        result["commit"] = run_git(worktree, ["rev-parse", "HEAD"])
        result["diff_stat"] = diff
        result["status"] = "committed_local"
        print("[DONE] Local commit created on %s. No push, PR, merge or issue closure was performed." % branch, flush=True)
        return result
    finally:
        report_name = "issue-%d-%s" % (issue_number, stamp)
        result_path = _save_report(report_name, result)
        print("[REPORT] %s" % result_path, flush=True)
        print("[WORKTREE] %s" % worktree, flush=True)
