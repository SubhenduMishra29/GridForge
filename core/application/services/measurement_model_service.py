"""Application service boundary for measurement transformer mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.ct import CTPolarity, CurrentTransformer
from core.model.cvt import CVTPolarity, CapacitiveVoltageTransformer
from core.model.terminal import Terminal
from core.network.network import Network


class MeasurementModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for CT and CVT equipment."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_current_transformer(
        self,
        *,
        ct_id: str,
        name: str = "",
        primary_rated_current_a: float = 100.0,
        secondary_rated_current_a: float = 5.0,
        burden_va: float | None = None,
        accuracy_class: str | None = None,
        frequency_hz: float = 50.0,
        polarity: CTPolarity | str = CTPolarity.P1_P2,
        in_service: bool = True,
        p1_endpoint: Bus | Terminal | None = None,
        p2_endpoint: Bus | Terminal | None = None,
        s1_endpoint: Bus | Terminal | None = None,
        s2_endpoint: Bus | Terminal | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[CurrentTransformer]:
        self._require_transaction(transaction)
        self._require_id(ct_id, "ct_id")
        endpoints = {
            "p1_endpoint": p1_endpoint,
            "p2_endpoint": p2_endpoint,
            "s1_endpoint": s1_endpoint,
            "s2_endpoint": s2_endpoint,
        }
        for field, endpoint in endpoints.items():
            if endpoint is not None:
                self._validate_endpoint(endpoint, field)
        self._ensure_not_exists("ct", ct_id, "CurrentTransformer")

        ct = CurrentTransformer(
            id=ct_id,
            name=name,
            primary_rated_current_a=primary_rated_current_a,
            secondary_rated_current_a=secondary_rated_current_a,
            burden_va=burden_va,
            accuracy_class=accuracy_class,
            frequency_hz=frequency_hz,
            polarity=polarity,
            in_service=in_service,
            p1_endpoint=p1_endpoint,
            p2_endpoint=p2_endpoint,
            s1_endpoint=s1_endpoint,
            s2_endpoint=s2_endpoint,
        )
        self._network.add_current_transformer(ct)
        transaction.record_undo(lambda ct=ct: self._network.remove_current_transformer(ct))
        return self._success(ct, "ct", ct_id, f"CurrentTransformer created: {ct_id}")

    def update_current_transformer(
        self,
        *,
        ct_id: str,
        name: str | None = None,
        primary_rated_current_a: float | None = None,
        secondary_rated_current_a: float | None = None,
        burden_va: float | None = None,
        accuracy_class: str | None = None,
        frequency_hz: float | None = None,
        polarity: CTPolarity | str | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[CurrentTransformer]:
        self._require_transaction(transaction)
        self._require_id(ct_id, "ct_id")
        ct = self._get_required("ct", ct_id, "CurrentTransformer")
        self._require_type(ct, CurrentTransformer, ct_id, "CurrentTransformer")
        values = (
            name, primary_rated_current_a, secondary_rated_current_a,
            burden_va, accuracy_class, frequency_hz, polarity, in_service,
        )
        if all(value is None for value in values):
            raise DomainError(
                code="NO_CT_UPDATE",
                message="At least one mutable CurrentTransformer property must be specified.",
                details={"ct_id": ct_id},
            )
        old = {
            "name": ct.name,
            "primary_rated_current_a": ct.primary_rated_current_a,
            "secondary_rated_current_a": ct.secondary_rated_current_a,
            "burden_va": ct.burden_va,
            "accuracy_class": ct.accuracy_class,
            "frequency_hz": ct.frequency_hz,
            "polarity": ct.polarity,
            "in_service": ct.in_service,
        }
        if name is not None:
            ct.name = name
        if primary_rated_current_a is not None:
            ct.primary_rated_current_a = primary_rated_current_a
        if secondary_rated_current_a is not None:
            ct.secondary_rated_current_a = secondary_rated_current_a
        if burden_va is not None:
            ct.burden_va = burden_va
        if accuracy_class is not None:
            ct.accuracy_class = accuracy_class
        if frequency_hz is not None:
            ct.frequency_hz = frequency_hz
        if polarity is not None:
            ct.polarity = polarity
        if in_service is not None:
            ct.in_service = in_service

        def restore() -> None:
            ct.name = old["name"]
            ct.primary_rated_current_a = old["primary_rated_current_a"]
            ct.secondary_rated_current_a = old["secondary_rated_current_a"]
            ct.burden_va = old["burden_va"]
            ct.accuracy_class = old["accuracy_class"]
            ct.frequency_hz = old["frequency_hz"]
            ct.polarity = old["polarity"]
            ct.in_service = old["in_service"]

        transaction.record_undo(restore)
        return self._success(ct, "ct", ct_id, f"CurrentTransformer updated: {ct_id}")

    def delete_current_transformer(
        self,
        *,
        ct_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[CurrentTransformer]:
        self._require_transaction(transaction)
        self._require_id(ct_id, "ct_id")
        ct = self._get_required("ct", ct_id, "CurrentTransformer")
        self._require_type(ct, CurrentTransformer, ct_id, "CurrentTransformer")
        self._network.remove_current_transformer(ct)
        transaction.record_undo(lambda ct=ct: self._network.add_current_transformer(ct))
        return self._success(ct, "ct", ct_id, f"CurrentTransformer deleted: {ct_id}")

    def put_current_transformer_in_service(self, *, ct_id: str, transaction: Transaction) -> ApplicationResult[CurrentTransformer]:
        return self._set_ct_service(ct_id=ct_id, in_service=True, transaction=transaction)

    def take_current_transformer_out_of_service(self, *, ct_id: str, transaction: Transaction) -> ApplicationResult[CurrentTransformer]:
        return self._set_ct_service(ct_id=ct_id, in_service=False, transaction=transaction)

    def _set_ct_service(self, *, ct_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[CurrentTransformer]:
        self._require_transaction(transaction)
        self._require_id(ct_id, "ct_id")
        ct = self._get_required("ct", ct_id, "CurrentTransformer")
        self._require_type(ct, CurrentTransformer, ct_id, "CurrentTransformer")
        old = ct.in_service
        ct.in_service = in_service
        transaction.record_undo(lambda ct=ct, old=old: setattr(ct, "in_service", old))
        state = "put in service" if in_service else "taken out of service"
        return self._success(ct, "ct", ct_id, f"CurrentTransformer {state}: {ct_id}")

    def create_capacitive_voltage_transformer(
        self,
        *,
        cvt_id: str,
        name: str = "",
        rated_primary_voltage_kv: float = 220.0,
        rated_secondary_voltage_v: float = 110.0,
        accuracy_class: str = "0.5",
        rated_burden_va: float = 100.0,
        polarity: CVTPolarity | str = CVTPolarity.NORMAL,
        frequency_hz: float = 50.0,
        in_service: bool = True,
        h1_endpoint: Bus | Terminal | None = None,
        h2_endpoint: Bus | Terminal | None = None,
        x1_endpoint: Bus | Terminal | None = None,
        x2_endpoint: Bus | Terminal | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[CapacitiveVoltageTransformer]:
        self._require_transaction(transaction)
        self._require_id(cvt_id, "cvt_id")
        endpoints = {
            "h1_endpoint": h1_endpoint,
            "h2_endpoint": h2_endpoint,
            "x1_endpoint": x1_endpoint,
            "x2_endpoint": x2_endpoint,
        }
        for field, endpoint in endpoints.items():
            if endpoint is not None:
                self._validate_endpoint(endpoint, field)
        self._ensure_not_exists("cvt", cvt_id, "CapacitiveVoltageTransformer")

        cvt = CapacitiveVoltageTransformer(
            id=cvt_id,
            name=name,
            rated_primary_voltage_kv=rated_primary_voltage_kv,
            rated_secondary_voltage_v=rated_secondary_voltage_v,
            accuracy_class=accuracy_class,
            rated_burden_va=rated_burden_va,
            polarity=polarity,
            frequency_hz=frequency_hz,
            in_service=in_service,
            h1_endpoint=h1_endpoint,
            h2_endpoint=h2_endpoint,
            x1_endpoint=x1_endpoint,
            x2_endpoint=x2_endpoint,
        )
        self._network.add_capacitive_voltage_transformer(cvt)
        transaction.record_undo(lambda cvt=cvt: self._network.remove_capacitive_voltage_transformer(cvt))
        return self._success(cvt, "cvt", cvt_id, f"CapacitiveVoltageTransformer created: {cvt_id}")

    def update_capacitive_voltage_transformer(
        self,
        *,
        cvt_id: str,
        name: str | None = None,
        rated_primary_voltage_kv: float | None = None,
        rated_secondary_voltage_v: float | None = None,
        accuracy_class: str | None = None,
        rated_burden_va: float | None = None,
        polarity: CVTPolarity | str | None = None,
        frequency_hz: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[CapacitiveVoltageTransformer]:
        self._require_transaction(transaction)
        self._require_id(cvt_id, "cvt_id")
        cvt = self._get_required("cvt", cvt_id, "CapacitiveVoltageTransformer")
        self._require_type(cvt, CapacitiveVoltageTransformer, cvt_id, "CapacitiveVoltageTransformer")
        values = (
            name, rated_primary_voltage_kv, rated_secondary_voltage_v,
            accuracy_class, rated_burden_va, polarity, frequency_hz, in_service,
        )
        if all(value is None for value in values):
            raise DomainError(
                code="NO_CVT_UPDATE",
                message="At least one mutable CapacitiveVoltageTransformer property must be specified.",
                details={"cvt_id": cvt_id},
            )
        old = {
            "name": cvt.name,
            "rated_primary_voltage_kv": cvt.rated_primary_voltage_kv,
            "rated_secondary_voltage_v": cvt.rated_secondary_voltage_v,
            "accuracy_class": cvt.accuracy_class,
            "rated_burden_va": cvt.rated_burden_va,
            "polarity": cvt.polarity,
            "frequency_hz": cvt.frequency_hz,
            "in_service": cvt.in_service,
        }
        if name is not None:
            cvt.name = name
        if rated_primary_voltage_kv is not None:
            cvt.rated_primary_voltage_kv = rated_primary_voltage_kv
        if rated_secondary_voltage_v is not None:
            cvt.rated_secondary_voltage_v = rated_secondary_voltage_v
        if accuracy_class is not None:
            cvt.accuracy_class = accuracy_class
        if rated_burden_va is not None:
            cvt.rated_burden_va = rated_burden_va
        if polarity is not None:
            cvt.polarity = polarity
        if frequency_hz is not None:
            cvt.frequency_hz = frequency_hz
        if in_service is not None:
            cvt.in_service = in_service

        def restore() -> None:
            cvt.name = old["name"]
            cvt.rated_primary_voltage_kv = old["rated_primary_voltage_kv"]
            cvt.rated_secondary_voltage_v = old["rated_secondary_voltage_v"]
            cvt.accuracy_class = old["accuracy_class"]
            cvt.rated_burden_va = old["rated_burden_va"]
            cvt.polarity = old["polarity"]
            cvt.frequency_hz = old["frequency_hz"]
            cvt.in_service = old["in_service"]

        transaction.record_undo(restore)
        return self._success(cvt, "cvt", cvt_id, f"CapacitiveVoltageTransformer updated: {cvt_id}")

    def delete_capacitive_voltage_transformer(
        self,
        *,
        cvt_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[CapacitiveVoltageTransformer]:
        self._require_transaction(transaction)
        self._require_id(cvt_id, "cvt_id")
        cvt = self._get_required("cvt", cvt_id, "CapacitiveVoltageTransformer")
        self._require_type(cvt, CapacitiveVoltageTransformer, cvt_id, "CapacitiveVoltageTransformer")
        self._network.remove_capacitive_voltage_transformer(cvt)
        transaction.record_undo(lambda cvt=cvt: self._network.add_capacitive_voltage_transformer(cvt))
        return self._success(cvt, "cvt", cvt_id, f"CapacitiveVoltageTransformer deleted: {cvt_id}")

    def put_capacitive_voltage_transformer_in_service(self, *, cvt_id: str, transaction: Transaction) -> ApplicationResult[CapacitiveVoltageTransformer]:
        return self._set_cvt_service(cvt_id=cvt_id, in_service=True, transaction=transaction)

    def take_capacitive_voltage_transformer_out_of_service(self, *, cvt_id: str, transaction: Transaction) -> ApplicationResult[CapacitiveVoltageTransformer]:
        return self._set_cvt_service(cvt_id=cvt_id, in_service=False, transaction=transaction)

    def _set_cvt_service(self, *, cvt_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[CapacitiveVoltageTransformer]:
        self._require_transaction(transaction)
        self._require_id(cvt_id, "cvt_id")
        cvt = self._get_required("cvt", cvt_id, "CapacitiveVoltageTransformer")
        self._require_type(cvt, CapacitiveVoltageTransformer, cvt_id, "CapacitiveVoltageTransformer")
        old = cvt.in_service
        cvt.in_service = in_service
        transaction.record_undo(lambda cvt=cvt, old=old: setattr(cvt, "in_service", old))
        state = "put in service" if in_service else "taken out of service"
        return self._success(cvt, "cvt", cvt_id, f"CapacitiveVoltageTransformer {state}: {cvt_id}")


__all__ = ["MeasurementModelService"]
