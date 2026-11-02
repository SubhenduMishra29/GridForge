"""Explicit field-device delivery and acknowledgement boundary.

An adapter is deployment supplied. Core/Application command acceptance is not
physical delivery, and delivery is not proof of device execution.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from threading import RLock
from typing import Any, Protocol, Callable


@dataclass(frozen=True, slots=True)
class FieldDeviceCommandRequest:
    project_id: str
    activation_generation: int
    protection_cycle_id: str
    command_id: str
    target_equipment_type: str
    target_equipment_id: str
    action_type: str
    issued_at: float

    def __post_init__(self) -> None:
        for name in ("project_id", "protection_cycle_id", "command_id",
                     "target_equipment_type", "target_equipment_id", "action_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty.")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if isinstance(self.issued_at, bool) or not isinstance(self.issued_at, (int, float)) or not math.isfinite(self.issued_at):
            raise ValueError("issued_at must be a finite trusted timestamp.")


@dataclass(frozen=True, slots=True)
class FieldDeviceDeliveryReceipt:
    command_id: str
    delivery_id: str
    status: str
    diagnostic: str = ""

    def __post_init__(self) -> None:
        if not self.command_id or not self.delivery_id:
            raise ValueError("command_id and delivery_id are required.")
        if self.status not in {"accepted", "rejected", "unknown"}:
            raise ValueError("delivery status must be accepted, rejected, or unknown.")


@dataclass(frozen=True, slots=True)
class FieldDeviceAcknowledgement:
    command_id: str
    delivery_id: str
    project_id: str
    activation_generation: int
    protection_cycle_id: str
    device_id: str
    status: str
    acknowledged_at: float
    timestamp_domain: str
    signature: str
    payload_digest: str
    acknowledgement_id: str

    def __post_init__(self) -> None:
        for name in ("command_id", "delivery_id", "project_id", "protection_cycle_id", "device_id", "timestamp_domain", "signature", "payload_digest", "acknowledgement_id"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required.")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("acknowledgement activation_generation must be a positive integer.")
        if self.status not in {"executed", "rejected"}:
            raise ValueError("acknowledgement status must be executed or rejected.")
        if isinstance(self.acknowledged_at, bool) or not isinstance(self.acknowledged_at, (int, float)) or not math.isfinite(self.acknowledged_at):
            raise ValueError("acknowledged_at must be a finite timestamp.")


@dataclass(frozen=True, slots=True)
class FieldDeviceExecutionStatus:
    delivery_status: str
    acknowledgement_status: str
    delivery_id: str | None = None
    acknowledgement_id: str | None = None
    diagnostic: str = ""
    project_id: str | None = None
    activation_generation: int | None = None
    protection_cycle_id: str | None = None
    device_id: str | None = None
    acknowledged_at: float | None = None
    timestamp_domain: str | None = None


class FieldDeviceAdapter(Protocol):
    def send(self, request: FieldDeviceCommandRequest) -> FieldDeviceDeliveryReceipt: ...
    def poll_acknowledgement(self, command_id: str) -> FieldDeviceAcknowledgement | None: ...


class FieldDeviceCommandService:
    """Validate adapter receipts and cryptographically authenticated feedback."""

    def __init__(self, adapter: FieldDeviceAdapter,
                 acknowledgement_verifier: Callable[[FieldDeviceAcknowledgement], bool],
                 *, clock: Callable[[], float], clock_domain: str,
                 max_acknowledgement_age_seconds: float = 30.0,
                 max_future_skew_seconds: float = 2.0) -> None:
        if not callable(getattr(adapter, "send", None)) or not callable(getattr(adapter, "poll_acknowledgement", None)):
            raise TypeError("adapter must implement send() and poll_acknowledgement().")
        if not callable(acknowledgement_verifier):
            raise TypeError("acknowledgement_verifier must be callable.")
        if not callable(clock):
            raise TypeError("a trusted clock callable is required for device acknowledgement validation.")
        if not isinstance(clock_domain, str) or not clock_domain.strip():
            raise ValueError("clock_domain must be a non-empty trusted clock domain.")
        for name, value in (("max_acknowledgement_age_seconds", max_acknowledgement_age_seconds), ("max_future_skew_seconds", max_future_skew_seconds)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative.")
        self._adapter = adapter
        self._acknowledgement_verifier = acknowledgement_verifier
        self._clock = clock
        self._clock_domain = clock_domain
        self._max_acknowledgement_age_seconds = float(max_acknowledgement_age_seconds)
        self._max_future_skew_seconds = float(max_future_skew_seconds)
        self._deliveries: dict[str, FieldDeviceDeliveryReceipt] = {}
        self._requests: dict[str, FieldDeviceCommandRequest] = {}
        self._lock = RLock()

    def deliver(self, request: FieldDeviceCommandRequest) -> FieldDeviceExecutionStatus:
        if not isinstance(request, FieldDeviceCommandRequest):
            raise TypeError("request must be FieldDeviceCommandRequest.")
        with self._lock:
            existing = self._deliveries.get(request.command_id)
            if existing is not None:
                return self.poll_acknowledgement(request.command_id)
            receipt = self._adapter.send(request)
            if not isinstance(receipt, FieldDeviceDeliveryReceipt):
                raise TypeError("field-device adapter must return FieldDeviceDeliveryReceipt.")
            if receipt.command_id != request.command_id:
                return FieldDeviceExecutionStatus("unknown", "unavailable", diagnostic="adapter receipt command identity mismatch")
            self._deliveries[request.command_id] = receipt
            self._requests[request.command_id] = request
            if receipt.status != "accepted":
                return FieldDeviceExecutionStatus(
                    receipt.status, "unavailable", receipt.delivery_id,
                    diagnostic=receipt.diagnostic or "device transport did not accept the command",
                )
            return self.poll_acknowledgement(request.command_id)

    def poll_acknowledgement(self, command_id: str) -> FieldDeviceExecutionStatus:
        with self._lock:
            receipt = self._deliveries.get(command_id)
        acknowledgement = self._adapter.poll_acknowledgement(command_id)
        if acknowledgement is None:
            return FieldDeviceExecutionStatus(
                "accepted" if receipt is not None else "unknown",
                "pending" if receipt is not None else "unavailable",
                receipt.delivery_id if receipt is not None else None,
                diagnostic="physical acknowledgement has not arrived" if receipt is not None
                else "no in-memory delivery receipt; adapter has no recoverable acknowledgement",
            )
        if not isinstance(acknowledgement, FieldDeviceAcknowledgement):
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else None,
                                              diagnostic="adapter returned an invalid acknowledgement type")
        request = self._requests.get(command_id)
        if request is not None and (
            acknowledgement.project_id != request.project_id
            or acknowledgement.activation_generation != request.activation_generation
            or acknowledgement.protection_cycle_id != request.protection_cycle_id
        ):
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic="acknowledgement project/cycle provenance does not match the dispatched request")
        if acknowledgement.command_id != command_id or (
            receipt is not None and acknowledgement.delivery_id != receipt.delivery_id
        ):
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic="acknowledgement correlation identity mismatch")
        if acknowledgement.timestamp_domain != self._clock_domain:
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic="acknowledgement timestamp domain does not match the trusted Application clock")
        try:
            trusted_now = self._clock()
        except Exception as exc:
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic=f"trusted clock unavailable for acknowledgement validation: {type(exc).__name__}: {exc}")
        if isinstance(trusted_now, bool) or not isinstance(trusted_now, (int, float)) or not math.isfinite(trusted_now):
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic="trusted clock returned an invalid timestamp during acknowledgement validation")
        acknowledgement_age = float(trusted_now) - float(acknowledgement.acknowledged_at)
        if acknowledgement_age < -self._max_future_skew_seconds or acknowledgement_age > self._max_acknowledgement_age_seconds:
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic="physical acknowledgement timestamp is outside the permitted trusted-clock freshness window")
        try:
            verified = self._acknowledgement_verifier(acknowledgement)
        except Exception as exc:
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic=f"acknowledgement verification failed: {type(exc).__name__}: {exc}")
        if verified is not True:
            return FieldDeviceExecutionStatus("accepted" if receipt is not None else "unknown", "invalid",
                                              receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
                                              diagnostic="physical acknowledgement signature was not authenticated")
        return FieldDeviceExecutionStatus(
            "accepted" if receipt is not None else "unknown", acknowledgement.status,
            receipt.delivery_id if receipt is not None else acknowledgement.delivery_id,
            acknowledgement_id=acknowledgement.acknowledgement_id,
            project_id=acknowledgement.project_id,
            activation_generation=acknowledgement.activation_generation,
            protection_cycle_id=acknowledgement.protection_cycle_id,
            device_id=acknowledgement.device_id,
            acknowledged_at=float(acknowledgement.acknowledged_at),
            timestamp_domain=acknowledgement.timestamp_domain,
        )


__all__ = [
    "FieldDeviceCommandRequest", "FieldDeviceDeliveryReceipt",
    "FieldDeviceAcknowledgement", "FieldDeviceExecutionStatus",
    "FieldDeviceAdapter", "FieldDeviceCommandService",
]
