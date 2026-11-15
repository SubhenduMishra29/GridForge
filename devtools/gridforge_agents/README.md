# GridForge Local Ollama Agent Workbench

A Python 3.10-compatible, VS Code-launched multi-agent workflow for inspecting and implementing GridForge GitHub issues with local Ollama models. It uses only the Python standard library; it does not install or change GridForge's application dependencies.

## Roles and model routing

The initial Windows profile uses one model at a time to fit the 8 GB RTX 4060 / 16 GB RAM development machine:

- Coordinator/planner: `qwen3:8b`
- Implementation: `qwen3:8b`
- Independent reviewer: `qwen3:8b`

The implementation model can be changed with `GRIDFORGE_CODER_MODEL` after its structured tool-calling behavior is verified. Qwen2.5-Coder 7B is not selected automatically because native tool-call reliability can vary by Ollama/model template.

## Setup on Windows

1. Install/update Ollama and start it.
2. Ensure the default model is installed:

   ```powershell
   ollama pull qwen3:8b
   ```

3. Open the GridForge repository folder in VS Code.
4. Run **Terminal → Run Task → GridForge Agents: Setup (Python 3.10)**.
5. Run **GridForge Agents: Doctor** and confirm `"status": "ready"`.

The runtime requires Ollama **0.3.0 or newer** for native tool calling. Doctor also sends a harmless structured-tool probe to each configured model; merely having a model installed is not enough.

No pip packages are required. The setup script creates `.venv-gridforge-agents` using the Python 3.10 launcher and sets `PYTHONPATH=devtools` for VS Code tasks.

## VS Code tasks

- **GridForge Agents: Doctor** — verifies Python/Git/Ollama/models/tool calling.
- **GridForge Agents: Read-only repository audit** — uses the coordinator to inspect current source and write a report under the user profile.
- **GridForge Agents: Implement GitHub issue** — prompts for an open issue number and runs the autonomous workflow.

CLI equivalents from the repository root:

```powershell
$env:PYTHONPATH = "$PWD\devtools"
.\.venv-gridforge-agents\Scripts\python.exe -m gridforge_agents doctor
.\.venv-gridforge-agents\Scripts\python.exe -m gridforge_agents audit
.\.venv-gridforge-agents\Scripts\python.exe -m gridforge_agents run --issue 1203
```

## Autonomous execution contract

For an issue run, the workbench:

1. Fetches the issue from the public GitHub API (or uses `GH_TOKEN` / `GITHUB_TOKEN` if supplied).
2. Fetches `origin/main` and creates a new branch plus Git worktree outside the repository's active working directory.
3. Runs a read-only planner, one domain-focused implementation agent, then an independent read-only reviewer.
4. Allows one bounded correction pass if the reviewer requests changes.
5. Runs `git diff --check` and Python `compileall` for changed Python files.
6. Creates a **local commit only** when the reviewer returns `APPROVE` and the static check passes.

It does not run the test suite or CI by default. It never pushes, creates a PR, merges, closes an issue, modifies remote branches, or edits the user's active worktree. Those actions remain explicit human operations.

## Isolation and guardrails

- Each issue gets a separate worktree under `%LOCALAPPDATA%\GridForgeAgent\worktrees`.
- Run reports are saved under `%LOCALAPPDATA%\GridForgeAgent\runs`.
- Model tools can list/search/read files, inspect Git status/diffs, and (for the implementation role only) write or replace text inside that worktree.
- Absolute paths, path traversal, Git metadata, virtual environments, secret files, caches and VS Code workspace settings are blocked.
- There is no arbitrary shell/PowerShell tool exposed to the model.
- A failed or interrupted run leaves the worktree and report available for manual inspection. It does not auto-delete partial work.
- Only one issue is implemented per invocation. Parallel issue implementation is deliberately deferred until file-overlap and memory limits are measured.

## Configuration

Environment overrides:

| Variable | Default |
|---|---|
| `GRIDFORGE_OLLAMA_URL` | `http://127.0.0.1:11434` |
| `GRIDFORGE_PLANNER_MODEL` | `qwen3:8b` |
| `GRIDFORGE_CODER_MODEL` | `qwen3:8b` |
| `GRIDFORGE_REVIEWER_MODEL` | `qwen3:8b` |
| `GRIDFORGE_CONTEXT_SIZE` | `8192` |
| `GRIDFORGE_MAX_TOOL_ROUNDS` | `24` |
| `GRIDFORGE_GITHUB_REPO` | `SubhenduMishra29/GridForge` |

## Current limitations

- The workbench has not been executed against the user's Windows/Ollama installation from GitHub; the first local Doctor run is required.
- GitHub issue retrieval requires network access. Public issue retrieval works without a token; a token is optional for private/rate-limited access.
- A successful local commit is not proof of engineering correctness. Inspect the report and diff, then push/create a PR manually when satisfied.
