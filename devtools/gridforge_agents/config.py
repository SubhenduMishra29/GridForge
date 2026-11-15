from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ollama_url: str = "http://127.0.0.1:11434"
    planner_model: str = "qwen3:8b"
    implementer_model: str = "qwen3:8b"
    reviewer_model: str = "qwen3:8b"
    context_size: int = 8192
    max_tool_rounds: int = 24
    request_timeout: int = 300
    github_repo: str = "SubhenduMishra29/GridForge"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            ollama_url=os.getenv("GRIDFORGE_OLLAMA_URL", cls.ollama_url).rstrip("/"),
            planner_model=os.getenv("GRIDFORGE_PLANNER_MODEL", cls.planner_model),
            implementer_model=os.getenv("GRIDFORGE_CODER_MODEL", cls.implementer_model),
            reviewer_model=os.getenv("GRIDFORGE_REVIEWER_MODEL", cls.reviewer_model),
            context_size=int(os.getenv("GRIDFORGE_CONTEXT_SIZE", str(cls.context_size))),
            max_tool_rounds=int(os.getenv("GRIDFORGE_MAX_TOOL_ROUNDS", str(cls.max_tool_rounds))),
            request_timeout=int(os.getenv("GRIDFORGE_REQUEST_TIMEOUT", str(cls.request_timeout))),
            github_repo=os.getenv("GRIDFORGE_GITHUB_REPO", cls.github_repo),
        )


def application_data_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home()
    path = base / "GridForgeAgent"
    path.mkdir(parents=True, exist_ok=True)
    return path
