"""Application service boundary for branch-domain mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.branch import Branch
from core.model.bus import Bus
from core.model.cable import Cable
from core.model.line import Line
from core.model.terminal import Terminal
from core.network.network import Network


class BranchModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for the branch domain.

    The branch domain includes the abstract Branch concept and its
    concrete two-terminal implementations: Line and Cable.
    """

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    # ============================================================
    # BRANCH
    # ============================================================

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

    # ============================================================
    # LINE
    # ============================================================

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

    # ============================================================
    # CABLE
    # ============================================================

    def create_cable(
        self,
        *,
        cable_id: str,
        endpoint_from: Bus | Terminal | None = None,
        endpoint_to: Bus | Terminal | None = None,
        name: str = "",
        length_km: float = 0.0,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float = 0.0,
        x1_ohm_per_km: float = 0.0,
        b1_us_per_km: float = 0.0,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Cable]:
        self._require_transaction(transaction)
        self._require_id(cable_id, "cable_id")
        if endpoint_from is not None:
            self._validate_endpoint(endpoint_from, "endpoint_from")
        if endpoint_to is not None:
            self._validate_endpoint(endpoint_to, "endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:
            self._require_distinct_endpoints(
                endpoint_from,
                endpoint_to,
                "INVALID_CABLE_ENDPOINTS",
                "Cable",
                cable_id,
            )
        self._ensure_not_exists("cable", cable_id, "Cable")
        cable = Cable(
            id=cable_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            name=name,
            length_km=length_km,
            rated_voltage_kv=rated_voltage_kv,
            rated_current_a=rated_current_a,
            r1_ohm_per_km=r1_ohm_per_km,
            x1_ohm_per_km=x1_ohm_per_km,
            b1_us_per_km=b1_us_per_km,
            r0_ohm_per_km=r0_ohm_per_km,
            x0_ohm_per_km=x0_ohm_per_km,
            b0_us_per_km=b0_us_per_km,
            in_service=in_service,
        )
        self._network.add_cable(cable)
        transaction.record_undo(lambda cable=cable: self._network.remove_cable(cable))
        return self._success(cable, "cable", cable_id, f"Cable created: {cable_id}")

    def update_cable(
        self,
        *,
        cable_id: str,
        name: str | None = None,
        length_km: float | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float | None = None,
        x1_ohm_per_km: float | None = None,
        b1_us_per_km: float | None = None,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Cable]:
        self._require_transaction(transaction)
        self._require_id(cable_id, "cable_id")
        cable = self._get_required("cable", cable_id, "Cable")
        self._require_type(cable, Cable, cable_id, "Cable")
        if all(
            value is None
            for value in (
                name,
                length_km,
                rated_voltage_kv,
                rated_current_a,
                r1_ohm_per_km,
                x1_ohm_per_km,
                b1_us_per_km,
                r0_ohm_per_km,
                x0_ohm_per_km,
                b0_us_per_km,
                in_service,
            )
        ):
            raise DomainError(
                code="NO_CABLE_UPDATE",
                message="At least one mutable Cable property must be specified.",
                details={"cable_id": cable_id},
            )

        old = {
            key: getattr(cable, key)
            for key in (
                "name",
                "length_km",
                "rated_voltage_kv",
                "rated_current_a",
                "r1_ohm_per_km",
                "x1_ohm_per_km",
                "b1_us_per_km",
                "r0_ohm_per_km",
                "x0_ohm_per_km",
                "b0_us_per_km",
                "in_service",
            )
        }
        for key, value in (
            ("name", name),
            ("length_km", length_km),
            ("rated_voltage_kv", rated_voltage_kv),
            ("rated_current_a", rated_current_a),
            ("r1_ohm_per_km", r1_ohm_per_km),
            ("x1_ohm_per_km", x1_ohm_per_km),
            ("b1_us_per_km", b1_us_per_km),
            ("r0_ohm_per_km", r0_ohm_per_km),
            ("x0_ohm_per_km", x0_ohm_per_km),
            ("b0_us_per_km", b0_us_per_km),
        ):
            if value is not None:
                setattr(cable, key, value)
        if in_service is not None:
            cable.set_in_service(in_service)

        def restore() -> None:
            for key, value in old.items():
                if key == "in_service":
                    cable.set_in_service(value)
                else:
                    setattr(cable, key, value)

        transaction.record_undo(restore)
        return self._success(cable, "cable", cable_id, f"Cable updated: {cable_id}")

    def delete_cable(
        self,
        *,
        cable_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Cable]:
        self._require_transaction(transaction)
        self._require_id(cable_id, "cable_id")
        cable = self._get_required("cable", cable_id, "Cable")
        self._require_type(cable, Cable, cable_id, "Cable")
        self._network.remove_cable(cable)
        transaction.record_undo(lambda cable=cable: self._network.add_cable(cable))
        return self._success(cable, "cable", cable_id, f"Cable deleted: {cable_id}")


__all__ = ["BranchModelService"]
