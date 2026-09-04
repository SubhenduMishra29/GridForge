# ============================================================
# File: tests/core/application/test_bus_application_contract.py
# GridForge V2 — Bus Application Contract Tests
# Author: Subhendu Mishra
# ============================================================

"""Regression tests for the Application Bus contract."""

from __future__ import annotations

import unittest

from core.application.commands import CreateBusCommand as PublicCreateBusCommand
from core.application.commands.create_bus import CreateBusCommand
from core.application.command_handlers import ModelCommandHandlers
from core.application.services.bus_model_service import ModelService
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.network.network import Network


class _RecordingBusService:
    """Minimal service double for handler contract testing."""

    def __init__(self) -> None:
        self.calls: dict[str, object] = {}

    def create_bus(self, **kwargs):
        self.calls = kwargs
        return "result"


class CreateBusApplicationContractTests(unittest.TestCase):
    def test_public_command_is_canonical_command(self) -> None:
        self.assertIs(PublicCreateBusCommand, CreateBusCommand)

    def test_command_payload_matches_authoritative_bus_contract(self) -> None:
        command = CreateBusCommand(
            bus_id="B1",
            name="Bus 1",
            nominal_voltage_kv=132.0,
            voltage_pu=1.02,
            angle_deg=-2.5,
            frequency_hz=50.0,
            in_service=True,
        )

        self.assertEqual(
            set(command.payload.keys()),
            {
                "bus_id",
                "name",
                "nominal_voltage_kv",
                "voltage_pu",
                "angle_deg",
                "frequency_hz",
                "in_service",
            },
        )
        self.assertEqual(command.payload["bus_id"], "B1")
        self.assertEqual(command.payload["name"], "Bus 1")
        self.assertEqual(command.payload["nominal_voltage_kv"], 132.0)
        self.assertEqual(command.payload["voltage_pu"], 1.02)
        self.assertEqual(command.payload["angle_deg"], -2.5)
        self.assertEqual(command.payload["frequency_hz"], 50.0)
        self.assertTrue(command.payload["in_service"])

    def test_handler_forwards_complete_bus_contract(self) -> None:
        service = _RecordingBusService()
        handlers = ModelCommandHandlers(service)
        command = CreateBusCommand(
            bus_id="B2",
            name="Bus 2",
            nominal_voltage_kv=220.0,
        )
        transaction = Transaction()

        result = handlers.create_bus(
            command,
            context=None,
            transaction=transaction,
        )

        self.assertEqual(result, "result")
        self.assertEqual(
            service.calls,
            {
                "bus_id": "B2",
                "name": "Bus 2",
                "nominal_voltage_kv": 220.0,
                "voltage_pu": 1.0,
                "angle_deg": 0.0,
                "frequency_hz": 50.0,
                "in_service": True,
                "transaction": transaction,
            },
        )

    def test_model_service_creates_authoritative_bus(self) -> None:
        network = Network()
        transaction = Transaction()
        service = ModelService(network)

        result = service.create_bus(
            bus_id="B3",
            name="Bus 3",
            nominal_voltage_kv=400.0,
            voltage_pu=1.02,
            angle_deg=-2.5,
            frequency_hz=50.0,
            in_service=True,
            transaction=transaction,
        )

        self.assertTrue(result.success)
        self.assertIsInstance(result.value, Bus)
        self.assertEqual(result.value.id, "B3")
        self.assertEqual(result.value.name, "Bus 3")
        self.assertEqual(result.value.nominal_voltage_kv, 400.0)
        self.assertEqual(result.value.voltage_pu, 1.02)
        self.assertEqual(result.value.angle_deg, -2.5)
        self.assertEqual(result.value.frequency_hz, 50.0)
        self.assertTrue(result.value.in_service)
        self.assertIn(result.value, network.buses)

    def test_bus_creation_rollback_removes_bus(self) -> None:
        network = Network()
        transaction = Transaction()
        service = ModelService(network)

        result = service.create_bus(
            bus_id="B4",
            name="Bus 4",
            nominal_voltage_kv=132.0,
            transaction=transaction,
        )

        self.assertTrue(result.success)
        transaction.rollback()
        self.assertNotIn(result.value, network.buses)


if __name__ == "__main__":
    unittest.main()
