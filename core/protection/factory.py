"""Canonical runtime construction boundary for protection functions."""

from __future__ import annotations

import inspect
from typing import Any, Mapping, get_type_hints

from .function_catalog import ProtectionFunctionStatus, get_protection_function
from .protection_element import ProtectionElement
from .relay_base import RelayBase


class ProtectionFactory:
    """Construct configured RelayBase/ProtectionElement compositions.

    Function selection is delegated exclusively to the canonical function
    catalog. The factory owns construction only; it does not become a second
    function registry or runtime orchestration system.
    """

    @staticmethod
    def _settings_type(implementation: type[RelayBase]) -> type[Any] | None:
        try:
            hints = get_type_hints(implementation.__init__)
        except (NameError, TypeError):
            hints = getattr(implementation.__init__, "__annotations__", {})
        candidate = hints.get("settings")
        return candidate if isinstance(candidate, type) else None

    @classmethod
    def _build_settings(cls, implementation: type[RelayBase], settings: Any) -> Any:
        if settings is None:
            raise ValueError(f"Protection function {implementation.__name__} requires settings.")
        if not isinstance(settings, Mapping):
            return settings
        settings_type = cls._settings_type(implementation)
        if settings_type is None:
            return dict(settings)
        try:
            return settings_type(**dict(settings))
        except TypeError as exc:
            raise ValueError(
                f"Invalid settings for {implementation.__name__}: {exc}"
            ) from exc

    @classmethod
    def create_element(
        cls,
        *,
        relay: Any,
        element_id: str,
        function_code: str,
        relay_inputs: Mapping[str, Any],
        settings: Any,
        enabled: bool = True,
        blocked: bool = False,
        name: str = "",
        priority: int = 0,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProtectionElement:
        spec = get_protection_function(function_code)
        if spec.status is not ProtectionFunctionStatus.IMPLEMENTED or spec.implementation is None:
            raise ValueError(f"Protection function {spec.code} is not implemented.")
        implementation = spec.implementation
        if not issubclass(implementation, RelayBase):
            raise TypeError(f"Catalog implementation for {spec.code} is not a RelayBase.")
        function_settings = cls._build_settings(implementation, settings)
        function = implementation(
            relay,
            element_id=element_id,
            relay_inputs=relay_inputs,
            settings=function_settings,
            enabled=enabled,
            blocked=blocked,
        )
        return ProtectionElement(
            id=element_id,
            relay=relay,
            function=function,
            function_type=spec.code,
            name=name or spec.name,
            enabled=enabled,
            priority=priority,
            metadata=metadata,
        )


__all__ = ["ProtectionFactory"]
