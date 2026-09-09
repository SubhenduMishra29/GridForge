"""Application service boundary for Potential Transformer mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.model.pt import PT
from core.model.terminal import Terminal
from core.network.network import Network


class PTModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for PT equipment."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network): raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network: return self._network

    def create_pt(self, *, pt_id: str, name: str = "", primary_voltage_kv: float = 11.0,
                  secondary_voltage_v: float = 110.0, accuracy_class: str = "0.5",
                  burden_va: float = 100.0, phase_displacement_deg: float = 0.0,
                  in_service: bool = True, primary_a: Bus | Terminal | None = None,
                  primary_b: Bus | Terminal | None = None, secondary_a: Bus | Terminal | None = None,
                  secondary_b: Bus | Terminal | None = None, transaction: Transaction) -> ApplicationResult[PT]:
        self._require_transaction(transaction); self._require_id(pt_id, "pt_id")
        endpoints = {"primary_a": primary_a, "primary_b": primary_b, "secondary_a": secondary_a, "secondary_b": secondary_b}
        for field, endpoint in endpoints.items():
            if endpoint is not None: self._validate_endpoint(endpoint, field)
        self._ensure_not_exists("pt", pt_id, "PT")
        pt = PT(id=pt_id, name=name, primary_voltage_kv=primary_voltage_kv, secondary_voltage_v=secondary_voltage_v,
                accuracy_class=accuracy_class, burden_va=burden_va, phase_displacement_deg=phase_displacement_deg,
                in_service=in_service, primary_a=primary_a, primary_b=primary_b, secondary_a=secondary_a, secondary_b=secondary_b)
        self._network.add_potential_transformer(pt)
        transaction.record_undo(lambda pt=pt: self._network.remove_potential_transformer(pt))
        return self._success(pt, "pt", pt_id, f"PT created: {pt_id}")

    def update_pt(self, *, pt_id: str, name: str | None = None, primary_voltage_kv: float | None = None,
                  secondary_voltage_v: float | None = None, accuracy_class: str | None = None,
                  burden_va: float | None = None, phase_displacement_deg: float | None = None,
                  in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[PT]:
        self._require_transaction(transaction); self._require_id(pt_id, "pt_id")
        pt = self._get_required("pt", pt_id, "PT"); self._require_type(pt, PT, pt_id, "PT")
        values = (name, primary_voltage_kv, secondary_voltage_v, accuracy_class, burden_va, phase_displacement_deg, in_service)
        if all(v is None for v in values): raise ValueError("UpdatePTCommand requires at least one mutable PT field.")
        old = {"name": pt.name, "primary_voltage_kv": pt.primary_voltage_kv, "secondary_voltage_v": pt.secondary_voltage_v,
               "accuracy_class": pt.accuracy_class, "burden_va": pt.burden_va,
               "phase_displacement_deg": pt.phase_displacement_deg, "in_service": pt.in_service}
        for key, value in (("name", name), ("primary_voltage_kv", primary_voltage_kv), ("secondary_voltage_v", secondary_voltage_v),
                           ("accuracy_class", accuracy_class), ("burden_va", burden_va), ("phase_displacement_deg", phase_displacement_deg), ("in_service", in_service)):
            if value is not None: setattr(pt, key, value)
        def restore() -> None:
            for key, value in old.items(): setattr(pt, key, value)
        transaction.record_undo(restore)
        return self._success(pt, "pt", pt_id, f"PT updated: {pt_id}")

    def delete_pt(self, *, pt_id: str, transaction: Transaction) -> ApplicationResult[PT]:
        self._require_transaction(transaction); self._require_id(pt_id, "pt_id")
        pt = self._get_required("pt", pt_id, "PT"); self._require_type(pt, PT, pt_id, "PT")
        self._network.remove_potential_transformer(pt)
        transaction.record_undo(lambda pt=pt: self._network.add_potential_transformer(pt))
        return self._success(pt, "pt", pt_id, f"PT deleted: {pt_id}")

    def put_pt_in_service(self, *, pt_id: str, transaction: Transaction) -> ApplicationResult[PT]:
        return self._set_service(pt_id=pt_id, in_service=True, transaction=transaction)

    def take_pt_out_of_service(self, *, pt_id: str, transaction: Transaction) -> ApplicationResult[PT]:
        return self._set_service(pt_id=pt_id, in_service=False, transaction=transaction)

    def _set_service(self, *, pt_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[PT]:
        self._require_transaction(transaction); self._require_id(pt_id, "pt_id")
        pt = self._get_required("pt", pt_id, "PT"); self._require_type(pt, PT, pt_id, "PT")
        old = pt.in_service; pt.set_in_service(in_service)
        transaction.record_undo(lambda pt=pt, old=old: pt.set_in_service(old))
        return self._success(pt, "pt", pt_id, f"PT {'put in service' if in_service else 'taken out of service'}: {pt_id}")


__all__ = ["PTModelService"]
