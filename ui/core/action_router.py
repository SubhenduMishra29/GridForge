from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from ui.core.action_definition import ActionDefinition

ActionHandler = Callable[[], Any]


class UIActionRouter:
    """Single presentation routing boundary; no Core/domain ownership."""

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}
        self._definitions: dict[str, ActionDefinition] = {}
        self._aliases: dict[str, str] = {}
        self._disposed = False
        self._enabled_provider: Callable[[str], bool] | None = None

    @property
    def actions(self) -> Mapping[str, ActionHandler]:
        return MappingProxyType(dict(self._handlers))

    @property
    def definitions(self) -> Mapping[str, ActionDefinition]:
        return MappingProxyType(dict(self._definitions))

    def register(self, action_id: str, handler: ActionHandler) -> None:
        self._ensure_active()
        self._validate_action_id(action_id)
        if not callable(handler):
            raise TypeError("handler must be callable.")
        if action_id in self._handlers or action_id in self._aliases:
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
            if action_id in self._handlers or action_id in self._aliases:
                raise ValueError(f"UI action already registered: {action_id!r}")
        self._handlers.update(handlers)

    def register_definition(self, definition: ActionDefinition, handler: ActionHandler) -> None:
        if not isinstance(definition, ActionDefinition):
            raise TypeError("definition must be an ActionDefinition.")
        self.register(definition.action_id, handler)
        self._definitions[definition.action_id] = definition

    def set_definition(self, definition: ActionDefinition) -> None:
        """Attach immutable metadata to an already-registered routed action."""
        self._ensure_active()
        if not isinstance(definition, ActionDefinition):
            raise TypeError("definition must be an ActionDefinition.")
        canonical = self._canonical_id(definition.action_id)
        if canonical not in self._handlers:
            raise KeyError(f"Cannot define unknown UI action: {definition.action_id!r}")
        self._definitions[canonical] = definition

    def register_alias(self, alias: str, action_id: str) -> None:
        self._ensure_active()
        self._validate_action_id(alias)
        canonical = self._canonical_id(action_id)
        if canonical not in self._handlers:
            raise KeyError(f"Cannot alias unknown UI action: {action_id!r}")
        if alias in self._handlers or alias in self._aliases:
            raise ValueError(f"UI action already registered: {alias!r}")
        self._aliases[alias] = canonical

    def definition(self, action_id: str) -> ActionDefinition:
        self._ensure_active()
        definition = self._definitions.get(self._canonical_id(action_id))
        if definition is None:
            raise KeyError(f"No canonical UI action definition: {action_id!r}")
        return definition

    def require(self, action_id: str) -> ActionHandler:
        self._ensure_active()
        handler = self._handlers.get(self._canonical_id(action_id))
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
        canonical = self._canonical_id(action_id)
        if canonical not in self._handlers:
            return False
        if self._enabled_provider is None:
            definition = self._definitions.get(canonical)
            return True if definition is None else definition.enabled
        try:
            return bool(self._enabled_provider(action_id))
        except (RuntimeError, TypeError, ValueError):
            return False

    def has(self, action_id: str) -> bool:
        return not self._disposed and isinstance(action_id, str) and self._canonical_id(action_id) in self._handlers

    def dispose(self) -> None:
        self._handlers.clear()
        self._definitions.clear()
        self._aliases.clear()
        self._enabled_provider = None
        self._disposed = True

    def _canonical_id(self, action_id: str) -> str:
        self._validate_action_id(action_id)
        return self._aliases.get(action_id, action_id)

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("UIActionRouter has been disposed.")

    @staticmethod
    def _validate_action_id(action_id: str) -> None:
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError("action_id must be a non-empty string.")


__all__ = ["ActionHandler", "UIActionRouter"]
