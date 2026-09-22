"""Application service boundary for Transformer mutations.

Author: Subhendu Mishra

Transformer impedance entered through the existing application contract is
explicitly referred to the FROM-side nominal voltage. This is a contract,
not an inferred electrical value, and is persisted on the Transformer as
``impedance_base_voltage_kv`` for deterministic study preparation.
"""

from __future__ import annotations

from typing import Any

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.model.terminal import Terminal
from core.model.transformer import Transformer
from core.network.network import Network


class TransformerModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Transformer."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    @staticmethod
    def _endpoint_nominal_voltage_kv(endpoint: Bus | Terminal, parameter_name: str) -> float:
        bus = endpoint if isinstance(endpoint, Bus) else endpoint.endpoint
        if not isinstance(bus, Bus):
            raise ValueError(
                f"{parameter_name} must resolve to a Bus with nominal_voltage_kv before a Transformer can declare its impedance basis."
            )
        voltage_kv = float(bus.nominal_voltage_kv)
        if voltage_kv <= 0.0:
            raise ValueError(f"{parameter_name} bus nominal_voltage_kv must be greater than zero.")
        return voltage_kv

    def create_transformer(
        self,
        *,
        transformer_id: str,
        endpoint_from: Bus | Terminal,
        endpoint_to: Bus | Terminal,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        impedance_basis: str,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction)
        self._require_id(transformer_id, "transformer_id")
        self._validate_endpoint(endpoint_from, "endpoint_from")
        self._validate_endpoint(endpoint_to, "endpoint_to")
        self._require_distinct_endpoints(endpoint_from, endpoint_to, "INVALID_TRANSFORMER_ENDPOINTS", "Transformer", transformer_id)
        self._ensure_not_exists("transformer", transformer_id, "Transformer")

        # Frozen application contract: transformer r/x/b is referred to the
        # explicitly named FROM side. The value is captured in the Core model
        # so preparation never has to infer which voltage base was intended.
        impedance_base_voltage_kv = self._endpoint_nominal_voltage_kv(endpoint_from, "endpoint_from")

        transformer = Transformer(
            id=transformer_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            impedance_basis=impedance_basis,
            impedance_base_voltage_kv=impedance_base_voltage_kv,
            tap=tap,
            shift=shift,
            name="" if name is None else name,
            rate_mva=rate_mva,
        )
        self._network.add_transformer(transformer)
        transaction.record_undo(lambda transformer=transformer: self._network.remove_transformer(transformer))
        return self._success(transformer, "transformer", transformer_id, f"Transformer created: {transformer_id}")

    def update_transformer(
        self,
        *,
        transformer_id: str,
        name: str | None = None,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        impedance_basis: Any | None = None,
        impedance_base_mva: float | None = None,
        tap: float | None = None,
        shift: float | None = None,
        rate_mva: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction)
        self._require_id(transformer_id, "transformer_id")
        transformer = self._get_required("transformer", transformer_id, "Transformer")
        self._require_type(transformer, Transformer, transformer_id, "Transformer")

        values = (
            name, r, x, b, impedance_basis, impedance_base_mva,
            tap, shift, rate_mva, in_service,
        )
        if all(value is None for value in values):
            raise ValueError("At least one Transformer configuration field must be specified.")

        old_state = {
            "name": transformer.name,
            "r": transformer.r,
            "x": transformer.x,
            "b": transformer.b,
            "impedance_basis": transformer.impedance_basis,
            "impedance_base_mva": transformer.impedance_base_mva,
            "tap": transformer.tap,
            "shift": transformer.shift,
            "rate_mva": transformer.rate_mva,
            "in_service": transformer.in_service,
        }

        transformer.update_configuration(
            name=name,
            r=r,
            x=x,
            b=b,
            impedance_basis=impedance_basis,
            impedance_base_mva=impedance_base_mva,
            tap=tap,
            shift=shift,
            rate_mva=rate_mva,
            in_service=in_service,
        )

        def restore() -> None:
            transformer.update_configuration(**old_state)

        transaction.record_undo(restore)
        return self._success(
            transformer,
            "transformer",
            transformer_id,
            f"Transformer updated: {transformer_id}",
        )

    def delete_transformer(self, *, transformer_id: str, transaction: Transaction) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction)
        self._require_id(transformer_id, "transformer_id")
        transformer = self._get_required("transformer", transformer_id, "Transformer")
        self._require_type(transformer, Transformer, transformer_id, "Transformer")
        self._network.remove_transformer(transformer)
        transaction.record_undo(lambda transformer=transformer: self._network.add_transformer(transformer))
        return self._success(transformer, "transformer", transformer_id, f"Transformer deleted: {transformer_id}")


__all__ = ["TransformerModelService"]
