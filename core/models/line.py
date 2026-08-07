# core/models/line.py

import numpy as np


class Line:
    """
    Transmission Line Model (π-model)

    Parameters (per-unit):
    - r_pu: resistance
    - x_pu: reactance
    - b_pu: total line charging susceptance
    """

    def __init__(
        self,
        from_bus: str,
        to_bus: str,
        r_pu: float,
        x_pu: float,
        b_pu: float = 0.0,
        name: str = None,
    ):
        if from_bus == to_bus:
            raise ValueError("Line cannot connect a bus to itself")

        if r_pu == 0 and x_pu == 0:
            raise ValueError("Line impedance cannot be zero")

        self.from_bus = from_bus
        self.to_bus = to_bus

        self.r_pu = r_pu
        self.x_pu = x_pu
        self.b_pu = b_pu

        self.name = name or f"{from_bus}-{to_bus}"

    # ---------------------------------------------------------
    # DERIVED PROPERTIES
    # ---------------------------------------------------------
    @property
    def z_pu(self):
        return complex(self.r_pu, self.x_pu)

    @property
    def y_pu(self):
        return 1 / self.z_pu

    # ---------------------------------------------------------
    # POWER FLOW CALCULATION (π-model)
    # ---------------------------------------------------------
    def calculate_flow(self, buses, Ybus):
        """
        Computes:
        - Forward flow (Pij, Qij)
        - Reverse flow (Pji, Qji)
        - Line losses (P_loss, Q_loss)
        """

        # Map bus IDs → indices
        bus_index = {bus.id: i for i, bus in enumerate(buses)}

        i = bus_index[self.from_bus]
        j = bus_index[self.to_bus]

        # Voltages
        Vi = buses[i].V
        Vj = buses[j].V
        thetai = buses[i].theta
        thetaj = buses[j].theta

        # Series admittance
        y = self.y_pu
        G = y.real
        B = y.imag

        angle = thetai - thetaj

        # -----------------------------------------------------
        # Forward flow (i → j)
        # -----------------------------------------------------
        Pij = Vi**2 * G - Vi * Vj * (G * np.cos(angle) + B * np.sin(angle))

        Qij = (
            -Vi**2 * B
            - Vi * Vj * (G * np.sin(angle) - B * np.cos(angle))
            + (Vi**2 * self.b_pu / 2)  # π-model shunt
        )

        # -----------------------------------------------------
        # Reverse flow (j → i)
        # -----------------------------------------------------
        Pji = Vj**2 * G - Vi * Vj * (G * np.cos(-angle) + B * np.sin(-angle))

        Qji = (
            -Vj**2 * B
            - Vi * Vj * (G * np.sin(-angle) - B * np.cos(-angle))
            + (Vj**2 * self.b_pu / 2)
        )

        # -----------------------------------------------------
        # LOSSES
        # -----------------------------------------------------
        P_loss = Pij + Pji
        Q_loss = Qij + Qji

        return {
            "Pij": Pij,
            "Qij": Qij,
            "Pji": Pji,
            "Qji": Qji,
            "P_loss": P_loss,
            "Q_loss": Q_loss,
        }

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def __repr__(self):
        return (
            f"Line({self.name}: {self.from_bus} → {self.to_bus}, "
            f"Z={self.r_pu}+j{self.x_pu}, B={self.b_pu})"
        )
