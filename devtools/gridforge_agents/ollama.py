from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .config import Settings


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot complete a request."""


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.settings.ollama_url + path
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if data is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.request_timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaError("Ollama returned HTTP %s: %s" % (exc.code, detail)) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise OllamaError(
                "Cannot reach Ollama at %s. Start Ollama and verify its local API." % self.settings.ollama_url
            ) from exc
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama returned invalid JSON from %s." % path) from exc

    def installed_models(self) -> list[str]:
        result = self._request("/api/tags")
        return [item.get("name", "") for item in result.get("models", []) if item.get("name")]

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "2m",
            "options": {
                "temperature": temperature,
                "num_ctx": self.settings.context_size,
                "num_predict": 4096,
            },
        }
        if tools:
            payload["tools"] = tools
        return self._request("/api/chat", payload)

    def unload(self, model: str) -> None:
        try:
            self._request(
                "/api/generate",
                {"model": model, "prompt": "", "stream": False, "keep_alive": 0},
            )
        except OllamaError:
            # Unloading is best-effort; never hide the result of the agent task.
            pass
