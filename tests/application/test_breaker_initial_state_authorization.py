"""Regression coverage for initial breaker modelling versus live close authorization."""

import pytest

from core.application.errors import DomainError
from core.application.services.switching_model_service import SwitchingModelService
from core.application.transaction import Transaction
from core.network.network import Network


def test_initial_closed_breaker_creation_does_not_require_ansi25_authorization():
    network = Network()
    authorization_calls = []

    def authorize(breaker, operation):
        authorization_calls.append((breaker.id, operation))
        return True

    service = SwitchingModelService(network, breaker_close_authorizer=authorize)
    result = service.create_breaker(
        breaker_id="BRK-INITIAL",
        closed=True,
        transaction=Transaction(),
    )

    assert result.success
    assert network.get_by_id("breaker", "BRK-INITIAL").closed is True
    assert authorization_calls == []


def test_operational_breaker_close_remains_fail_closed_without_ansi25_authorizer():
    network = Network()
    service = SwitchingModelService(network)
    service.create_breaker(
        breaker_id="BRK-OPERATIONAL",
        closed=False,
        transaction=Transaction(),
    )

    with pytest.raises(DomainError) as exc_info:
        service.close_breaker(
            breaker_id="BRK-OPERATIONAL",
            transaction=Transaction(),
        )

    assert exc_info.value.code == "ANSI25_AUTHORIZATION_UNAVAILABLE"
    assert network.get_by_id("breaker", "BRK-OPERATIONAL").closed is False


def test_operational_close_still_invokes_ansi25_authorizer():
    network = Network()
    authorization_calls = []

    def authorize(breaker, operation):
        authorization_calls.append((breaker.id, operation))
        return True

    service = SwitchingModelService(network, breaker_close_authorizer=authorize)
    service.create_breaker(
        breaker_id="BRK-CLOSE",
        closed=False,
        transaction=Transaction(),
    )

    service.close_breaker(
        breaker_id="BRK-CLOSE",
        transaction=Transaction(),
    )

    assert authorization_calls == [("BRK-CLOSE", "close")]
    assert network.get_by_id("breaker", "BRK-CLOSE").closed is True


def test_update_cannot_operationally_close_without_ansi25_authorizer():
    network = Network()
    service = SwitchingModelService(network)
    service.create_breaker(
        breaker_id="BRK-UPDATE",
        closed=False,
        transaction=Transaction(),
    )

    with pytest.raises(DomainError) as exc_info:
        service.update_breaker(
            breaker_id="BRK-UPDATE",
            closed=True,
            transaction=Transaction(),
        )

    assert exc_info.value.code == "ANSI25_AUTHORIZATION_UNAVAILABLE"
    assert network.get_by_id("breaker", "BRK-UPDATE").closed is False


def test_reenergizing_initially_closed_breaker_requires_ansi25_authorizer():
    network = Network()
    service = SwitchingModelService(network)
    service.create_breaker(
        breaker_id="BRK-REENERGIZE",
        closed=True,
        in_service=False,
        transaction=Transaction(),
    )

    with pytest.raises(DomainError) as exc_info:
        service.put_breaker_in_service(
            breaker_id="BRK-REENERGIZE",
            transaction=Transaction(),
        )

    assert exc_info.value.code == "ANSI25_AUTHORIZATION_UNAVAILABLE"
    breaker = network.get_by_id("breaker", "BRK-REENERGIZE")
    assert breaker.closed is True
    assert breaker.in_service is False
