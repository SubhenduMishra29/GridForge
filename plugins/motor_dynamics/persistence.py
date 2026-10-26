"""Versioned, validation-first persistence adapter; archive parsing is side-effect free."""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION = 1
class MotorPluginPersistenceHandler:
    def __init__(self, application: Any = None) -> None: self.application = application
    def serialize_plugin_data(self) -> dict[str, Any]:
        # Persist domain identifiers/configuration only; never Qt objects or solver buffers.
        store = getattr(self.application, "motor_registry", None)
        records = store.export_records() if store is not None and hasattr(store, "export_records") else []
        return {"schema_version": SCHEMA_VERSION, "motors": deepcopy(records)}
    def deserialize_plugin_data(self, payload: Mapping[str, Any]) -> None:
        if not isinstance(payload, Mapping) or payload.get("schema_version") != SCHEMA_VERSION: raise ValueError("unsupported motor plugin persistence schema")
        records = payload.get("motors", [])
        if not isinstance(records, list): raise ValueError("motors must be a list")
        ids = set()
        for item in records:
            if not isinstance(item, dict) or not isinstance(item.get("motor_id"), str) or not item["motor_id"]: raise ValueError("each motor record requires motor_id")
            if item["motor_id"] in ids: raise ValueError("duplicate motor_id")
            ids.add(item["motor_id"])
            if "parameters" in item and not isinstance(item["parameters"], dict): raise ValueError("parameters must be an object")
        # Mutate only through an application-owned atomic import service.
        importer = getattr(self.application, "import_motor_records_atomic", None)
        if records and not callable(importer): raise RuntimeError("application does not expose import_motor_records_atomic")
        if callable(importer): importer(deepcopy(records))
