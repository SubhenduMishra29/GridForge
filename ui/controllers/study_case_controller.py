# ============================================================
# File: ui/controllers/study_case_controller.py
# GridForge V2 — Study Case Interaction Boundary
# Author: Subhendu Mishra
# ============================================================

"""UI interaction boundary for creating and running Application-owned Study Cases."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math
from uuid import UUID
from threading import RLock
from typing import Any

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.analysis.transient_stability import TransientStabilityStudyConfiguration
from core.solver.short_circuit.fault_types import FaultType


@dataclass(frozen=True, slots=True)
class StudySubmission:
    """Study identity plus its asynchronous Application Future."""

    study_id: UUID
    future: Any


class StudyCaseController:
    """Translate Study Case UI intent into the Application study boundary."""

    def __init__(self, *, application: Any, error_handler: Callable[[BaseException], object] | None = None) -> None:
        if application is None:
            raise ValueError("application is required.")
        if not callable(getattr(application, "study_case", None)):
            raise TypeError("application must expose study_case().")
        if not callable(getattr(application, "submit_study_case", None)):
            raise TypeError("application must expose submit_study_case().")
        self._application = application
        self._error_handler = error_handler
        self._active_scopes: dict[UUID, tuple[str, int]] = {}
        self._scope_lock = RLock()

    def _track_submission(self, study_id: UUID, project_id: str, activation_generation: int, future: Any) -> Any:
        scope = (project_id, activation_generation)
        with self._scope_lock:
            self._active_scopes[study_id] = scope

        def _release_scope(_completed: object) -> None:
            with self._scope_lock:
                if self._active_scopes.get(study_id) == scope:
                    self._active_scopes.pop(study_id, None)

        future.add_done_callback(_release_scope)
        return future

    def run_study(self, study_id: UUID) -> object | None:
        """Run the selected structured Study Case through Application only."""
        if not isinstance(study_id, UUID):
            try:
                study_id = UUID(str(study_id))
            except (TypeError, ValueError) as exc:
                return self._handle_error(ValueError("Selected Study Case identity is invalid."), cause=exc)
        try:
            case = self._application.study_case(study_id)
            future = self._application.submit_study_case(study_id)
            return self._track_submission(study_id, case.project_id, case.activation_generation, future)
        except Exception as exc:
            with self._scope_lock:
                self._active_scopes.pop(study_id, None)
            return self._handle_error(exc)

    def run_draft_study(
        self,
        study_type: str,
        display_name: str,
        slack_bus_id: str,
        pv_bus_ids: Iterable[str],
        base_mva_text: str,
        fault_bus_id: str,
        fault_type: str,
        fault_resistance_text: str,
        fault_reactance_text: str,
        end_time_text: str,
        dt_text: str,
    ) -> StudySubmission | None:
        """Run PF/SC against an immutable active DraftNetwork snapshot."""
        try:
            normalized_type = str(study_type).strip().lower()
            if normalized_type not in {"power_flow", "short_circuit"}:
                raise ValueError("Draft studies support Power Flow and Short-Circuit only.")
            configuration = self._build_configuration(
                normalized_type,
                slack_bus_id,
                pv_bus_ids,
                base_mva_text,
                fault_bus_id,
                fault_type,
                fault_resistance_text,
                fault_reactance_text,
                end_time_text,
                dt_text,
                include_draft=True,
            )
            create_request = getattr(self._application, "create_draft_study_request", None)
            submit = getattr(self._application, "submit_study", None)
            if not callable(create_request) or not callable(submit):
                raise RuntimeError("Application draft-study execution boundary is unavailable.")
            request = create_request(
                study_type=normalized_type,
                configuration={"configuration": configuration},
            )
            future = submit(request)
            self._track_submission(request.study_id, request.project_id, request.activation_generation, future)
            return StudySubmission(request.study_id, future)
        except Exception as exc:
            return self._handle_error(exc)

    def cancel_study(self, study_id: UUID) -> bool:
        """Cancel using the exact project activation captured at submission."""
        with self._scope_lock:
            scope = self._active_scopes.get(study_id)
        if scope is None:
            return False
        project_id, activation_generation = scope
        try:
            return bool(self._application.cancel_study(
                study_id, project_id=project_id,
                activation_generation=activation_generation,
            ))
        except Exception as exc:
            self._handle_error(exc)
            return False

    def handle_async_error(self, error: BaseException) -> None:
        """Surface worker failures from the panel's Qt-thread Future poll."""
        if self._error_handler is not None:
            self._error_handler(error)

    def export_study_comparison(
        self, left_source: str, left_record_id: UUID | str,
        right_source: str, right_record_id: UUID | str,
    ) -> str:
        """Request a live/archive Study comparison export through Application."""
        try:
            left_id = left_record_id if isinstance(left_record_id, UUID) else UUID(str(left_record_id))
            right_id = right_record_id if isinstance(right_record_id, UUID) else UUID(str(right_record_id))
        except (TypeError, ValueError) as exc:
            return self._handle_error(ValueError("Selected Study execution identity is invalid."), cause=exc)
        if (
            not isinstance(left_source, str) or left_source not in {"live", "archive"}
            or not isinstance(right_source, str) or right_source not in {"live", "archive"}
        ):
            return self._handle_error(ValueError("Selected Study execution source is invalid."))
        try:
            export = getattr(self._application, "export_study_comparison", None)
            if not callable(export):
                raise RuntimeError("Application unified Study comparison export is unavailable.")
            payload = export(left_source, left_id, right_source, right_id)
            if not isinstance(payload, str) or not payload:
                raise RuntimeError("Application returned an empty Study comparison export.")
            return payload
        except Exception as exc:
            return self._handle_error(exc)

    def _committed_bus_ids(self) -> tuple[str, ...]:
        read_network = getattr(self._application, "read_network", None)
        if not callable(read_network):
            raise TypeError("application must expose read_network().")
        snapshot = read_network()
        return tuple(sorted(
            str(element.object_id)
            for element in getattr(snapshot, "elements", ())
            if str(getattr(element, "element_type", "")).strip().lower() == "bus"
            and str(getattr(element, "object_id", "")).strip()
        ))

    def available_bus_ids(self) -> tuple[str, ...]:
        """Return committed and deterministic active Draft Bus identities for the panel."""
        reader = getattr(self._application, "read_study_bus_ids", None)
        if callable(reader):
            return tuple(reader(include_draft=True))
        return self._committed_bus_ids()

    @staticmethod
    def _positive_finite(value: object, label: str) -> float:
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be entered as a number.") from exc
        if not math.isfinite(parsed) or parsed <= 0.0:
            raise ValueError(f"{label} must be finite and greater than zero.")
        return parsed

    def _build_configuration(
        self,
        study_type: str,
        slack_bus_id: str,
        pv_bus_ids: Iterable[str],
        base_mva_text: str,
        fault_bus_id: str,
        fault_type: str,
        fault_resistance_text: str,
        fault_reactance_text: str,
        end_time_text: str,
        dt_text: str,
        *,
        include_draft: bool,
    ) -> object:
        bus_ids = self.available_bus_ids() if include_draft else self._committed_bus_ids()
        if not bus_ids:
            raise ValueError("The selected study input network has no Bus objects.")
        bus_set = set(bus_ids)
        if study_type == "power_flow":
            slack_id, pv_ids = self._operating_point(bus_set, slack_bus_id, pv_bus_ids)
            return PowerFlowStudyConfiguration.from_mapping(
                {bus_id: "SLACK" if bus_id == slack_id else "PV" if bus_id in pv_ids else "PQ" for bus_id in bus_ids},
                base_mva=self._positive_finite(base_mva_text, "System base MVA"),
            )
        if study_type == "short_circuit":
            fault_bus = str(fault_bus_id).strip()
            if fault_bus not in bus_set:
                raise ValueError("Select a valid fault Bus from the selected study input network.")
            try:
                resistance = float(str(fault_resistance_text).strip())
                reactance = float(str(fault_reactance_text).strip())
            except (TypeError, ValueError) as exc:
                raise ValueError("Fault resistance and reactance must be numbers.") from exc
            if not math.isfinite(resistance) or not math.isfinite(reactance):
                raise ValueError("Fault resistance and reactance must be finite.")
            return ShortCircuitStudyConfiguration(
                fault_type=FaultType.from_value(fault_type),
                fault_bus_id=fault_bus,
                fault_impedance=complex(resistance, reactance),
                base_mva=self._positive_finite(base_mva_text, "System base MVA"),
            )
        if study_type == "transient_stability":
            if include_draft:
                raise ValueError("Draft studies do not support Transient Stability.")
            slack_id, pv_ids = self._operating_point(bus_set, slack_bus_id, pv_bus_ids)
            initial_pf = PowerFlowStudyConfiguration.from_mapping(
                {bus_id: "SLACK" if bus_id == slack_id else "PV" if bus_id in pv_ids else "PQ" for bus_id in bus_ids},
                base_mva=self._positive_finite(base_mva_text, "Initial Power Flow system base MVA"),
            )
            try:
                end_time = float(str(end_time_text).strip())
                dt = float(str(dt_text).strip())
            except (TypeError, ValueError) as exc:
                raise ValueError("Transient end time and time step must be numbers.") from exc
            return TransientStabilityStudyConfiguration(
                start_time=0.0,
                end_time=end_time,
                dt=dt,
                power_flow_configuration=initial_pf,
            )
        raise ValueError(f"Unsupported Study Case type: {study_type!r}.")

    def create_study_case(
        self,
        study_type: str,
        display_name: str,
        slack_bus_id: str,
        pv_bus_ids: Iterable[str],
        base_mva_text: str,
        fault_bus_id: str,
        fault_type: str,
        fault_resistance_text: str,
        fault_reactance_text: str,
        end_time_text: str,
        dt_text: str,
    ) -> object | None:
        """Validate typed configuration and register it through Application."""
        try:
            study_type = str(study_type).strip().lower()
            configuration = self._build_configuration(
                study_type, slack_bus_id, pv_bus_ids, base_mva_text,
                fault_bus_id, fault_type, fault_resistance_text, fault_reactance_text,
                end_time_text, dt_text, include_draft=False,
            )
            create = getattr(self._application, "create_study_case", None)
            if not callable(create):
                raise TypeError("Application must expose create_study_case().")
            return create(
                study_type=study_type,
                configuration={"configuration": configuration},
                display_name=str(display_name).strip(),
            )
        except Exception as exc:
            return self._handle_error(exc)

    @staticmethod
    def _operating_point(bus_set: set[str], slack_bus_id: str, pv_bus_ids: Iterable[str]) -> tuple[str, set[str]]:
        slack_id = str(slack_bus_id).strip()
        if slack_id not in bus_set:
            raise ValueError("Select a valid Slack Bus from the active network.")
        pv_ids = {str(bus_id).strip() for bus_id in pv_bus_ids if str(bus_id).strip()}
        unknown = sorted(pv_ids - bus_set)
        if unknown:
            raise ValueError("Unknown PV Bus ID(s): " + ", ".join(unknown))
        if slack_id in pv_ids:
            raise ValueError("The Slack Bus cannot also be classified as PV.")
        return slack_id, pv_ids

    def _handle_error(self, error: Exception, *, cause: BaseException | None = None) -> None:
        if self._error_handler is not None:
            self._error_handler(error)
            return None
        if cause is not None:
            raise error from cause
        raise error


__all__ = ["StudyCaseController", "StudySubmission"]
