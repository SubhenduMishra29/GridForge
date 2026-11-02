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
    device_id: str
    status: str
    acknowledged_at: float
    signature: str
    payload_digest: str
    acknowledgement_id: str

    def __post_init__(self) -> None:
        for name in ("command_id", "delivery_id", "device_id", "signature", "payload_digest", "acknowledgement_id"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required.")
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


class FieldDeviceAdapter(Protocol):
    def send(self, request: FieldDeviceCommandRequest) -> FieldDeviceDeliveryReceipt: ...
    def poll_acknowledgement(self, command_id: str) -> FieldDeviceAcknowledgement | None: ...


class FieldDeviceCommandService:
    """Validate adapter receipts and cryptographically authenticated feedback."""

    def __init__(self, adapter: FieldDeviceAdapter,
                 acknowledgement_verifier: Callable[[FieldDeviceAcknowledgement], bool]) -> None:
        if not callable(getattr(adapter, "send", None)) or not callable(getattr(adapter, "poll_acknowledgement", None)):
            raise TypeError("adapter must implement send() and poll_acknowledgement().")
        if not callable(acknowledgement_verifier):
            raise TypeError("acknowledgement_verifier must be callable.")
        self._adapter = adapter
        self._acknowledgement_verifier = acknowledgement_verifier
        self._deliveries: dict[str, FieldDeviceDeliveryReceipt] = {}
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
        with self._lock:
            self._deliveries[request.command_id] = receipt
        if receipt.status != "accepted":
            return FieldDeviceExecutionStatus(receipt.status, "unavailable", receipt.delivery_id,
                                              diagnostic=receipt.diagnostic or "device transport did not accept the command")
        return self.poll_acknowledgement(request.command_id)

    def poll_acknowledgement(self, command_id: str) -> FieldDeviceExecutionStatus:
        with self._lock:
            receipt = self._deliveries.get(command_id)
        if receipt is None:
            return FieldDeviceExecutionStatus("unknown", "unavailable", diagnostic="no accepted delivery is registered for this command")
        acknowledgement = self._adapter.poll_acknowledgement(command_id)
        if acknowledgement is None:
            return FieldDeviceExecutionStatus("accepted", "pending", receipt.delivery_id,
                                              diagnostic="delivery accepted; physical acknowledgement has not arrived")
        if not isinstance(acknowledgement, FieldDeviceAcknowledgement):
            return FieldDeviceExecutionStatus("accepted", "invalid", receipt.delivery_id,
                                              diagnostic="adapter returned an invalid acknowledgement type")
        if acknowledgement.command_id != command_id or acknowledgement.delivery_id != receipt.delivery_id:
            return FieldDeviceExecutionStatus("accepted", "invalid", receipt.delivery_id,
                                              diagnostic="acknowledgement correlation identity mismatch")
        try:
            verified = self._acknowledgement_verifier(acknowledgement)
        except Exception as exc:
            return FieldDeviceExecutionStatus("accepted", "invalid", receipt.delivery_id,
                                              diagnostic=f"acknowledgement verification failed: {type(exc).__name__}: {exc}")
        if verified is not True:
            return FieldDeviceExecutionStatus("accepted", "invalid", receipt.delivery_id,
                                              diagnostic="physical acknowledgement signature was not authenticated")
        return FieldDeviceExecutionStatus(
            "accepted", acknowledgement.status, receipt.delivery_id,
            acknowledgement_id=acknowledgement.acknowledgement_id,
        )


__all__ = [
    "FieldDeviceCommandRequest", "FieldDeviceDeliveryReceipt",
    "FieldDeviceAcknowledgement", "FieldDeviceExecutionStatus",
    "FieldDeviceAdapter", "FieldDeviceCommandService",
]
