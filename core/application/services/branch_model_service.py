"""Application service boundary for Branch mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.branch import Branch
from core.model.bus import Bus
from core.model.terminal import Terminal
from core.network.network import Network


class BranchModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Branch."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_branch(
        self,
        *,
        branch_id: str,
        endpoint_from: Bus | Terminal | None = None,
        endpoint_to: Bus | Terminal | None = None,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        name: str = "",
        rate_mva: float | None = None,
        tap: float = 1.0,
        shift: float = 0.0,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Branch]:
        self._require_transaction(transaction)
        self._require_id(branch_id, "branch_id")
        if endpoint_from is not None:
            self._validate_endpoint(endpoint_from, "endpoint_from")
        if endpoint_to is not None:
            self._validate_endpoint(endpoint_to, "endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:
            self._require_distinct_endpoints(
                endpoint_from,
                endpoint_to,
                "INVALID_BRANCH_ENDPOINTS",
                "Branch",
                branch_id,
            )
        self._ensure_not_exists("branch", branch_id, "Branch")
        branch = Branch(
            id=branch_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
            tap=tap,
            shift=shift,
            in_service=in_service,
        )
        self._network.add_branch(branch)
        transaction.record_undo(lambda branch=branch: self._network.remove_branch(branch))
        return self._success(branch, "branch", branch_id, f"Branch created: {branch_id}")

    def update_branch(
        self,
        *,
        branch_id: str,
        name: str | None = None,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        rate_mva: float | None = None,
        tap: float | None = None,
        shift: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Branch]:
        self._require_transaction(transaction)
        self._require_id(branch_id, "branch_id")
        branch = self._get_required("branch", branch_id, "Branch")
        self._require_type(branch, Branch, branch_id, "Branch")
        if all(v is None for v in (name, r, x, b, rate_mva, tap, shift, in_service)):
            raise DomainError(
                code="NO_BRANCH_UPDATE",
                message="At least one mutable Branch property must be specified.",
                details={"branch_id": branch_id},
            )
        old = {
            "name": branch.name,
            "r": branch.r,
            "x": branch.x,
            "b": branch.b,
            "rate_mva": branch.rate_mva,
            "tap": branch.tap,
            "shift": branch.shift,
            "in_service": branch.in_service,
        }
        if name is not None:
            branch.name = name
        if r is not None:
            branch.r = r
        if x is not None:
            branch.x = x
        if b is not None:
            branch.b = b
        if rate_mva is not None:
            branch.rate_mva = rate_mva
        if tap is not None:
            branch.tap = tap
        if shift is not None:
            branch.shift = shift
        if in_service is not None:
            branch.set_in_service(in_service)

        def restore() -> None:
            branch.name = old["name"]
            branch.r = old["r"]
            branch.x = old["x"]
            branch.b = old["b"]
            branch.rate_mva = old["rate_mva"]
            branch.tap = old["tap"]
            branch.shift = old["shift"]
            branch.set_in_service(old["in_service"])

        transaction.record_undo(restore)
        return self._success(branch, "branch", branch_id, f"Branch updated: {branch_id}")

    def delete_branch(
        self,
        *,
        branch_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Branch]:
        self._require_transaction(transaction)
        self._require_id(branch_id, "branch_id")
        branch = self._get_required("branch", branch_id, "Branch")
        self._require_type(branch, Branch, branch_id, "Branch")
        self._network.remove_branch(branch)
        transaction.record_undo(lambda branch=branch: self._network.add_branch(branch))
        return self._success(branch, "branch", branch_id, f"Branch deleted: {branch_id}")


__all__ = ["BranchModelService"]
