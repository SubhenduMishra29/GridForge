"""
GridForge Core Network Engine

File:
    core/network/network.py

Purpose:
    Central network model and orchestration layer for GridForge.

Responsibilities:
    - Maintain electrical equipment containers
    - Maintain network-wide system base
    - Maintain bus indexing
    - Coordinate topology management
    - Coordinate Y-bus construction
    - Coordinate power-flow analysis
    - Coordinate short-circuit analysis
    - Coordinate line and transformer flow calculations
    - Provide interfaces to protection and dynamic studies
    - Maintain analysis results and network state

Does NOT:
    - Perform numerical power-flow calculations
    - Assemble Newton-Raphson Jacobians
    - Solve numerical linear systems
    - Directly construct Y-bus internally
    - Perform short-circuit mathematics
    - Perform transient numerical integration
    - Make protection decisions

Architecture:

    Network
       │
       ├── Elements
       │     ├── Buses
       │     ├── Lines
       │     ├── Transformers
       │     └── Generators
       │
       ├── TopologyManager
       │
       ├── YBusBuilder
       │
       ├── Power Flow Solver
       │
       ├── Short Circuit Solver
       │
       ├── Protection
       │
       └── Dynamics

Important:
    Network is the MODEL/ORCHESTRATION boundary.

    Numerical algorithms belong under:
        core/solver/

    Electrical element models belong under:
        core/models/

    Network construction and topology belong under:
        core/network/
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from core.network.ybus import YBusBuilder
from core.network.topology import TopologyManager
from core.network.per_unit import PerUnitSystem


class Network:
    """
    Central GridForge electrical network model.

    The Network object owns the physical model of the electrical
    system and provides controlled entry points to analysis engines.

    Parameters
    ----------
    base_mva:
        System-wide MVA base used by the per-unit system.

    Notes
    -----
    The Network does not implement numerical algorithms itself.

    For example:

        network.build_ybus()

    delegates to:

        YBusBuilder

    Similarly:

        network.run_power_flow()

    delegates to the power-flow analysis/solver layer.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, base_mva: float = 100.0):

        if base_mva <= 0:
            raise ValueError(
                "Network base MVA must be positive"
            )

        # -----------------------------------------------------
        # SYSTEM BASE
        # -----------------------------------------------------

        self.base_mva = float(base_mva)

        self.per_unit = PerUnitSystem(
            base_mva=self.base_mva
        )

        # -----------------------------------------------------
        # ELECTRICAL ELEMENT CONTAINERS
        # -----------------------------------------------------

        self.buses: List[Any] = []

        self.lines: List[Any] = []

        self.transformers: List[Any] = []

        self.generators: List[Any] = []

        self.loads: List[Any] = []

        self.shunts: List[Any] = []

        # -----------------------------------------------------
        # BUS INDEX
        #
        # Maps:
        #
        #     bus.id → matrix index
        #
        # This is used by Y-bus and numerical solvers.
        # -----------------------------------------------------

        self.bus_index: Dict[Any, int] = {}

        # -----------------------------------------------------
        # NETWORK MATRICES
        # -----------------------------------------------------

        self.Ybus = None

        # -----------------------------------------------------
        # NETWORK SERVICES
        # -----------------------------------------------------

        self.topology = TopologyManager(
            self
        )

        self.ybus_builder = YBusBuilder(
            self
        )

        # -----------------------------------------------------
        # ANALYSIS RESULTS
        # -----------------------------------------------------

        self.power_flow_result = None

        self.fault_result = None

        self.line_flow_result = None

        self.transformer_flow_result = None

        # -----------------------------------------------------
        # EVENT / STUDY STATE
        # -----------------------------------------------------

        self.active_fault = None

        # -----------------------------------------------------
        # STATE FLAGS
        # -----------------------------------------------------

        self._topology_dirty = True

        self._ybus_dirty = True

    # =========================================================
    # ELEMENT MANAGEMENT
    # =========================================================

    def add_bus(self, bus):
        """
        Add a bus to the network.

        Bus IDs must be unique.
        """

        if bus is None:
            raise ValueError(
                "Cannot add None as a bus"
            )

        if bus.id in self.bus_index:
            raise ValueError(
                f"Duplicate bus ID: {bus.id}"
            )

        self.buses.append(bus)

        self._topology_dirty = True
        self._ybus_dirty = True

    # ---------------------------------------------------------

    def add_line(self, line):
        """
        Add a transmission/distribution line.
        """

        if line is None:
            raise ValueError(
                "Cannot add None as a line"
            )

        self.lines.append(line)

        self._topology_dirty = True
        self._ybus_dirty = True

    # ---------------------------------------------------------

    def add_transformer(self, transformer):
        """
        Add a transformer.
        """

        if transformer is None:
            raise ValueError(
                "Cannot add None as a transformer"
            )

        self.transformers.append(
            transformer
        )

        self._topology_dirty = True
        self._ybus_dirty = True

    # ---------------------------------------------------------

    def add_generator(self, generator):
        """
        Add a generator.
        """

        if generator is None:
            raise ValueError(
                "Cannot add None as a generator"
            )

        self.generators.append(
            generator
        )

    # ---------------------------------------------------------

    def add_load(self, load):
        """
        Add a load model.
        """

        if load is None:
            raise ValueError(
                "Cannot add None as a load"
            )

        self.loads.append(
            load
        )

    # ---------------------------------------------------------

    def add_shunt(self, shunt):
        """
        Add a shunt element.
        """

        if shunt is None:
            raise ValueError(
                "Cannot add None as a shunt"
            )

        self.shunts.append(
            shunt
        )

        self._ybus_dirty = True

    # =========================================================
    # BUS INDEXING
    # =========================================================

    def rebuild_bus_index(self):
        """
        Rebuild the bus ID → matrix index mapping.

        The mapping is deterministic and follows the order
        of self.buses.
        """

        self.bus_index.clear()

        for index, bus in enumerate(self.buses):

            if bus.id in self.bus_index:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

            self.bus_index[bus.id] = index

        return self.bus_index

    # =========================================================
    # TOPOLOGY
    # =========================================================

    def rebuild_topology(self):
        """
        Rebuild the electrical connectivity graph.
        """

        self.topology._dirty = True

        graph = self.topology.build()

        self._topology_dirty = False

        return graph

    # ---------------------------------------------------------

    def find_islands(self):
        """
        Return electrical network islands.
        """

        return self.topology.find_islands()

    # ---------------------------------------------------------

    def is_connected(self, bus_a, bus_b):
        """
        Check whether two buses are electrically connected.
        """

        return self.topology.is_connected(
            bus_a,
            bus_b
        )

    # =========================================================
    # Y-BUS
    # =========================================================

    def build_ybus(self):
        """
        Build the network Y-bus.

        IMPORTANT:
            Y-bus mathematics belongs exclusively to
            core/network/ybus.py.

        This method is only the Network-level API.
        """

        self.rebuild_bus_index()

        self.Ybus = self.ybus_builder.build()

        self._ybus_dirty = False

        return self.Ybus

    # =========================================================
    # POWER FLOW
    # =========================================================

    def run_power_flow(
        self,
        options=None
    ):
        """
        Run the AC power-flow analysis.

        The numerical solver resides under:

            core/solver/power_flow/

        Network only prepares and delegates the study.
        """

        # Import here to avoid unnecessary circular imports
        # during Network model initialization.
        from core.analysis.power_flow import (
            PowerFlowSolver
        )

        if self.Ybus is None or self._ybus_dirty:
            self.build_ybus()

        solver = PowerFlowSolver(
            self,
            options=options
        )

        self.power_flow_result = solver.solve()

        return self.power_flow_result

    # ---------------------------------------------------------
    # Backward-compatible alias
    # ---------------------------------------------------------

    def run_load_flow(
        self,
        options=None
    ):
        """
        Backward-compatible alias.

        GridForge now uses the terminology:

            POWER FLOW

        instead of:

            LOAD FLOW
        """

        return self.run_power_flow(
            options=options
        )

    # =========================================================
    # LINE FLOWS
    # =========================================================

    def compute_line_flows(self):
        """
        Calculate line power flows from the solved power-flow state.
        """

        if self.power_flow_result is None:
            raise RuntimeError(
                "Power flow must be solved before "
                "line flows can be calculated"
            )

        from core.analysis.line_flow import (
            LineFlowCalculator
        )

        calculator = LineFlowCalculator(
            self
        )

        self.line_flow_result = calculator.compute(
            self.power_flow_result["Vm"],
            self.power_flow_result["Va"]
        )

        return self.line_flow_result

    # =========================================================
    # TRANSFORMER FLOWS
    # =========================================================

    def compute_transformer_flows(self):
        """
        Calculate transformer power flows from the solved
        power-flow state.
        """

        if self.power_flow_result is None:
            raise RuntimeError(
                "Power flow must be solved before "
                "transformer flows can be calculated"
            )

        from core.analysis.transformer_flow import (
            TransformerFlowCalculator
        )

        calculator = TransformerFlowCalculator(
            self
        )

        self.transformer_flow_result = (
            calculator.compute(
                self.power_flow_result["Vm"],
                self.power_flow_result["Va"]
            )
        )

        return self.transformer_flow_result

    # =========================================================
    # SHORT CIRCUIT
    # =========================================================

    def apply_fault(
        self,
        bus_id,
        fault_type,
        Zf=0.0
    ):
        """
        Store the currently active fault condition.

        This does not perform fault calculations.
        """

        if bus_id not in self.bus_index:
            self.rebuild_bus_index()

        if bus_id not in self.bus_index:
            raise KeyError(
                f"Unknown fault bus: {bus_id}"
            )

        if Zf < 0:
            raise ValueError(
                "Fault impedance cannot be negative"
            )

        self.active_fault = {
            "bus_id": bus_id,
            "type": fault_type,
            "Zf": Zf
        }

    # ---------------------------------------------------------

    def run_short_circuit(
        self,
        fault_bus,
        Zf=0.0
    ):
        """
        Run a balanced three-phase short-circuit study.
        """

        from core.analysis.short_circuit import (
            ShortCircuitAnalyzer
        )

        if self.Ybus is None or self._ybus_dirty:
            self.build_ybus()

        analyzer = ShortCircuitAnalyzer(
            self
        )

        self.fault_result = (
            analyzer.run_three_phase_fault(
                fault_bus,
                Zf
            )
        )

        return self.fault_result

    # ---------------------------------------------------------

    def run_unbalanced_faults(
        self,
        fault_type,
        fault_bus,
        Zf=0.0
    ):
        """
        Run an unbalanced fault study using sequence networks.
        """

        from core.analysis.unbalanced_fault import (
            UnbalancedFaultAnalyzer
        )

        analyzer = UnbalancedFaultAnalyzer(
            self,
            self.sequence_network
            if hasattr(self, "sequence_network")
            else None
        )

        self.fault_result = analyzer.run(
            fault_type,
            fault_bus,
            Zf
        )

        return self.fault_result

    # =========================================================
    # PROTECTION
    # =========================================================

    def run_protection(self):
        """
        Execute the protection analysis interface.

        Protection logic remains outside Network.
        """

        if self.fault_result is None:
            raise RuntimeError(
                "Fault study must be completed before "
                "protection evaluation"
            )

        from core.protection.protection import (
            ProtectionSystem
        )

        protection_system = ProtectionSystem()

        return protection_system.evaluate(
            self.fault_result,
            self.lines,
            self.generators
        )

    # =========================================================
    # NETWORK RECONFIGURATION
    # =========================================================

    def reconfigure(self):
        """
        Rebuild topology and Y-bus after network changes.
        """

        self._topology_dirty = True
        self._ybus_dirty = True

        self.rebuild_topology()
        self.build_ybus()

        return self.Ybus

    # =========================================================
    # DYNAMIC SIMULATION
    # =========================================================

    def run_transient_stability(
        self,
        t_end=5.0,
        dt=0.01
    ):
        """
        Run transient-stability simulation.

        Dynamic numerical implementation belongs under:

            core/solver/dynamics/
        """

        from core.solver.dynamics.transient_stability import (
            TransientStabilitySolver
        )

        solver = TransientStabilitySolver(
            self
        )

        return solver.run(
            self.active_fault,
            t_end,
            dt
        )

    # ---------------------------------------------------------

    def run_multi_machine(
        self,
        t_end=5.0,
        dt=0.01
    ):
        """
        Run multi-machine dynamic simulation.
        """

        from core.solver.dynamics.multi_machine import (
            MultiMachineSimulator
        )

        simulator = MultiMachineSimulator(
            self
        )

        return simulator.run(
            t_end,
            dt
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self):
        """
        Validate the minimum requirements of the network.

        This method performs structural validation only.
        """

        if len(self.buses) == 0:
            raise ValueError(
                "Network contains no buses"
            )

        self.rebuild_bus_index()

        bus_ids = set(
            self.bus_index.keys()
        )

        # -----------------------------------------------------
        # Validate line terminals
        # -----------------------------------------------------

        for line in self.lines:

            from_bus = (
                line.from_bus.id
                if hasattr(line.from_bus, "id")
                else line.from_bus
            )

            to_bus = (
                line.to_bus.id
                if hasattr(line.to_bus, "id")
                else line.to_bus
            )

            if from_bus not in bus_ids:
                raise ValueError(
                    f"Line {getattr(line, 'id', line)} "
                    f"references unknown from-bus {from_bus}"
                )

            if to_bus not in bus_ids:
                raise ValueError(
                    f"Line {getattr(line, 'id', line)} "
                    f"references unknown to-bus {to_bus}"
                )

        # -----------------------------------------------------
        # Validate transformer terminals
        # -----------------------------------------------------

        for transformer in self.transformers:

            from_bus = (
                transformer.from_bus.id
                if hasattr(transformer.from_bus, "id")
                else transformer.from_bus
            )

            to_bus = (
                transformer.to_bus.id
                if hasattr(transformer.to_bus, "id")
                else transformer.to_bus
            )

            if from_bus not in bus_ids:
                raise ValueError(
                    f"Transformer "
                    f"{getattr(transformer, 'id', transformer)} "
                    f"references unknown from-bus {from_bus}"
                )

            if to_bus not in bus_ids:
                raise ValueError(
                    f"Transformer "
                    f"{getattr(transformer, 'id', transformer)} "
                    f"references unknown to-bus {to_bus}"
                )

        return True

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self):
        """
        Return a concise network summary.
        """

        return {
            "base_mva": self.base_mva,
            "buses": len(self.buses),
            "lines": len(self.lines),
            "transformers": len(self.transformers),
            "generators": len(self.generators),
            "loads": len(self.loads),
            "shunts": len(self.shunts),
            "ybus_built": self.Ybus is not None,
            "ybus_dirty": self._ybus_dirty,
            "topology_dirty": self._topology_dirty,
        }
