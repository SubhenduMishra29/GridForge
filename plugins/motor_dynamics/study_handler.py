"""Application StudyService adapter for motor transient studies.

The handler is headless: it computes and returns a detached result envelope.
A StudyCompleted subscriber publishes that envelope to the read model only
after StudyService has stored a successful StudyResult.
"""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from collections.abc import Mapping
from typing import Any

from core.application.events import StudyCancelled, StudyCompleted, StudyFailed, StudyStarted
from core.application.study import StudyRequest, StudyExecutionContext, StudyCancellationToken, StudyResult
from .transient_solver import MotorParameters, MotorSimulationResult, solve_transient_batch, solve_transient_cpu


@dataclass(frozen=True, slots=True)
class MotorTransientEnvelope:
    """Detached solver output awaiting canonical StudyService completion."""
    motor_id: str
    parameters: MotorParameters
    electrical_frequency_hz: float
    load_torque_nm: float
    result: MotorSimulationResult


class MotorTransientStudyHandler:
    """Execute one motor transient StudyRequest without publishing UI state."""

    def __call__(
        self,
        request: StudyRequest,
        execution_context: StudyExecutionContext,
        cancellation: StudyCancellationToken,
    ) -> MotorTransientEnvelope | None:
        del execution_context  # The solver consumes explicit validated study inputs.
        config = request.configuration
        motor_id = config.get("motor_id")
        if not isinstance(motor_id, str) or not motor_id.strip():
            raise ValueError("motor_transient configuration requires a non-empty motor_id")
        raw_parameters = config.get("parameters")
        if isinstance(raw_parameters, MotorParameters):
            parameters = raw_parameters
        elif isinstance(raw_parameters, Mapping):
            parameters = MotorParameters(**dict(raw_parameters))
        else:
            raise TypeError("motor_transient parameters must be MotorParameters or a mapping of MotorParameters fields")

        duration_s = config.get("duration_s")
        step_s = config.get("step_s")
        voltage_d = config.get("stator_voltage_d_v", 0.0)
        voltage_q = config.get("stator_voltage_q_v", 0.0)
        frequency = config.get("electrical_frequency_hz", 50.0)
        load_torque = config.get("load_torque_nm", 0.0)
        backend = config.get("backend", "auto")
        for name, value in (("duration_s", duration_s), ("step_s", step_s)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a numeric scalar")
        if not isinstance(backend, str) or backend not in ("auto", "cpu", "cuda"):
            raise ValueError("backend must be 'auto', 'cpu', or 'cuda'")
        if cancellation.cancelled:
            return None

        # GPU API currently supports constant dq voltage inputs. Profiles use
        # the CPU reference integrator; no inference provider is treated as a
        # physics accelerator. NPU physics dispatch is intentionally not claimed.
        if isinstance(voltage_d, (int, float)) and not isinstance(voltage_d, bool) and isinstance(voltage_q, (int, float)) and not isinstance(voltage_q, bool):
            result = solve_transient_batch(
                (motor_id.strip(),), (parameters,), float(duration_s), float(step_s),
                stator_voltage_d_v=float(voltage_d),
                stator_voltage_q_v=float(voltage_q),
                electrical_frequency_hz=frequency,
                load_torque_nm=(load_torque,),
                backend=backend,
            )[0]
        else:
            if backend == "cuda":
                # An explicit backend request is a contract, not a preference.
                # Variable dq profiles are not implemented by the CUDA batch
                # kernel, so fail clearly rather than silently changing backend.
                raise ValueError(
                    "backend='cuda' is unsupported for variable stator-voltage "
                    "profiles; use backend='cpu' or backend='auto'."
                )
            result = solve_transient_cpu(
                motor_id.strip(), parameters, float(duration_s), float(step_s),
                stator_voltage_d_v=voltage_d, stator_voltage_q_v=voltage_q,
                electrical_frequency_hz=frequency, load_torque_nm=load_torque,
            )
        if cancellation.cancelled:
            return None
        return MotorTransientEnvelope(
            motor_id.strip(), parameters, float(frequency), float(load_torque), result
        )


class MotorTransientResultPublisher:
    """Publish only stored, successful motor_transient StudyResults."""

    def __init__(self, application: Any, read_models: Any) -> None:
        self._application = application
        self._read_models = read_models
        self.last_error: str | None = None
        self._order_lock = RLock()
        self._next_study_order = 0
        self._study_orders: dict[str, int] = {}
        self._active = True

    def on_started(self, event: StudyStarted) -> None:
        """Record submission order so late completion cannot replace newer output."""
        payload = event.payload
        if payload.get("study_type") != "motor_transient":
            return
        study_id = payload.get("study_id")
        if not isinstance(study_id, str) or not study_id.strip():
            return
        with self._order_lock:
            if not self._active:
                return
            self._next_study_order += 1
            self._study_orders[study_id] = self._next_study_order

    def on_terminal(self, event: StudyFailed | StudyCancelled) -> None:
        """Discard ordering metadata for studies that will never publish results."""
        study_id = event.payload.get("study_id")
        if not isinstance(study_id, str):
            return
        with self._order_lock:
            self._study_orders.pop(study_id, None)

    def close(self) -> None:
        """Prevent late events from publishing and release retained study IDs."""
        with self._order_lock:
            self._active = False
            self._study_orders.clear()

    def __call__(self, event: StudyCompleted) -> None:
        payload = event.payload
        with self._order_lock:
            if not self._active:
                return
        study_id = payload.get("study_id")
        project_id = payload.get("project_id")
        generation = payload.get("activation_generation")
        if not isinstance(study_id, str) or not isinstance(project_id, str):
            return
        if isinstance(generation, bool) or not isinstance(generation, int):
            return
        try:
            from uuid import UUID
            parsed_id = UUID(study_id)
        except (TypeError, ValueError):
            return
        get_result = getattr(self._application, "study_result", None)
        if not callable(get_result):
            return
        result = get_result(parsed_id, project_id=project_id, activation_generation=generation)
        if not isinstance(result, StudyResult) or result.status != "completed" or result.study_type != "motor_transient":
            return
        envelope = result.value
        if not isinstance(envelope, MotorTransientEnvelope):
            return
        with self._order_lock:
            if not self._active:
                return
            study_order = self._study_orders.pop(study_id, None)
        if study_order is None:
            self.last_error = "missing_study_start_order"
            return
        try:
            accepted = envelope.result.publish_to(
                self._read_models, envelope.parameters, envelope.electrical_frequency_hz,
                envelope.load_torque_nm, study_id=study_id, study_order=study_order,
            )
            if not accepted:
                self.last_error = "stale_study_result_ignored"
                return
        except Exception as exc:
            # A projection/read-model failure must not make StudyService turn
            # an already stored successful engineering result into "failed".
            self.last_error = f"{type(exc).__name__}: {exc}"
        else:
            self.last_error = None


__all__ = ["MotorTransientEnvelope", "MotorTransientStudyHandler", "MotorTransientResultPublisher"]
