# core/models/line.py

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
        z = self.z_pu
        return 1 / z

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def __repr__(self):
        return (
            f"Line({self.name}: {self.from_bus} → {self.to_bus}, "
            f"Z={self.r_pu}+j{self.x_pu}, B={self.b_pu})"
        )
