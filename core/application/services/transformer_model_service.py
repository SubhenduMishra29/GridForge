"""Application service boundary for Transformer mutations.

Author: Subhendu Mishra

Transformer impedance reference voltage is explicit engineering input.
It is never derived from endpoint connectivity and is persisted on the
Transformer as ``impedance_base_voltage_kv`` for deterministic study
preparation.
"""

from __future__ import annotations

from typing import Any

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.model.terminal import Terminal
from core.model.transformer import Transformer, TransformerWindingConnection
from core.model.transformer_zero_sequence_contracts import TransformerVectorGroupConfiguration, TransformerZeroSequenceTestConfiguration
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
        endpoint_from: Bus | Terminal | None = None,
        endpoint_to: Bus | Terminal | None = None,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        impedance_basis: str,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        impedance_base_mva: float | None = None,
        impedance_base_voltage_kv: float | None = None,
        hv_winding_connection: TransformerWindingConnection | str | None = None,
        lv_winding_connection: TransformerWindingConnection | str | None = None,
        hv_neutral_grounding_impedance_ohm: complex | None = None,
        lv_neutral_grounding_impedance_ohm: complex | None = None,
        hv_terminal_role: str | None = None,
        lv_terminal_role: str | None = None,
        impedance_reference_winding: str | None = None,
        zero_sequence_resistance_ohm: float | None = None,
        zero_sequence_reactance_ohm: float | None = None,
        core_construction: Any | None = None,
        zero_sequence_test_basis: str | None = None,
        vector_group_configuration: TransformerVectorGroupConfiguration | None = None,
        zero_sequence_test_configuration: TransformerZeroSequenceTestConfiguration | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction)
        self._require_id(transformer_id, "transformer_id")
        if endpoint_from is not None:
            self._validate_endpoint(endpoint_from, "endpoint_from")
        if endpoint_to is not None:
            self._validate_endpoint(endpoint_to, "endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:
            self._require_distinct_endpoints(endpoint_from, endpoint_to, "INVALID_TRANSFORMER_ENDPOINTS", "Transformer", transformer_id)
        self._ensure_not_exists("transformer", transformer_id, "Transformer")

        # Transformer impedance reference voltage is engineering input, never
        # inferred from an absent endpoint. A connected transformer may still
        # be created with explicit endpoint references, but placement does not
        # require them.
        if impedance_base_voltage_kv is None:
            raise ValueError(
                "Transformer impedance_base_voltage_kv must be explicitly declared; "
                "it cannot be inferred from endpoint connectivity."
            )
        impedance_base_voltage_kv = float(impedance_base_voltage_kv)
        if impedance_base_voltage_kv <= 0.0:
            raise ValueError("Transformer impedance_base_voltage_kv must be greater than zero.")

        transformer = Transformer(
            id=transformer_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            impedance_basis=impedance_basis,
            tap=tap,
            shift=shift,
            name="" if name is None else name,
            rate_mva=rate_mva,
            impedance_base_mva=impedance_base_mva,
            impedance_base_voltage_kv=impedance_base_voltage_kv,
            hv_winding_connection=hv_winding_connection,
            lv_winding_connection=lv_winding_connection,
            hv_neutral_grounding_impedance_ohm=hv_neutral_grounding_impedance_ohm,
            lv_neutral_grounding_impedance_ohm=lv_neutral_grounding_impedance_ohm,
            hv_terminal_role=hv_terminal_role,
            lv_terminal_role=lv_terminal_role,
            impedance_reference_winding=impedance_reference_winding,
            zero_sequence_resistance_ohm=zero_sequence_resistance_ohm,
            zero_sequence_reactance_ohm=zero_sequence_reactance_ohm,
            core_construction=core_construction,
            zero_sequence_test_basis=zero_sequence_test_basis,
            vector_group_configuration=vector_group_configuration,
            zero_sequence_test_configuration=zero_sequence_test_configuration,
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
        hv_winding_connection: TransformerWindingConnection | str | None = None,
        lv_winding_connection: TransformerWindingConnection | str | None = None,
        hv_neutral_grounding_impedance_ohm: complex | None = None,
        lv_neutral_grounding_impedance_ohm: complex | None = None,
        hv_terminal_role: str | None = None,
        lv_terminal_role: str | None = None,
        impedance_reference_winding: str | None = None,
        zero_sequence_resistance_ohm: float | None = None,
        zero_sequence_reactance_ohm: float | None = None,
        core_construction: Any | None = None,
        zero_sequence_test_basis: str | None = None,
        vector_group_configuration: TransformerVectorGroupConfiguration | None = None,
        zero_sequence_test_configuration: TransformerZeroSequenceTestConfiguration | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction)
        self._require_id(transformer_id, "transformer_id")
        transformer = self._get_required("transformer", transformer_id, "Transformer")
        self._require_type(transformer, Transformer, transformer_id, "Transformer")

        values = (
            name, r, x, b, impedance_basis, impedance_base_mva,
            tap, shift, rate_mva, in_service,
            hv_winding_connection, lv_winding_connection,
            hv_neutral_grounding_impedance_ohm, lv_neutral_grounding_impedance_ohm,
            hv_terminal_role, lv_terminal_role, impedance_reference_winding,
            zero_sequence_resistance_ohm, zero_sequence_reactance_ohm,
            core_construction, zero_sequence_test_basis,
            vector_group_configuration, zero_sequence_test_configuration,
        )
        if all(value is None for value in values):
            raise ValueError("At least one Transformer configuration field must be specified.")
        if in_service is not None and not isinstance(in_service, bool):
            raise TypeError("in_service must be a bool.")

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
            "hv_winding_connection": transformer.hv_winding_connection,
            "lv_winding_connection": transformer.lv_winding_connection,
            "hv_neutral_grounding_impedance_ohm": transformer.hv_neutral_grounding_impedance_ohm,
            "lv_neutral_grounding_impedance_ohm": transformer.lv_neutral_grounding_impedance_ohm,
            "hv_terminal_role": transformer.hv_terminal_role,
            "lv_terminal_role": transformer.lv_terminal_role,
            "impedance_reference_winding": transformer.impedance_reference_winding,
            "zero_sequence_resistance_ohm": transformer.zero_sequence_resistance_ohm,
            "zero_sequence_reactance_ohm": transformer.zero_sequence_reactance_ohm,
            "core_construction": transformer.core_construction,
            "zero_sequence_test_basis": transformer.zero_sequence_test_basis,
            "vector_group_configuration": transformer.vector_group_configuration,
            "zero_sequence_test_configuration": transformer.zero_sequence_test_configuration,
        }
        service_state_changed = (
            in_service is not None and in_service != old_state["in_service"]
        )

        # Transformer.update_configuration validates the complete candidate
        # and restores its prior state if the candidate is invalid.
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
            hv_winding_connection=hv_winding_connection,
            lv_winding_connection=lv_winding_connection,
            hv_neutral_grounding_impedance_ohm=hv_neutral_grounding_impedance_ohm,
            lv_neutral_grounding_impedance_ohm=lv_neutral_grounding_impedance_ohm,
            hv_terminal_role=hv_terminal_role,
            lv_terminal_role=lv_terminal_role,
            impedance_reference_winding=impedance_reference_winding,
            zero_sequence_resistance_ohm=zero_sequence_resistance_ohm,
            zero_sequence_reactance_ohm=zero_sequence_reactance_ohm,
            core_construction=core_construction,
            zero_sequence_test_basis=zero_sequence_test_basis,
            vector_group_configuration=vector_group_configuration,
            zero_sequence_test_configuration=zero_sequence_test_configuration,
        )

        if service_state_changed:
            self._network.invalidate_topology()

        def restore() -> None:
            transformer.update_configuration(
                **old_state,
                _replace_winding_configuration=True,
            )
            if service_state_changed:
                self._network.invalidate_topology()

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
