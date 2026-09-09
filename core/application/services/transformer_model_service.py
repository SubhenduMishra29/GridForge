"""Application service boundary for Transformer mutations."""

from __future__ import annotations

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

    def create_transformer(
        self,
        *,
        transformer_id: str,
        endpoint_from: Bus | Terminal,
        endpoint_to: Bus | Terminal,
        r: float = 0.0,
        x: float = 0.0,
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
        self._require_distinct_endpoints(
            endpoint_from,
            endpoint_to,
            "INVALID_TRANSFORMER_ENDPOINTS",
            "Transformer",
            transformer_id,
        )
        self._ensure_not_exists("transformer", transformer_id, "Transformer")
        transformer = Transformer(
            id=transformer_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            tap=tap,
            shift=shift,
            name="" if name is None else name,
            rate_mva=rate_mva,
        )
        self._network.add_transformer(transformer)
        transaction.record_undo(
            lambda transformer=transformer: self._network.remove_transformer(transformer)
        )
        return self._success(
            transformer,
            "transformer",
            transformer_id,
            f"Transformer created: {transformer_id}",
        )

    def delete_transformer(
        self,
        *,
        transformer_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction)
        self._require_id(transformer_id, "transformer_id")
        transformer = self._get_required("transformer", transformer_id, "Transformer")
        self._require_type(transformer, Transformer, transformer_id, "Transformer")
        self._network.remove_transformer(transformer)
        transaction.record_undo(
            lambda transformer=transformer: self._network.add_transformer(transformer)
        )
        return self._success(
            transformer,
            "transformer",
            transformer_id,
            f"Transformer deleted: {transformer_id}",
        )


__all__ = ["TransformerModelService"]
