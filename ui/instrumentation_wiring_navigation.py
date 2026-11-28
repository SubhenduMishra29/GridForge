"""Host-level navigation between SLD physical wiring and canonical signal consumers.

The navigator consumes Application endpoint-resolution read models and delegates
only presentation navigation/highlighting to the owning UI workspaces. It never
creates wiring records, changes Core topology, or treats unresolved bindings as
physical continuity.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
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
        activate_editor: Callable[[str], Any] | None = None,
        refresh_editor: Callable[[str], Any] | None = None,
        select_object: Callable[[str], Any] | None = None,
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
        for name, callback in (
            ("activate_editor", activate_editor),
            ("refresh_editor", refresh_editor),
            ("select_object", select_object),
        ):
            if callback is not None and not callable(callback):
                raise TypeError(f"{name} must be callable or None.")
        self._activate_editor = activate_editor
        self._refresh_editor = refresh_editor
        self._select_object = select_object

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


    def provenance_targets(self) -> dict[str, tuple[dict[str, Any], ...]]:
        """Return current, resolved consumers grouped by canonical signal identity."""
        identity = self._active_project_identity()
        if identity is None:
            return {}
        resolver = getattr(self._application, "resolve_instrumentation_signal_endpoints", None)
        if not callable(resolver):
            return {}
        try:
            resolutions = tuple(resolver())
        except Exception:
            return {}
        if self._active_project_identity() != identity:
            return {}

        project_id, generation = identity
        targets: dict[str, list[dict[str, Any]]] = {}
        for item in resolutions:
            if (
                str(getattr(item, "project_id", "")) != project_id
                or getattr(item, "activation_generation", None) != generation
                or str(getattr(item, "status", "")).upper() != "RESOLVED"
                or not tuple(getattr(item, "carrier_ids", ()) or ())
            ):
                continue
            endpoint_kind = str(getattr(item, "endpoint_kind", "")).upper()
            if endpoint_kind == "CONTROL_INPUT":
                target_editor = "control"
                target_object_id = str(getattr(item, "endpoint_id", "") or "").strip()
            elif endpoint_kind == "PROTECTION_INPUT":
                target_editor = "protection"
                target_object_id = str(getattr(item, "owner_id", "") or "").strip()
            else:
                continue

            signal_id = str(getattr(item, "signal_id", "") or "").strip()
            binding_id = str(getattr(item, "binding_id", "") or "").strip()
            owner_id = str(getattr(item, "owner_id", "") or "").strip()
            endpoint_id = str(getattr(item, "endpoint_id", "") or "").strip()
            port = str(getattr(item, "port", "") or "").strip()
            if not all((signal_id, binding_id, owner_id, endpoint_id, port, target_object_id)):
                continue
            carrier_ids = tuple(sorted({
                str(value).strip()
                for value in tuple(getattr(item, "carrier_ids", ()) or ())
                if isinstance(value, str) and value.strip()
            }))
            if not carrier_ids:
                continue
            label = (
                f"Control: {owner_id}.{port}"
                if target_editor == "control"
                else f"Protection: {owner_id}.{port}"
            )
            detail = (
                f"Signal {signal_id} | Binding {binding_id} | Endpoint {endpoint_id} | "
                f"Port {port} | Physical carriers: {', '.join(carrier_ids)}"
            )
            targets.setdefault(signal_id, []).append({
                "signal_id": signal_id,
                "binding_id": binding_id,
                "endpoint_kind": endpoint_kind,
                "endpoint_id": endpoint_id,
                "owner_id": owner_id,
                "port": port,
                "target_editor": target_editor,
                "target_object_id": target_object_id,
                "label": label,
                "detail": detail,
            })
        return {
            signal_id: tuple(sorted(
                entries,
                key=lambda item: (
                    item["target_editor"], item["owner_id"], item["port"], item["binding_id"]
                ),
            ))
            for signal_id, entries in targets.items()
        }

    def navigate_to_consumer(self, target: Mapping[str, Any]) -> WiringNavigationResult:
        """Revalidate one exact endpoint binding, then select it in its owning editor."""
        if not isinstance(target, Mapping):
            return WiringNavigationResult(False, "Signal consumer target is invalid.")
        required = (
            "signal_id", "binding_id", "endpoint_kind", "endpoint_id",
            "owner_id", "port", "target_editor", "target_object_id",
        )
        values = {key: str(target.get(key) or "").strip() for key in required}
        if any(not value for value in values.values()):
            return WiringNavigationResult(False, "Signal consumer target has incomplete identity.")
        expected_editor = {
            "CONTROL_INPUT": "control",
            "PROTECTION_INPUT": "protection",
        }.get(values["endpoint_kind"].upper())
        expected_object = (
            values["endpoint_id"]
            if expected_editor == "control"
            else values["owner_id"]
        )
        if (
            expected_editor is None
            or values["target_editor"] != expected_editor
            or values["target_object_id"] != expected_object
        ):
            return WiringNavigationResult(False, "Signal consumer target does not match its canonical endpoint kind.")
        if not callable(self._activate_editor) or not callable(self._select_object):
            return WiringNavigationResult(False, "Reverse SLD-to-consumer navigation is not configured.")

        identity = self._active_project_identity()
        if identity is None:
            return WiringNavigationResult(False, "Instrumentation wiring navigation requires an active project.")
        resolver = getattr(self._application, "resolve_instrumentation_signal_endpoints", None)
        if not callable(resolver):
            return WiringNavigationResult(False, "Application signal-endpoint resolution is unavailable.")
        try:
            resolutions = tuple(resolver())
        except Exception as exc:
            return WiringNavigationResult(False, f"Signal-endpoint revalidation failed closed: {exc}")
        if self._active_project_identity() != identity:
            return WiringNavigationResult(False, "The active project changed during endpoint revalidation.")

        selected = tuple(
            item for item in resolutions
            if str(getattr(item, "signal_id", "")) == values["signal_id"]
            and str(getattr(item, "binding_id", "")) == values["binding_id"]
            and str(getattr(item, "endpoint_kind", "")).upper() == values["endpoint_kind"].upper()
            and str(getattr(item, "endpoint_id", "")) == values["endpoint_id"]
            and str(getattr(item, "owner_id", "")) == values["owner_id"]
            and str(getattr(item, "port", "")) == values["port"]
        )
        if len(selected) != 1:
            return WiringNavigationResult(False, "The selected signal endpoint is missing or ambiguous; no editor was opened.")
        current = selected[0]
        if (
            str(getattr(current, "project_id", "")) != identity[0]
            or getattr(current, "activation_generation", None) != identity[1]
            or str(getattr(current, "status", "")).upper() != "RESOLVED"
            or not tuple(getattr(current, "carrier_ids", ()) or ())
        ):
            return WiringNavigationResult(False, "The selected physical signal path is no longer resolved; no editor was opened.")

        try:
            self._activate_editor(expected_editor)
            if self._active_project_identity() != identity:
                return WiringNavigationResult(False, "The active project changed while opening the consumer editor.")
            if callable(self._refresh_editor):
                self._refresh_editor(expected_editor)
            if self._active_project_identity() != identity:
                return WiringNavigationResult(False, "The active project changed while refreshing the consumer editor.")
            self._select_object(expected_object)
        except Exception as exc:
            return WiringNavigationResult(False, f"Could not navigate to the signal consumer: {exc}")
        return WiringNavigationResult(
            True,
            f"Opened {expected_editor.title()} endpoint {values['owner_id']}.{values['port']} "
            f"for signal {values['signal_id']}.",
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

        # Re-resolve after the SLD projection refresh so a wiring edit that
        # occurred during workspace activation cannot highlight an old route.
        try:
            current_resolutions = tuple(resolver())
        except Exception as exc:
            return WiringNavigationResult(
                False,
                f"Signal-endpoint revalidation failed closed: {exc}",
            )
        if self._active_project_identity() != identity:
            return WiringNavigationResult(
                False,
                "The active project changed during SLD route revalidation; no route was highlighted.",
            )
        current_selected = tuple(
            item
            for item in current_resolutions
            if str(getattr(item, "endpoint_kind", "")).upper() == endpoint_kind
            and (not owner_ids or str(getattr(item, "owner_id", "")) in owner_ids)
            and (not endpoint_ids or str(getattr(item, "endpoint_id", "")) in endpoint_ids)
        )
        if not current_selected or any(
            str(getattr(item, "project_id", "")) != project_id
            or getattr(item, "activation_generation", None) != generation
            for item in current_selected
        ):
            return WiringNavigationResult(
                False,
                "The selected endpoint changed project identity during SLD refresh; no route was highlighted.",
            )
        current_resolved = tuple(
            item
            for item in current_selected
            if str(getattr(item, "status", "")).upper() == "RESOLVED"
            and tuple(getattr(item, "carrier_ids", ()) or ())
        )
        unresolved_count = len(current_selected) - len(current_resolved)
        if not current_resolved:
            return WiringNavigationResult(
                False,
                "The selected physical path is no longer resolved after SLD refresh; no route was highlighted.",
            )
        signal_ids = frozenset(
            str(item.signal_id).strip()
            for item in current_resolved
            if isinstance(getattr(item, "signal_id", None), str)
            and str(item.signal_id).strip()
        )
        carrier_ids = frozenset(
            str(carrier_id).strip()
            for item in current_resolved
            for carrier_id in tuple(getattr(item, "carrier_ids", ()) or ())
            if isinstance(carrier_id, str) and carrier_id.strip()
        )
        terminal_point_ids = frozenset(
            str(sink.get("terminal_point_id")).strip()
            for item in current_resolved
            for sink in (getattr(item, "physical_sink_terminal", None),)
            if isinstance(sink, Mapping)
            and sink.get("terminal_point_id") is not None
            and str(sink.get("terminal_point_id")).strip()
        )
        signal_carrier_pairs = frozenset(
            (str(item.signal_id).strip(), str(carrier_id).strip())
            for item in current_resolved
            if isinstance(getattr(item, "signal_id", None), str)
            and str(item.signal_id).strip()
            for carrier_id in tuple(getattr(item, "carrier_ids", ()) or ())
            if isinstance(carrier_id, str) and carrier_id.strip()
        )
        if not signal_ids or not carrier_ids or not signal_carrier_pairs:
            return WiringNavigationResult(
                False,
                "Revalidated endpoint data contains no canonical signal/carrier identity; no route was highlighted.",
            )

        if not getattr(self._surface, "document_id", None):
            return WiringNavigationResult(
                False,
                "There is no active SLD document to display the resolved physical wiring.",
            )

        try:
            highlighted = tuple(
                self._surface.highlight_instrumentation_routes(
                    signal_carrier_pairs=signal_carrier_pairs,
                    terminal_point_ids=terminal_point_ids,
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
