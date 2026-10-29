# ============================================================
# GridForge V2 — Study Projection
# ============================================================
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Mapping
import logging
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Callable
from uuid import UUID

from core.application.revision import ProjectRevision

_LOGGER = logging.getLogger(__name__)

from core.application.events import (
    ElementCreated,
    ElementRemoved,
    ElementUpdated,
    NetworkCommitted,
    NetworkChanged,
    ProtectionChanged,
    ProjectClosed,
    ProjectLoaded,
    SLDPresentationChanged,
    TopologyChanged,
    StudyCancelled,
    StudyCaseCreated,
    StudyCompleted,
    StudyFailed,
    StudyStarted,
)


@dataclass(frozen=True, slots=True)
class StudyCaseRow:
    """Immutable presentation row retaining Study Case identity separately from display text."""

    study_id: UUID
    display_name: str
    study_type: str
    status: str
    current: bool = True
    message: str = ""


def _flatten_result_value(
    value: Any,
    *,
    prefix: str = "value",
    depth: int = 0,
    max_depth: int = 4,
    budget: list[int] | None = None,
) -> list[str]:
    """Format bounded result data for display without changing its engineering value."""
    if budget is None:
        budget = [80]
    if budget[0] <= 0:
        return []
    budget[0] -= 1

    if value is None or isinstance(value, (bool, int, float, complex, str)):
        rendered = repr(value) if isinstance(value, str) else str(value)
        return [f"{prefix}: {rendered}"]

    if depth >= max_depth:
        return [f"{prefix}: {value!r}"]

    if isinstance(value, Mapping):
        if not value:
            return [f"{prefix}: {{}}"]
        output: list[str] = []
        for key, item in value.items():
            output.extend(_flatten_result_value(
                item, prefix=f"{prefix}.{key}", depth=depth + 1,
                max_depth=max_depth, budget=budget,
            ))
            if budget[0] <= 0:
                break
        return output

    if is_dataclass(value) and not isinstance(value, type):
        output = []
        for item in fields(value):
            try:
                field_value = getattr(value, item.name)
            except Exception:
                continue
            output.extend(_flatten_result_value(
                field_value, prefix=f"{prefix}.{item.name}", depth=depth + 1,
                max_depth=max_depth, budget=budget,
            ))
            if budget[0] <= 0:
                break
        return output or [f"{prefix}: {type(value).__name__} (no fields)"]

    if isinstance(value, (tuple, list, set, frozenset)):
        values = tuple(value)
        if not values:
            return [f"{prefix}: []"]
        output = []
        for index, item in enumerate(values[:20]):
            output.extend(_flatten_result_value(
                item, prefix=f"{prefix}[{index}]", depth=depth + 1,
                max_depth=max_depth, budget=budget,
            ))
            if budget[0] <= 0:
                break
        if len(values) > 20:
            output.append(f"{prefix}: … {len(values) - 20} additional items omitted")
        return output

    # Numerical libraries may expose array-like results without being imported
    # into the UI layer. Convert only through their public value conversion API.
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        try:
            return _flatten_result_value(
                tolist(), prefix=prefix, depth=depth + 1,
                max_depth=max_depth, budget=budget,
            )
        except Exception:
            pass

    return [f"{prefix}: {value!r}"]


def _result_lines(result: Any) -> tuple[str, ...]:
    """Build a bounded read-only summary for the selected Study Result."""
    lines = [
        f"Study type: {result.study_type}",
        f"Status: {result.status}",
        f"Freshness: {'CURRENT' if result.current else 'STALE'}",
        f"Project: {result.project_id}",
        f"Source revision: {result.source_revision}",
    ]
    if result.message:
        lines.append(f"Message: {result.message}")
    if result.metadata:
        lines.extend(_flatten_result_value(result.metadata, prefix="metadata"))
    if result.value is None:
        lines.append("value: no numerical payload was published")
    else:
        lines.extend(_flatten_result_value(result.value))
    return tuple(lines)


