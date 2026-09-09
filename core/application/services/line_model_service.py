"""Application service boundary for Line mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.model.line import Line
from core.model.terminal import Terminal
from core.network.network import Network


class LineModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Line."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_line(
        self,
        *,
        line_id: str,
        endpoint_from: Bus | Terminal,
        endpoint_to: Bus | Terminal,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
        self._require_transaction(transaction)
        self._require_id(line_id, "line_id")
        self._validate_endpoint(endpoint_from, "endpoint_from")
        self._validate_endpoint(endpoint_to, "endpoint_to")
        self._require_distinct_endpoints(
            endpoint_from,
            endpoint_to,
            "INVALID_LINE_ENDPOINTS",
            "Line",
            line_id,
        )
        self._ensure_not_exists("line", line_id, "Line")
        line = Line(
            id=line_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name="" if name is None else name,
            rate_mva=rate_mva,
        )
        self._network.add_line(line)
        transaction.record_undo(lambda line=line: self._network.remove_line(line))
        return self._success(line, "line", line_id, f"Line created: {line_id}")

    def delete_line(
        self,
        *,
        line_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
        self._require_transaction(transaction)
        self._require_id(line_id, "line_id")
        line = self._get_required("line", line_id, "Line")
        self._require_type(line, Line, line_id, "Line")
        self._network.remove_line(line)
        transaction.record_undo(lambda line=line: self._network.add_line(line))
        return self._success(line, "line", line_id, f"Line deleted: {line_id}")


__all__ = ["LineModelService"]
