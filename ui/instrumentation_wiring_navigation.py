"""Host-level navigation from Control/Protection inputs to canonical SLD wiring.

The navigator consumes Application endpoint-resolution read models and delegates
only presentation navigation/highlighting to the existing SLD workspace. It
never creates wiring records, changes Core topology, or treats unresolved
bindings as physical continuity.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class WiringNavigationResult:
    """Outcome of one read-only cross-canvas wiring navigation request."""

    success: bool
    message: str
    highlighted_segments: int = 0


class InstrumentationWiringNavigator:
    """Navigate exact resolved Control/Protection inputs to SLD route segments."""

    def __init__(
        self,
        *,
        application: Any,
        activate_sld: Callable[[], Any],
        refresh_sld: Callable[[], Any],
        surface: Any,
    ) -> None:
        if application is None:
            raise ValueError("application is required.")
        if not callable(activate_sld):
            raise TypeError("activate_sld must be callable.")
        if not callable(refresh_sld):
            raise TypeError("refresh_sld must be callable.")
        if surface is None or not callable(
            getattr(surface, "highlight_instrumentation_routes", None)
        ):
            raise TypeError("surface must expose highlight_instrumentation_routes().")
        self._application = application
        self._activate_sld = activate_sld
        self._refresh_sld = refresh_sld
        self._surface = surface

    def locate_control_component(self, component_id: str) -> WiringNavigationResult:
        """Locate all resolved physical signal paths terminating at a Control component."""
        endpoint_ids = self._normalize_ids(component_id)
        if not endpoint_ids:
            return WiringNavigationResult(False, "Select a Control component first.")
        return self._locate(
            endpoint_kind="CONTROL_INPUT",
            endpoint_ids=endpoint_ids,
        )

    def locate_protection_elements(
        self,
        element_ids: Iterable[str],
    ) -> WiringNavigationResult:
        """Locate resolved physical signal paths terminating at Protection elements."""
        owner_ids = self._normalize_ids(element_ids)
        if not owner_ids:
            return WiringNavigationResult(False, "Select a Protection element or Relay first.")
        return self._locate(
            endpoint_kind="PROTECTION_INPUT",
            owner_ids=owner_ids,
        )

    def _locate(
        self,
        *,
        endpoint_kind: str,
        owner_ids: frozenset[str] = frozenset(),
        endpoint_ids: frozenset[str] = frozenset(),
    ) -> WiringNavigationResult:
        identity = self._active_project_identity()
        if identity is None:
            return WiringNavigationResult(
                False,
                "Instrumentation wiring navigation requires an active project.",
            )
        project_id, generation = identity

        resolver = getattr(
            self._application,
            "resolve_instrumentation_signal_endpoints",
            None,
        )
        if not callable(resolver):
            return WiringNavigationResult(
                False,
                "Application signal-endpoint resolution is unavailable.",
            )
        try:
            resolutions = tuple(resolver())
        except Exception as exc:
            return WiringNavigationResult(
                False,
                f"Signal-endpoint resolution failed closed: {exc}",
            )

        if self._active_project_identity() != identity:
            return WiringNavigationResult(
                False,
                "The active project changed during endpoint resolution; refresh and retry.",
            )

        selected = tuple(
            item
            for item in resolutions
            if str(getattr(item, "endpoint_kind", "")).upper() == endpoint_kind
            and (not owner_ids or str(getattr(item, "owner_id", "")) in owner_ids)
            and (not endpoint_ids or str(getattr(item, "endpoint_id", "")) in endpoint_ids)
        )
        if not selected:
            return WiringNavigationResult(
                False,
                "No canonical signal endpoint binding is declared for this selection.",
            )

        if any(
            str(getattr(item, "project_id", "")) != project_id
            or getattr(item, "activation_generation", None) != generation
            for item in selected
        ):
            return WiringNavigationResult(
                False,
                "Endpoint resolution belongs to a different project activation; no route was highlighted.",
            )

        resolved = tuple(
            item
            for item in selected
            if str(getattr(item, "status", "")).upper() == "RESOLVED"
            and tuple(getattr(item, "carrier_ids", ()) or ())
        )
        unresolved_count = len(selected) - len(resolved)
        if not resolved:
            statuses = sorted({str(getattr(item, "status", "UNKNOWN")) for item in selected})
            status_text = ", ".join(statuses) if statuses else "UNRESOLVED"
            return WiringNavigationResult(
                False,
                f"No resolved physical path is available for this selection ({status_text}); no SLD route was highlighted.",
            )

        signal_ids = frozenset(
            str(item.signal_id).strip()
            for item in resolved
            if isinstance(getattr(item, "signal_id", None), str)
            and str(item.signal_id).strip()
        )
        carrier_ids = frozenset(
            str(carrier_id).strip()
            for item in resolved
            for carrier_id in tuple(getattr(item, "carrier_ids", ()) or ())
            if isinstance(carrier_id, str) and carrier_id.strip()
        )
        if not signal_ids or not carrier_ids:
            return WiringNavigationResult(
                False,
                "Resolved endpoint data contains no canonical signal/carrier identity; no SLD route was highlighted.",
            )

        try:
            self._activate_sld()
            self._refresh_sld()
        except Exception as exc:
            return WiringNavigationResult(
                False,
                f"Could not activate and refresh the canonical SLD workspace: {exc}",
            )

        if self._active_project_identity() != identity:
            return WiringNavigationResult(
                False,
                "The active project changed before SLD highlighting; no route was highlighted.",
            )
        if not getattr(self._surface, "document_id", None):
            return WiringNavigationResult(
                False,
                "There is no active SLD document to display the resolved physical wiring.",
            )

        try:
            highlighted = tuple(
                self._surface.highlight_instrumentation_routes(
                    signal_ids=signal_ids,
                    carrier_ids=carrier_ids,
                )
            )
        except Exception as exc:
            return WiringNavigationResult(
                False,
                f"SLD route highlighting failed: {exc}",
            )
        if not highlighted:
            return WiringNavigationResult(
                False,
                "No visible SLD physical route segments match the resolved signal and carrier identities.",
            )

        message = (
            f"Located {len(highlighted)} SLD physical wiring segment(s) "
            f"across {len(carrier_ids)} carrier(s) for {len(signal_ids)} signal(s)."
        )
        if unresolved_count:
            message += (
                f" {unresolved_count} unresolved or ambiguous endpoint(s) "
                "were excluded from highlighting."
            )
        return WiringNavigationResult(True, message, len(highlighted))

    def _active_project_identity(self) -> tuple[str, int] | None:
        lifecycle = getattr(self._application, "project_lifecycle", None)
        context = getattr(lifecycle, "context", None)
        if (
            lifecycle is None
            or getattr(lifecycle, "state", None) != "ACTIVE"
            or not bool(getattr(lifecycle, "has_project", False))
            or context is None
        ):
            return None
        project_id = getattr(context, "project_id", None)
        generation = getattr(lifecycle, "activation_generation", None)
        if (
            not isinstance(project_id, str)
            or not project_id.strip()
            or isinstance(generation, bool)
            or not isinstance(generation, int)
            or generation < 1
        ):
            return None
        return project_id.strip(), generation

    @staticmethod
    def _normalize_ids(values: Iterable[str] | str | None) -> frozenset[str]:
        if values is None:
            return frozenset()
        if isinstance(values, str):
            values = (values,)
        return frozenset(
            value.strip()
            for value in values
            if isinstance(value, str) and value.strip()
        )


__all__ = ["InstrumentationWiringNavigator", "WiringNavigationResult"]