class StudyProjection:
    """Project Application-owned study lifecycle and results into the Study Cases UI."""

    event_types = (
        ProjectLoaded,
        ProjectClosed,
        ElementCreated,
        ElementRemoved,
        ElementUpdated,
        NetworkCommitted,
        StudyStarted,
        StudyCompleted,
        StudyFailed,
        StudyCancelled,
        StudyCaseCreated,
        NetworkChanged,
        TopologyChanged,
        ProtectionChanged,
        SLDPresentationChanged,
    )

    def __init__(
        self,
        *,
        application: Any,
        panel: Any,
        result_changed: Callable[[Any | None], object] | None = None,
    ) -> None:
        if application is None or not callable(getattr(application, "read_study_result", None)):
            raise TypeError("application must provide read_study_result().")
        if panel is None or not callable(getattr(panel, "set_cases", None)):
            raise TypeError("panel must provide set_cases().")
        if result_changed is not None and not callable(result_changed):
            raise TypeError("result_changed must be callable or None.")
        self._application = application
        self._panel = panel
        self._result_changed = result_changed
        self._cases: tuple[StudyCaseRow, ...] = ()
        self._active: dict[str, dict[str, str]] = {}
        self._results: dict[UUID, Any] = {}
        self._selected_study_id: UUID | None = None
        self._disposed = False
        bind_selection = getattr(panel, "set_result_selection_handler", None)
        if callable(bind_selection):
            bind_selection(self.select_result)
        self._refresh_all_results()
        self._render()

    @property
    def cases(self) -> tuple[StudyCaseRow, ...]:
        return self._cases

    def refresh(self, event: Any) -> None:
        if self._disposed:
            return
        if isinstance(event, ProjectClosed):
            self._active.clear()
            self._results.clear()
            self._cases = ()
            self._selected_study_id = None
            self._panel.set_cases(())
            self._show_empty_result()
            return

        if isinstance(event, ProjectLoaded):
            self._active.clear()
            self._results.clear()
            self._selected_study_id = None
            self._refresh_all_results()
            self._render()
            if not self._cases:
                self._show_empty_result()
            return

        if isinstance(event, StudyCaseCreated):
            self._refresh_all_results()
            self._render()
            payload = getattr(event, "payload", {})
            study_id = payload.get("study_id") if hasattr(payload, "get") else None
            try:
                case_id = UUID(str(study_id))
            except (TypeError, ValueError):
                return
            select_case = getattr(self._panel, "select_case", None)
            if callable(select_case):
                select_case(case_id)
            return

        if isinstance(event, (
            ElementCreated,
            ElementRemoved,
            ElementUpdated,
            NetworkCommitted,
            NetworkChanged,
            TopologyChanged,
            ProtectionChanged,
            SLDPresentationChanged,
        )):
            # Invalidate the selected result projection on both granular Core
            # mutation events and aggregate revision events. Event families can
            # differ by command path; relying on NetworkChanged alone can leave
            # a formerly-current result overlay visible after a committed edit.
            self._refresh_all_results()
            self._render()
            if self._selected_study_id is not None:
                # Refreshing the cache alone is insufficient: the canvas owns
                # only a projection of the last callback payload. Re-select the
                # same result identity so current/stale status is re-evaluated
                # and the SLD overlay is explicitly replaced or cleared.
                self.select_result(self._selected_study_id)
            elif not self._cases:
                self._show_empty_result()
            return

        payload = getattr(event, "payload", {})
        study_id = payload.get("study_id") if hasattr(payload, "get") else None
        study_type = payload.get("study_type") if hasattr(payload, "get") else None
        if study_id is None:
            return

        status = event.event_type.rsplit(".", 1)[-1]
        entry = {
            "study_id": str(study_id),
            "study_type": str(study_type or "study"),
            "status": status,
        }
        if status == "started":
            # Do not leave a previous successful run projected while a rerun
            # is in progress. The stored historical result may remain readable,
            # but it must not be presented as the output of this execution.
            try:
                started_id = UUID(str(study_id))
            except (TypeError, ValueError):
                return
            self._results.pop(started_id, None)
        if status in {"completed", "failed", "cancelled"}:
            try:
                result = self._application.read_study_result(UUID(str(study_id)))
            except (TypeError, ValueError):
                result = None
            if result is not None:
                result_id = result.study_id
                self._results[result_id] = result
                entry["study_type"] = str(result.study_type)
                entry["status"] = str(result.status)
                entry["current"] = "true" if bool(getattr(result, "current", False)) else "false"
                if getattr(result, "message", ""):
                    entry["message"] = str(result.message)
        self._active[str(study_id)] = entry
        self._render()
        if status == "started" and self._selected_study_id == UUID(str(study_id)):
            self.select_result(self._selected_study_id)
            return
        # A completed run is immediately inspectable, while subsequent selection
        # remains authoritative for which result is shown.
        if status in {"completed", "failed", "cancelled"} and self._selected_study_id is None:
            try:
                self.select_result(UUID(str(study_id)))
            except (TypeError, ValueError):
                self._show_empty_result()

    def _refresh_all_results(self) -> None:
        """Reload active Study Cases and project-scoped results after mutations."""
        read_network = getattr(self._application, "read_network", None)
        set_available_buses = getattr(self._panel, "set_available_buses", None)
        if callable(read_network) and callable(set_available_buses):
            try:
                network = read_network()
                set_available_buses(
                    element.object_id
                    for element in getattr(network, "elements", ())
                    if str(getattr(element, "element_type", "")).strip().lower() == "bus"
                )
            except Exception:
                _LOGGER.exception("Study Case Bus choices could not be refreshed")

        try:
            cases = tuple(getattr(self._application, "study_cases", ()))
            revision = getattr(self._application, "revision", None)
        except Exception:
            _LOGGER.exception("Study Case read-model refresh failed")
            cases = ()
            revision = None

        for case in cases:
            case_id = getattr(case, "study_id", None)
            if not isinstance(case_id, UUID):
                continue
            source_revision = getattr(case, "source_revision", None)
            current = (
                isinstance(source_revision, ProjectRevision)
                and source_revision.matches_study_state(revision)
            )
            existing = self._active.get(str(case_id), {})
            status = "started" if existing.get("status") == "started" else "ready"
            self._active[str(case_id)] = {
                "study_id": str(case_id),
                "study_type": str(getattr(case, "study_type", "study")),
                "status": status,
                "current": "true" if current else "false",
                "message": (
                    "Study Case configuration was created against an earlier project revision."
                    if not current else ""
                ),
            }

        reader = getattr(self._application, "read_study_results", None)
        if not callable(reader):
            return
        try:
            results = tuple(reader())
        except Exception:
            _LOGGER.exception("Study result read-model refresh failed")
            return

        self._results.clear()
        for result in results:
            result_id = getattr(result, "study_id", None)
            if not isinstance(result_id, UUID):
                continue
            self._results[result_id] = result
            # A refresh during a rerun may still read the previous completed
            # result from Application storage. Preserve the in-flight state
            # until this execution publishes its terminal lifecycle event.
            existing = self._active.get(str(result_id), {})
            if existing.get("status") == "started":
                continue
            study_type = str(getattr(result, "study_type", "study"))
            status = str(getattr(result, "status", "unknown"))
            self._active[str(result_id)] = {
                "study_id": str(result_id),
                "study_type": study_type,
                "status": status,
                "current": "true" if bool(getattr(result, "current", False)) else "false",
                "message": str(getattr(result, "message", "") or ""),
            }

    def select_result(self, study_id: UUID | None) -> None:
        """Display the result associated with the selected Study Case identity."""
        self._selected_study_id = study_id
        if study_id is None:
            self._show_empty_result()
            return
        active_entry = self._active.get(str(study_id), {})
        if active_entry.get("status") == "started":
            self._set_result_details(
                "Study In Progress",
                (
                    f"Study type: {active_entry.get('study_type', 'study')}",
                    "A new execution is running; the previous numerical result is not current for this run.",
                ),
            )
            self._notify_result_changed(None)
            return
        result = self._results.get(study_id)
        if result is None:
            try:
                result = self._application.read_study_result(study_id)
            except (TypeError, ValueError):
                result = None
            if result is not None:
                self._results[study_id] = result
        if result is None:
            self._set_result_details("Study Result", ("No result has been published for this study.",))
            self._notify_result_changed(None)
            return
        title = f"{result.study_type.replace('_', ' ').title()} Result"
        lines = _result_lines(result)
        self._set_result_details(title, lines)
        # Numerical overlays are valid only for a completed, current result whose
        # solver explicitly reports success when that contract is available.
        # Keep historical result details inspectable, but never project failed,
        # cancelled, stale, or explicitly non-converged numerical values onto SLD.
        solver_success = getattr(result.value, "success", None)
        overlay_result = (
            result
            if str(getattr(result, "status", "")).strip().lower() == "completed"
            and bool(getattr(result, "current", False))
            and solver_success is not False
            else None
        )
        self._notify_result_changed(overlay_result)

    def _set_result_details(self, title: str, lines: tuple[str, ...]) -> None:
        setter = getattr(self._panel, "set_result_details", None)
        if callable(setter):
            setter(title, lines)

    def _show_empty_result(self) -> None:
        self._set_result_details("Study Results", ("Select a completed study to inspect its results.",))
        self._notify_result_changed(None)

    def _notify_result_changed(self, result: Any | None) -> None:
        if self._result_changed is None:
            return
        try:
            self._result_changed(result)
        except Exception:
            # SLD overlay refresh is an independent projection. A rendering
            # failure must not hide the result details already shown in-panel.
            _LOGGER.exception("Study result overlay refresh failed")

    def _render(self) -> None:
        rows: list[StudyCaseRow] = []
        for entry in self._active.values():
            study_id = UUID(str(entry["study_id"]))
            study_type = str(entry["study_type"])
            display_name = f"{study_type.replace('_', ' ').title()} Study"
            try:
                case = self._application.study_case(study_id)
            except (KeyError, TypeError, ValueError):
                case = None
            if case is not None:
                display_name = case.display_name
                study_type = case.study_type
            rows.append(
                StudyCaseRow(
                    study_id=study_id,
                    display_name=display_name,
                    study_type=study_type,
                    status=str(entry["status"]),
                    current=entry.get("current", "true") == "true",
                    message=str(entry.get("message") or ""),
                )
            )
        self._cases = tuple(rows)
        self._panel.set_cases(self._cases)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._active.clear()
        self._results.clear()
        self._cases = ()
        self._selected_study_id = None
        self._panel.set_cases(())
        self._show_empty_result()
        self._disposed = True


__all__ = ["StudyCaseRow", "StudyProjection"]
