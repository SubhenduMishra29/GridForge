# ============================================================
# File: core/application/services/grid_model_service.py
# GridForge V2 — Grid Model Service
# ============================================================

"""Application service owning Grid mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.grid import Grid
from core.model.terminal import Terminal
from core.network.network import Network


class GridModelService(ModelServiceSupport):
    """Own Grid mutation operations while preserving the application boundary."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_grid(self, *, grid_id: str, endpoint: Bus | Terminal | None = None, name: str | None = None, nominal_voltage_kv: float = 0.0, frequency_hz: float = 50.0, voltage_pu: float = 1.0, angle_deg: float = 0.0, p_mw: float = 0.0, q_mvar: float = 0.0, short_circuit_mva: float = 0.0, x_over_r: float = 0.0, z1_pu: complex = 0j, z2_pu: complex = 0j, z0_pu: complex = 0j, in_service: bool = True, grounded: bool = True, transaction: Transaction) -> ApplicationResult[Grid]:
        self._require_transaction(transaction); self._require_id(grid_id, "grid_id")
        if endpoint is not None: self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("grid", grid_id, "Grid")
        grid = Grid(id=grid_id, name="" if name is None else name, endpoint=endpoint, nominal_voltage_kv=nominal_voltage_kv, frequency_hz=frequency_hz, voltage_pu=voltage_pu, angle_deg=angle_deg, p_mw=p_mw, q_mvar=q_mvar, short_circuit_mva=short_circuit_mva, x_over_r=x_over_r, z1_pu=z1_pu, z2_pu=z2_pu, z0_pu=z0_pu, in_service=in_service, grounded=grounded)
        self._network.add_grid(grid); transaction.record_undo(lambda grid=grid: self._network.remove_grid(grid)); return self._success(grid, "grid", grid_id, f"Grid created: {grid_id}")

    def update_grid(self, *, grid_id: str, name: str | None = None, nominal_voltage_kv: float | None = None, frequency_hz: float | None = None, voltage_pu: float | None = None, angle_deg: float | None = None, p_mw: float | None = None, q_mvar: float | None = None, short_circuit_mva: float | None = None, x_over_r: float | None = None, z1_pu: complex | None = None, z2_pu: complex | None = None, z0_pu: complex | None = None, in_service: bool | None = None, grounded: bool | None = None, transaction: Transaction) -> ApplicationResult[Grid]:
        self._require_transaction(transaction); self._require_id(grid_id, "grid_id"); grid = self._get_required("grid", grid_id, "Grid"); self._require_type(grid, Grid, grid_id, "Grid")
        if all(v is None for v in (name, nominal_voltage_kv, frequency_hz, voltage_pu, angle_deg, p_mw, q_mvar, short_circuit_mva, x_over_r, z1_pu, z2_pu, z0_pu, in_service, grounded)): raise DomainError(code="NO_GRID_UPDATE", message="At least one mutable Grid property must be specified.", details={"grid_id": grid_id})
        old = {"name": grid.name, "nominal_voltage_kv": grid.nominal_voltage_kv, "frequency_hz": grid.frequency_hz, "voltage_pu": grid.voltage_pu, "angle_deg": grid.angle_deg, "p_mw": grid.p_mw, "q_mvar": grid.q_mvar, "short_circuit_mva": grid.short_circuit_mva, "x_over_r": grid.x_over_r, "z1_pu": grid.z1_pu, "z2_pu": grid.z2_pu, "z0_pu": grid.z0_pu, "in_service": grid.in_service, "grounded": grid.grounded}
        if name is not None: grid.name = name
        if nominal_voltage_kv is not None: grid.nominal_voltage_kv = nominal_voltage_kv
        if frequency_hz is not None: grid.frequency_hz = frequency_hz
        if short_circuit_mva is not None: grid.short_circuit_mva = short_circuit_mva
        if x_over_r is not None: grid.x_over_r = x_over_r
        if grounded is not None: grid.grounded = grounded
        if voltage_pu is not None or angle_deg is not None: grid.set_voltage(grid.voltage_pu if voltage_pu is None else voltage_pu, grid.angle_deg if angle_deg is None else angle_deg)
        if p_mw is not None or q_mvar is not None: grid.set_power(grid.p_mw if p_mw is None else p_mw, grid.q_mvar if q_mvar is None else q_mvar)
        if z1_pu is not None or z2_pu is not None or z0_pu is not None: grid.set_sequence_impedances(grid.z1_pu if z1_pu is None else z1_pu, grid.z2_pu if z2_pu is None else z2_pu, grid.z0_pu if z0_pu is None else z0_pu)
        if in_service is not None: grid.put_in_service() if in_service else grid.take_out_of_service()
        def restore() -> None:
            grid.name = old["name"]; grid.nominal_voltage_kv = old["nominal_voltage_kv"]; grid.frequency_hz = old["frequency_hz"]; grid.short_circuit_mva = old["short_circuit_mva"]; grid.x_over_r = old["x_over_r"]; grid.grounded = old["grounded"]; grid.set_voltage(old["voltage_pu"], old["angle_deg"]); grid.set_power(old["p_mw"], old["q_mvar"]); grid.set_sequence_impedances(old["z1_pu"], old["z2_pu"], old["z0_pu"]); grid.put_in_service() if old["in_service"] else grid.take_out_of_service()
        transaction.record_undo(restore); return self._success(grid, "grid", grid_id, f"Grid updated: {grid_id}")

    def delete_grid(self, *, grid_id: str, transaction: Transaction) -> ApplicationResult[Grid]:
        self._require_transaction(transaction); self._require_id(grid_id, "grid_id"); grid = self._get_required("grid", grid_id, "Grid"); self._require_type(grid, Grid, grid_id, "Grid"); self._network.remove_grid(grid); transaction.record_undo(lambda grid=grid: self._network.add_grid(grid)); return self._success(grid, "grid", grid_id, f"Grid deleted: {grid_id}")


__all__ = ["GridModelService"]
