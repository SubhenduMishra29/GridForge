# ============================================================
# File: ui/core/action_router.py
# GridForge V2 — Canonical Presentation Action Router
# Author: Subhendu Mishra
# ============================================================
"""Single presentation routing boundary for non-tool UI actions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any


ActionHandler = Callable[[], Any]


class UIActionRouter:
    """Route presentation action identifiers to composition-owned handlers.

    The router owns no application/domain state and executes no engineering
    logic. Handlers are supplied by the composition root and must delegate to
    the canonical Controller/Application/Workspace boundaries.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}
        self._disposed = False
        self._enabled_provider: Callable[[str], bool] | None = None

    @property
    def actions(self) -> Mapping[str, ActionHandler]:
        return MappingProxyType(dict(self._handlers))

    def register(self, action_id: str, handler: ActionHandler) -> None:
        self._ensure_active()
        self._validate_action_id(action_id)
        if not callable(handler):
            raise TypeError("handler must be callable.")
        if action_id in self._handlers:
            raise ValueError(f"UI action already registered: {action_id!r}")
        self._handlers[action_id] = handler

    def register_many(self, handlers: Mapping[str, ActionHandler]) -> None:
        self._ensure_active()
        if not isinstance(handlers, Mapping):
            raise TypeError("handlers must be a mapping.")
        for action_id, handler in handlers.items():
            self._validate_action_id(action_id)
            if not callable(handler):
                raise TypeError(f"Handler for {action_id!r} must be callable.")
            if action_id in self._handlers:
                raise ValueError(f"UI action already registered: {action_id!r}")
        self._handlers.update(handlers)

    def require(self, action_id: str) -> ActionHandler:
        self._ensure_active()
        self._validate_action_id(action_id)
        handler = self._handlers.get(action_id)
        if handler is None:
            raise KeyError(f"No canonical UI action handler registered: {action_id!r}")
        return handler

    def dispatch(self, action_id: str) -> Any:
        if not self.is_enabled(action_id):
            raise RuntimeError(f"UI action is currently disabled: {action_id!r}")
        return self.require(action_id)()

    def set_enabled_provider(self, provider: Callable[[str], bool] | None) -> None:
        if provider is not None and not callable(provider):
            raise TypeError("provider must be callable or None.")
        self._enabled_provider = provider

    def is_enabled(self, action_id: str) -> bool:
        self._ensure_active()
        self._validate_action_id(action_id)
        if action_id not in self._handlers:
            return False
        if self._enabled_provider is None:
            return True
        try:
            return bool(self._enabled_provider(action_id))
        except (RuntimeError, TypeError, ValueError):
            return False

    def has(self, action_id: str) -> bool:
        return not self._disposed and isinstance(action_id, str) and action_id in self._handlers

    def dispose(self) -> None:
        self._handlers.clear()
        self._enabled_provider = None
        self._disposed = True

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("UIActionRouter has been disposed.")

    @staticmethod
    def _validate_action_id(action_id: str) -> None:
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError("action_id must be a non-empty string.")


__all__ = ["ActionHandler", "UIActionRouter"]
