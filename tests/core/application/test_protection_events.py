# ============================================================
# File: tests/core/application/test_protection_events.py
# GridForge V2 — Protection Application Event Tests
# Author: Subhendu Mishra
# ============================================================

from core.application.events import ProtectionTripRequested
from core.protection.decision import ProtectionDecision


def test_protection_trip_requested_event_contains_canonical_decision_identity() -> None:
    decision = ProtectionDecision(
        relay_id="R1",
        element_id="OC50",
        function_code="50",
        pickup=True,
        operate=True,
        trip_request=True,
        valid=True,
    )

    event = ProtectionTripRequested.from_decision(decision, breaker_id="BRK-1")

    assert event.event_type == "protection.trip.requested"
    assert event.payload["relay_id"] == "R1"
    assert event.payload["element_id"] == "OC50"
    assert event.payload["function_code"] == "50"
    assert event.payload["breaker_id"] == "BRK-1"
