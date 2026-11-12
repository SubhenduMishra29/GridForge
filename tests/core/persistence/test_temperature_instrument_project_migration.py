from core.persistence.migration import ProjectPersistenceMigration


def test_schema_7_migration_adds_empty_temperature_inventory_without_inference():
    migrated = ProjectPersistenceMigration()._project_steps[7].migrate({
        "schema": 7,
        "project": {"project_id": "p-1", "name": "Legacy"},
        "instrumentation_wiring": {
            "schema": 2, "cables": [], "cores": [], "panel_wires": [],
            "signals": [], "signal_bindings": [], "tag_policy": [],
        },
        "measurement": {"channels": []},
    })
    assert migrated["schema"] == 8
    assert migrated["temperature_instruments"] == {
        "schema": 1, "instruments": [], "interfaces": [], "alarm_trip_bindings": [],
    }
    assert "temperature_instruments" not in {
        "schema": 7, "generic_rtd_records": [{"id": "legacy-rtd"}],
    }


def test_schema_7_migration_preserves_existing_temperature_payload():
    payload = {
        "schema": 7,
        "temperature_instruments": {
            "schema": 1, "instruments": [], "interfaces": [], "alarm_trip_bindings": [],
        },
    }
    migrated = ProjectPersistenceMigration()._project_steps[7].migrate(payload)
    assert migrated["temperature_instruments"] == payload["temperature_instruments"]
