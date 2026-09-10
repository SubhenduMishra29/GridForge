"""Targeted tests for the canonical .gridforge project package.

Author: Subhendu Mishra
"""

from zipfile import ZipFile
import json

from core.model.bus import Bus
from core.model.transformer import Transformer
from core.network.network import Network
from projects.gridforge_package import GridForgePackage, Project


def test_project_round_trip_preserves_transformer_basis_and_identity(tmp_path):
    network = Network()
    from_bus = Bus("BUS-1", name="HV", nominal_voltage_kv=132.0)
    to_bus = Bus("BUS-2", name="LV", nominal_voltage_kv=33.0)
    transformer = Transformer(
        "TR-1",
        endpoint_from=from_bus,
        endpoint_to=to_bus,
        r=0.01,
        x=0.08,
        b=0.002,
        impedance_basis="pu",
        impedance_base_mva=50.0,
        impedance_base_voltage_kv=132.0,
        rate_mva=50.0,
    )
    network.add_bus(from_bus)
    network.add_bus(to_bus)
    network.add_transformer(transformer)

    original = Project(
        network=network,
        metadata={"name": "reference"},
        sld_layout={"TR-1": {"x": 120.0, "y": 80.0}},
    )
    path = tmp_path / "project.gridforge"
    GridForgePackage.save(original, path)

    with ZipFile(path) as archive:
        assert set(archive.namelist()) == {"manifest.json", "project.json"}
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["root"] == "Project"
        assert manifest["format_version"] == 1

    restored = GridForgePackage.load(path)
    restored_transformer = restored.network.get_by_id("transformer", "TR-1")

    assert restored.metadata == original.metadata
    assert restored.sld_layout == original.sld_layout
    assert restored.network.get_by_id("bus", "BUS-1").name == "HV"
    assert restored_transformer.id == "TR-1"
    assert restored_transformer.impedance_basis == "pu"
    assert restored_transformer.impedance_base_mva == 50.0
    assert restored_transformer.impedance_base_voltage_kv == 132.0
    assert restored_transformer.r == 0.01
    assert restored_transformer.x == 0.08
    assert restored_transformer.b == 0.002
    assert restored_transformer.endpoint_from.id == "BUS-1"
    assert restored_transformer.endpoint_to.id == "BUS-2"


def test_legacy_transformer_without_explicit_basis_is_rejected():
    from core.persistence.migration import AmbiguousElectricalDataError, LegacyElectricalDataMigration

    try:
        LegacyElectricalDataMigration().migrate("transformer", {"r": 0.01, "x": 0.08, "b": 0.0})
    except AmbiguousElectricalDataError:
        return
    raise AssertionError("Ambiguous legacy transformer impedance must not be inferred.")
