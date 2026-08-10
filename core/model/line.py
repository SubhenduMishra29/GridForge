# ============================================================
# File: core/model/line.py
# GridForge Transmission Line Model (Topology + Electrical)
# ============================================================

import numpy as np


class Line:
    """
    π-equivalent transmission line model.

    Hybrid Design:
    --------------
    - Solver uses: bus IDs (strings)
    - UI uses: bus object references

    This avoids:
    ❌ Tight coupling with UI
    ❌ Expensive lookups during rendering
    """

    def __init__(
        self,
        from_bus: str,
        to_bus: str,
        r_pu: float,
        x_pu: float,
        b_pu: float = 0.0,
        name: str = None,
        rate_mva: float = 100.0,
    ):

        # -------------------------
        # Validation
        # -------------------------

        if from_bus == to_bus:
            raise ValueError("Line cannot connect a bus to itself")

        if r_pu == 0 and x_pu == 0:
            raise ValueError("Line impedance cannot be zero")

        # -------------------------
        # Connectivity (Solver Layer)
        # -------------------------

        self.from_bus = from_bus  # ID (string)
        self.to_bus = to_bus      # ID (string)

        # -------------------------
        # Connectivity (UI Layer)
        # -------------------------
        # These will be injected by Graph after creation

        self.from_bus_ref = None
        self.to_bus_ref = None

        # -------------------------
        # Electrical parameters
        # -------------------------

        self.r_pu = r_pu
        self.x_pu = x_pu
        self.b_pu = b_pu

        # -------------------------
        # Equipment data
        # -------------------------

        self.name = name if name else f"{from_bus}-{to_bus}"
        self.rate_mva = rate_mva

        # -------------------------
        # Operational state
        # -------------------------

        self.in_service = True

        # -------------------------
        # Flow results
        # -------------------------

        self.Pij = 0.0
        self.Qij = 0.0
        self.Pji = 0.0
        self.Qji = 0.0
        self.loss_p = 0.0
        self.loss_q = 0.0

    # =====================================================
    # TOPOLOGY (UI SUPPORT)
    # =====================================================

    def bind_buses(self, from_bus_obj, to_bus_obj):
        """
        Attach actual Bus objects (called by Graph).
        """
        self.from_bus_ref = from_bus_obj
        self.to_bus_ref = to_bus_obj

    def endpoints(self):
        """
        UI-safe geometry access.
        """
        if not self.from_bus_ref or not self.to_bus_ref:
            return (0, 0), (0, 0)

        return (
            (self.from_bus_ref.x, self.from_bus_ref.y),
            (self.to_bus_ref.x, self.to_bus_ref.y),
        )

    # =====================================================
    # ELECTRICAL PROPERTIES
    # =====================================================

    @property
    def z_pu(self):
        return complex(self.r_pu, self.x_pu)

    @property
    def y_pu(self):
        return 1 / self.z_pu

    # =====================================================
    # STATUS CONTROL
    # =====================================================

    def trip(self):
        self.in_service = False

    def close(self):
        self.in_service = True

    # =====================================================
    # POWER FLOW
    # =====================================================

    def calculate_flow(self, buses):

        bus_index = {
            bus.id: idx
            for idx, bus in enumerate(buses)
        }

        i = bus_index[self.from_bus]
        j = bus_index[self.to_bus]

        Vi = buses[i].V
        Vj = buses[j].V

        ti = buses[i].theta
        tj = buses[j].theta

        y = self.y_pu
        G = y.real
        B = y.imag

        angle = ti - tj

        Pij = (
            Vi**2 * G
            - Vi * Vj * (G * np.cos(angle) + B * np.sin(angle))
        )

        Qij = (
            -Vi**2 * B
            - Vi * Vj * (G * np.sin(angle) - B * np.cos(angle))
            + Vi**2 * self.b_pu / 2
        )

        Pji = (
            Vj**2 * G
            - Vi * Vj * (G * np.cos(-angle) + B * np.sin(-angle))
        )

        Qji = (
            -Vj**2 * B
            - Vi * Vj * (G * np.sin(-angle) - B * np.cos(-angle))
            + Vj**2 * self.b_pu / 2
        )

        self.Pij = Pij
        self.Qij = Qij
        self.Pji = Pji
        self.Qji = Qji

        self.loss_p = Pij + Pji
        self.loss_q = Qij + Qji

        return {
            "Pij": Pij,
            "Qij": Qij,
            "Pji": Pji,
            "Qji": Qji,
            "P_loss": self.loss_p,
            "Q_loss": self.loss_q,
        }

    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):
        return (
            f"Line({self.name}: "
            f"{self.from_bus} → {self.to_bus}, "
            f"Z={self.r_pu}+j{self.x_pu}, "
            f"status={self.in_service})"
        )
