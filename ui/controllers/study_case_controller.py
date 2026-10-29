# ============================================================
# File: ui/controllers/study_case_controller.py
# GridForge V2 — Study Case Interaction Boundary
# Author: Subhendu Mishra
# ============================================================

"""UI interaction boundary for creating and running Application-owned Study Cases."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import math
from uuid import UUID
from typing import Any

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.analysis.transient_stability import TransientStabilityStudyConfiguration
from core.solver.short_circuit.fault_types import FaultType


class StudyCaseController:
    """Translate Study Case UI intent into the Application study boundary."""

    def __init__(self, *, application: Any, error_handler: Callable[[BaseException], object] | None = None) -> None:
        if application is None:
            raise ValueError("application is required.")
        if not callable(getattr(application, "study_case", None)):
            raise TypeError("application must expose study_case().")
        if not callable(getattr(application, "execute_study_case", None)):
            raise TypeError("application must expose execute_study_case().")
        self._application = application
        self._error_handler = error_handler

    def run_study(self, study_id: UUID) -> object | None:
        """Run the selected structured Study Case through Application only."""
        if not isinstance(study_id, UUID):
            try:
                study_id = UUID(str(study_id))
            except (TypeError, ValueError) as exc:
                return self._handle_error(ValueError("Selected Study Case identity is invalid."), cause=exc)
        try:
            self._application.study_case(study_id)
            return self._application.execute_study_case(study_id)
        except Exception as exc:
            return self._handle_error(exc)

    def available_bus_ids(self) -> tuple[str, ...]:
        """Return canonical Bus identities from the Application read model."""
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

    @staticmethod
    def _positive_finite(value: object, label: str) -> float:
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be entered as a number.") from exc
        if not math.isfinite(parsed) or parsed <= 0.0:
            raise ValueError(f"{label} must be finite and greater than zero.")
        return parsed

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
            bus_ids = self.available_bus_ids()
            if not bus_ids:
                raise ValueError("The active network has no Bus objects.")
            bus_set = set(bus_ids)
            if study_type == "power_flow":
                slack_id, pv_ids = self._operating_point(bus_set, slack_bus_id, pv_bus_ids)
                configuration = PowerFlowStudyConfiguration.from_mapping(
                    {bus_id: "SLACK" if bus_id == slack_id else "PV" if bus_id in pv_ids else "PQ" for bus_id in bus_ids},
                    base_mva=self._positive_finite(base_mva_text, "System base MVA"),
                )
            elif study_type == "short_circuit":
                fault_bus = str(fault_bus_id).strip()
                if fault_bus not in bus_set:
                    raise ValueError("Select a valid fault Bus from the active network.")
                try:
                    resistance = float(str(fault_resistance_text).strip())
                    reactance = float(str(fault_reactance_text).strip())
                except (TypeError, ValueError) as exc:
                    raise ValueError("Fault resistance and reactance must be numbers.") from exc
                if not math.isfinite(resistance) or not math.isfinite(reactance):
                    raise ValueError("Fault resistance and reactance must be finite.")
                configuration = ShortCircuitStudyConfiguration(
                    fault_type=FaultType.from_value(fault_type),
                    fault_bus_id=fault_bus,
                    fault_impedance=complex(resistance, reactance),
                    base_mva=self._positive_finite(base_mva_text, "System base MVA"),
                )
            elif study_type == "transient_stability":
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
                configuration = TransientStabilityStudyConfiguration(
                    start_time=0.0,
                    end_time=end_time,
                    dt=dt,
                    power_flow_configuration=initial_pf,
                )
            else:
                raise ValueError(f"Unsupported Study Case type: {study_type!r}.")
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


__all__ = ["StudyCaseController"]
