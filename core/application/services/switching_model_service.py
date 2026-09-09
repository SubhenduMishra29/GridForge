"""Application service boundary for switching-device mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.breaker import Breaker
from core.model.bus import Bus
from core.model.disconnector import Disconnector
from core.model.fuse import Fuse
from core.model.switch import Switch
from core.model.terminal import Terminal
from core.network.network import Network


class SwitchingModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for switching devices."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_switch(
        self, *, switch_id: str, name: str = "",
        endpoint_a: Bus | Terminal | None = None,
        endpoint_b: Bus | Terminal | None = None,
        closed: bool = False, in_service: bool = True,
        normally_closed: bool | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Switch]:
        self._require_transaction(transaction)
        self._require_id(switch_id, "switch_id")
        if endpoint_a is not None:
            self._validate_endpoint(endpoint_a, "endpoint_a")
        if endpoint_b is not None:
            self._validate_endpoint(endpoint_b, "endpoint_b")
        if endpoint_a is not None and endpoint_b is not None:
            self._require_distinct_endpoints(endpoint_a, endpoint_b, "INVALID_SWITCH_ENDPOINTS", "Switch", switch_id)
        self._ensure_not_exists("switch", switch_id, "Switch")
        switch = Switch(id=switch_id, name=name, endpoint_a=endpoint_a, endpoint_b=endpoint_b,
                        closed=closed, in_service=in_service, normally_closed=normally_closed,
                        rated_voltage_kv=rated_voltage_kv, rated_current_a=rated_current_a)
        self._network.add_switch(switch)
        transaction.record_undo(lambda switch=switch: self._network.remove_switch(switch))
        return self._success(switch, "switch", switch_id, f"Switch created: {switch_id}")

    def update_switch(
        self, *, switch_id: str, name: str | None = None,
        closed: bool | None = None, in_service: bool | None = None,
        normally_closed: bool | None = None, rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None, transaction: Transaction,
    ) -> ApplicationResult[Switch]:
        self._require_transaction(transaction); self._require_id(switch_id, "switch_id")
        switch = self._get_required("switch", switch_id, "Switch"); self._require_type(switch, Switch, switch_id, "Switch")
        if all(v is None for v in (name, closed, in_service, normally_closed, rated_voltage_kv, rated_current_a)):
            raise DomainError(code="NO_SWITCH_UPDATE", message="At least one mutable Switch property must be specified.", details={"switch_id": switch_id})
        old = {"name": switch.name, "closed": switch.closed, "in_service": switch.in_service,
               "normally_closed": switch.normally_closed, "rated_voltage_kv": switch.rated_voltage_kv,
               "rated_current_a": switch.rated_current_a}
        if name is not None: switch.name = name
        if closed is not None: switch.set_closed(closed)
        if in_service is not None: switch.set_in_service(in_service)
        if normally_closed is not None: switch.set_normally_closed(normally_closed)
        if rated_voltage_kv is not None: switch.rated_voltage_kv = rated_voltage_kv
        if rated_current_a is not None: switch.rated_current_a = rated_current_a
        def restore() -> None:
            switch.name = old["name"]; switch.set_closed(old["closed"]); switch.set_in_service(old["in_service"])
            switch.set_normally_closed(old["normally_closed"]); switch.rated_voltage_kv = old["rated_voltage_kv"]
            switch.rated_current_a = old["rated_current_a"]
        transaction.record_undo(restore)
        return self._success(switch, "switch", switch_id, f"Switch updated: {switch_id}")

    def delete_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction); self._require_id(switch_id, "switch_id")
        switch = self._get_required("switch", switch_id, "Switch"); self._require_type(switch, Switch, switch_id, "Switch")
        self._network.remove_switch(switch)
        transaction.record_undo(lambda switch=switch: self._network.add_switch(switch))
        return self._success(switch, "switch", switch_id, f"Switch deleted: {switch_id}")

    def open_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._set_switch_closed(switch_id=switch_id, closed=False, transaction=transaction)

    def close_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._set_switch_closed(switch_id=switch_id, closed=True, transaction=transaction)

    def put_switch_in_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._set_switch_service(switch_id=switch_id, in_service=True, transaction=transaction)

    def take_switch_out_of_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._set_switch_service(switch_id=switch_id, in_service=False, transaction=transaction)

    def _set_switch_closed(self, *, switch_id: str, closed: bool, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction); self._require_id(switch_id, "switch_id")
        switch = self._get_required("switch", switch_id, "Switch"); self._require_type(switch, Switch, switch_id, "Switch")
        old = switch.closed; switch.set_closed(closed)
        transaction.record_undo(lambda switch=switch, old=old: switch.set_closed(old))
        return self._success(switch, "switch", switch_id, f"Switch {'closed' if closed else 'opened'}: {switch_id}")

    def _set_switch_service(self, *, switch_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction); self._require_id(switch_id, "switch_id")
        switch = self._get_required("switch", switch_id, "Switch"); self._require_type(switch, Switch, switch_id, "Switch")
        old = switch.in_service; switch.set_in_service(in_service)
        transaction.record_undo(lambda switch=switch, old=old: switch.set_in_service(old))
        return self._success(switch, "switch", switch_id, f"Switch {'put in service' if in_service else 'taken out of service'}: {switch_id}")

    # ------------------------------------------------------------------
    # Breaker
    # ------------------------------------------------------------------

    def create_breaker(
        self, *, breaker_id: str, endpoint_from: Bus | Terminal | None = None,
        endpoint_to: Bus | Terminal | None = None, name: str = "",
        in_service: bool = True, closed: bool = True, failed: bool = False,
        voltage_kv: float | None = None, current_a: float | None = None,
        interrupting_ka: float | None = None, transaction: Transaction,
    ) -> ApplicationResult[Breaker]:
        self._require_transaction(transaction); self._require_id(breaker_id, "breaker_id")
        if endpoint_from is not None: self._validate_endpoint(endpoint_from, "endpoint_from")
        if endpoint_to is not None: self._validate_endpoint(endpoint_to, "endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:
            self._require_distinct_endpoints(endpoint_from, endpoint_to, "INVALID_BREAKER_ENDPOINTS", "Breaker", breaker_id)
        self._ensure_not_exists("breaker", breaker_id, "Breaker")
        breaker = Breaker(id=breaker_id, endpoint_from=endpoint_from, endpoint_to=endpoint_to,
                          name=name, in_service=in_service, closed=closed, failed=failed,
                          voltage_kv=voltage_kv, current_a=current_a, interrupting_ka=interrupting_ka)
        self._network.add_breaker(breaker)
        transaction.record_undo(lambda breaker=breaker: self._network.remove_breaker(breaker))
        return self._success(breaker, "breaker", breaker_id, f"Breaker created: {breaker_id}")

    def update_breaker(
        self, *, breaker_id: str, name: str | None = None,
        in_service: bool | None = None, closed: bool | None = None,
        failed: bool | None = None, voltage_kv: float | None = None,
        current_a: float | None = None, interrupting_ka: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Breaker]:
        self._require_transaction(transaction); self._require_id(breaker_id, "breaker_id")
        breaker = self._get_required("breaker", breaker_id, "Breaker"); self._require_type(breaker, Breaker, breaker_id, "Breaker")
        if all(v is None for v in (name, in_service, closed, failed, voltage_kv, current_a, interrupting_ka)):
            raise DomainError(code="NO_BREAKER_UPDATE", message="At least one mutable Breaker property must be specified.", details={"breaker_id": breaker_id})
        old = {"name": breaker.name, "in_service": breaker.in_service, "closed": breaker.closed,
               "failed": breaker.failed, "voltage_kv": breaker.voltage_kv,
               "current_a": breaker.current_a, "interrupting_ka": breaker.interrupting_ka}
        if name is not None: breaker.name = name
        if in_service is not None: breaker.in_service = in_service
        if closed is not None: breaker.closed = closed
        if failed is not None: breaker.failed = failed
        if voltage_kv is not None: breaker.voltage_kv = voltage_kv
        if current_a is not None: breaker.current_a = current_a
        if interrupting_ka is not None: breaker.interrupting_ka = interrupting_ka
        def restore() -> None:
            breaker.name = old["name"]; breaker.in_service = old["in_service"]
            breaker.closed = old["closed"]; breaker.failed = old["failed"]
            breaker.voltage_kv = old["voltage_kv"]; breaker.current_a = old["current_a"]
            breaker.interrupting_ka = old["interrupting_ka"]
        transaction.record_undo(restore)
        return self._success(breaker, "breaker", breaker_id, f"Breaker updated: {breaker_id}")

    def delete_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        self._require_transaction(transaction); self._require_id(breaker_id, "breaker_id")
        breaker = self._get_required("breaker", breaker_id, "Breaker"); self._require_type(breaker, Breaker, breaker_id, "Breaker")
        self._network.remove_breaker(breaker)
        transaction.record_undo(lambda breaker=breaker: self._network.add_breaker(breaker))
        return self._success(breaker, "breaker", breaker_id, f"Breaker deleted: {breaker_id}")

    def open_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._set_breaker_closed(breaker_id=breaker_id, closed=False, transaction=transaction)

    def close_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._set_breaker_closed(breaker_id=breaker_id, closed=True, transaction=transaction)

    def put_breaker_in_service(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._set_breaker_service(breaker_id=breaker_id, in_service=True, transaction=transaction)

    def take_breaker_out_of_service(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._set_breaker_service(breaker_id=breaker_id, in_service=False, transaction=transaction)

    def trip_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        self._require_transaction(transaction); self._require_id(breaker_id, "breaker_id")
        breaker = self._get_required("breaker", breaker_id, "Breaker"); self._require_type(breaker, Breaker, breaker_id, "Breaker")
        old = breaker.closed; breaker.trip()
        transaction.record_undo(lambda breaker=breaker, old=old: breaker.close() if old else breaker.open())
        return self._success(breaker, "breaker", breaker_id, f"Breaker tripped: {breaker_id}")

    def _set_breaker_closed(self, *, breaker_id: str, closed: bool, transaction: Transaction) -> ApplicationResult[Breaker]:
        self._require_transaction(transaction); self._require_id(breaker_id, "breaker_id")
        breaker = self._get_required("breaker", breaker_id, "Breaker"); self._require_type(breaker, Breaker, breaker_id, "Breaker")
        old = breaker.closed
        if closed: breaker.close()
        else: breaker.open()
        transaction.record_undo(lambda breaker=breaker, old=old: breaker.close() if old else breaker.open())
        return self._success(breaker, "breaker", breaker_id, f"Breaker {'closed' if closed else 'opened'}: {breaker_id}")

    def _set_breaker_service(self, *, breaker_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Breaker]:
        self._require_transaction(transaction); self._require_id(breaker_id, "breaker_id")
        breaker = self._get_required("breaker", breaker_id, "Breaker"); self._require_type(breaker, Breaker, breaker_id, "Breaker")
        old = breaker.in_service; breaker.in_service = in_service
        transaction.record_undo(lambda breaker=breaker, old=old: setattr(breaker, "in_service", old))
        return self._success(breaker, "breaker", breaker_id, f"Breaker {'put in service' if in_service else 'taken out of service'}: {breaker_id}")

    def create_disconnector(
        self, *, disconnector_id: str, voltage_kv: float, rated_current_a: float,
        endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None,
        operating_time: float = 1.0, closed: bool = True, in_service: bool = True,
        name: str = "", transaction: Transaction,
    ) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction); self._require_id(disconnector_id, "disconnector_id")
        if endpoint_from is not None: self._validate_endpoint(endpoint_from, "endpoint_from")
        if endpoint_to is not None: self._validate_endpoint(endpoint_to, "endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:
            self._require_distinct_endpoints(endpoint_from, endpoint_to, "INVALID_DISCONNECTOR_ENDPOINTS", "Disconnector", disconnector_id)
        self._ensure_not_exists("disconnector", disconnector_id, "Disconnector")
        disconnector = Disconnector(id=disconnector_id, voltage_kv=voltage_kv, rated_current_a=rated_current_a,
                                    endpoint_from=endpoint_from, endpoint_to=endpoint_to, operating_time=operating_time,
                                    closed=closed, in_service=in_service, name=name)
        self._network.add_disconnector(disconnector)
        transaction.record_undo(lambda disconnector=disconnector: self._network.remove_disconnector(disconnector))
        return self._success(disconnector, "disconnector", disconnector_id, f"Disconnector created: {disconnector_id}")

    def update_disconnector(
        self, *, disconnector_id: str, voltage_kv: float | None = None,
        rated_current_a: float | None = None, operating_time: float | None = None,
        closed: bool | None = None, in_service: bool | None = None,
        name: str | None = None, transaction: Transaction,
    ) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction); self._require_id(disconnector_id, "disconnector_id")
        disconnector = self._get_required("disconnector", disconnector_id, "Disconnector")
        self._require_type(disconnector, Disconnector, disconnector_id, "Disconnector")
        if all(v is None for v in (voltage_kv, rated_current_a, operating_time, closed, in_service, name)):
            raise DomainError(code="NO_DISCONNECTOR_UPDATE", message="At least one mutable Disconnector property must be specified.", details={"disconnector_id": disconnector_id})
        old = {"voltage_kv": disconnector.voltage_kv, "rated_current_a": disconnector.rated_current_a,
               "operating_time": disconnector.operating_time, "closed": disconnector.closed,
               "in_service": disconnector.in_service, "name": disconnector.name}
        for key, value in (("voltage_kv", voltage_kv), ("rated_current_a", rated_current_a),
                           ("operating_time", operating_time), ("name", name)):
            if value is not None: setattr(disconnector, key, value)
        if closed is not None: disconnector.set_closed(closed)
        if in_service is not None: disconnector.set_in_service(in_service)
        def restore() -> None:
            disconnector.voltage_kv = old["voltage_kv"]; disconnector.rated_current_a = old["rated_current_a"]
            disconnector.operating_time = old["operating_time"]; disconnector.set_closed(old["closed"])
            disconnector.set_in_service(old["in_service"]); disconnector.name = old["name"]
        transaction.record_undo(restore)
        return self._success(disconnector, "disconnector", disconnector_id, f"Disconnector updated: {disconnector_id}")

    def delete_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction); self._require_id(disconnector_id, "disconnector_id")
        disconnector = self._get_required("disconnector", disconnector_id, "Disconnector")
        self._require_type(disconnector, Disconnector, disconnector_id, "Disconnector")
        self._network.remove_disconnector(disconnector)
        transaction.record_undo(lambda disconnector=disconnector: self._network.add_disconnector(disconnector))
        return self._success(disconnector, "disconnector", disconnector_id, f"Disconnector deleted: {disconnector_id}")

    def open_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._set_disconnector_closed(disconnector_id=disconnector_id, closed=False, transaction=transaction)

    def close_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._set_disconnector_closed(disconnector_id=disconnector_id, closed=True, transaction=transaction)

    def put_disconnector_in_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._set_disconnector_service(disconnector_id=disconnector_id, in_service=True, transaction=transaction)

    def take_disconnector_out_of_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._set_disconnector_service(disconnector_id=disconnector_id, in_service=False, transaction=transaction)

    def _set_disconnector_closed(self, *, disconnector_id: str, closed: bool, transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction); self._require_id(disconnector_id, "disconnector_id")
        disconnector = self._get_required("disconnector", disconnector_id, "Disconnector"); self._require_type(disconnector, Disconnector, disconnector_id, "Disconnector")
        old = disconnector.closed; disconnector.set_closed(closed)
        transaction.record_undo(lambda disconnector=disconnector, old=old: disconnector.set_closed(old))
        return self._success(disconnector, "disconnector", disconnector_id, f"Disconnector {'closed' if closed else 'opened'}: {disconnector_id}")

    def _set_disconnector_service(self, *, disconnector_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction); self._require_id(disconnector_id, "disconnector_id")
        disconnector = self._get_required("disconnector", disconnector_id, "Disconnector"); self._require_type(disconnector, Disconnector, disconnector_id, "Disconnector")
        old = disconnector.in_service; disconnector.set_in_service(in_service)
        transaction.record_undo(lambda disconnector=disconnector, old=old: disconnector.set_in_service(old))
        return self._success(disconnector, "disconnector", disconnector_id, f"Disconnector {'put in service' if in_service else 'taken out of service'}: {disconnector_id}")

    def create_fuse(
        self, *, fuse_id: str, name: str = "", rated_current_a: float = 1.0,
        rated_voltage_v: float = 1.0, interrupting_rating_ka: float = 0.0,
        in_service: bool = True, blown: bool = False, transaction: Transaction,
    ) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction); self._require_id(fuse_id, "fuse_id")
        self._ensure_not_exists("fuse", fuse_id, "Fuse")
        fuse = Fuse(id=fuse_id, name=name, rated_current_a=rated_current_a, rated_voltage_v=rated_voltage_v,
                    interrupting_rating_ka=interrupting_rating_ka, in_service=in_service, blown=blown)
        self._network.add_fuse(fuse)
        transaction.record_undo(lambda fuse=fuse: self._network.remove_fuse(fuse))
        return self._success(fuse, "fuse", fuse_id, f"Fuse created: {fuse_id}")

    def update_fuse(
        self, *, fuse_id: str, name: str | None = None, rated_current_a: float | None = None,
        rated_voltage_v: float | None = None, interrupting_rating_ka: float | None = None,
        in_service: bool | None = None, blown: bool | None = None, transaction: Transaction,
    ) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction); self._require_id(fuse_id, "fuse_id")
        fuse = self._get_required("fuse", fuse_id, "Fuse"); self._require_type(fuse, Fuse, fuse_id, "Fuse")
        if all(v is None for v in (name, rated_current_a, rated_voltage_v, interrupting_rating_ka, in_service, blown)):
            raise DomainError(code="NO_FUSE_UPDATE", message="At least one mutable Fuse property must be specified.", details={"fuse_id": fuse_id})
        old = {"name": fuse.name, "rated_current_a": fuse.rated_current_a, "rated_voltage_v": fuse.rated_voltage_v,
               "interrupting_rating_ka": fuse.interrupting_rating_ka, "in_service": fuse.in_service, "blown": fuse.blown}
        for key, value in (("name", name), ("rated_current_a", rated_current_a),
                           ("rated_voltage_v", rated_voltage_v), ("interrupting_rating_ka", interrupting_rating_ka)):
            if value is not None: setattr(fuse, key, value)
        if in_service is not None: fuse.set_in_service(in_service)
        if blown is not None: fuse.blow() if blown else fuse.reset()
        def restore() -> None:
            fuse.name = old["name"]; fuse.rated_current_a = old["rated_current_a"]
            fuse.rated_voltage_v = old["rated_voltage_v"]; fuse.interrupting_rating_ka = old["interrupting_rating_ka"]
            fuse.set_in_service(old["in_service"]); fuse.blow() if old["blown"] else fuse.reset()
        transaction.record_undo(restore)
        return self._success(fuse, "fuse", fuse_id, f"Fuse updated: {fuse_id}")

    def delete_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction); self._require_id(fuse_id, "fuse_id")
        fuse = self._get_required("fuse", fuse_id, "Fuse"); self._require_type(fuse, Fuse, fuse_id, "Fuse")
        self._network.remove_fuse(fuse)
        transaction.record_undo(lambda fuse=fuse: self._network.add_fuse(fuse))
        return self._success(fuse, "fuse", fuse_id, f"Fuse deleted: {fuse_id}")

    def blow_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction); self._require_id(fuse_id, "fuse_id")
        fuse = self._get_required("fuse", fuse_id, "Fuse"); self._require_type(fuse, Fuse, fuse_id, "Fuse")
        old = fuse.blown; fuse.blow()
        transaction.record_undo(lambda fuse=fuse, old=old: fuse.reset() if not old else fuse.blow())
        return self._success(fuse, "fuse", fuse_id, f"Fuse blown: {fuse_id}")

    def reset_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction); self._require_id(fuse_id, "fuse_id")
        fuse = self._get_required("fuse", fuse_id, "Fuse"); self._require_type(fuse, Fuse, fuse_id, "Fuse")
        old = fuse.blown; fuse.reset()
        transaction.record_undo(lambda fuse=fuse, old=old: fuse.blow() if old else fuse.reset())
        return self._success(fuse, "fuse", fuse_id, f"Fuse reset: {fuse_id}")

    def put_fuse_in_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._set_fuse_service(fuse_id=fuse_id, in_service=True, transaction=transaction)

    def take_fuse_out_of_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._set_fuse_service(fuse_id=fuse_id, in_service=False, transaction=transaction)

    def _set_fuse_service(self, *, fuse_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction); self._require_id(fuse_id, "fuse_id")
        fuse = self._get_required("fuse", fuse_id, "Fuse"); self._require_type(fuse, Fuse, fuse_id, "Fuse")
        old = fuse.in_service; fuse.set_in_service(in_service)
        transaction.record_undo(lambda fuse=fuse, old=old: fuse.set_in_service(old))
        return self._success(fuse, "fuse", fuse_id, f"Fuse {'put in service' if in_service else 'taken out of service'}: {fuse_id}")


__all__ = ["SwitchingModelService"]
