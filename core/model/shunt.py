# core/models/shunt.py

class Shunt:
    """
    Shunt Element Model (Per-Unit)

    Represents:
    - Capacitors (+jB)
    - Reactors (-jB)
    - General shunt admittance (G + jB)
    """

    def __init__(
        self,
        bus: str,
        g_pu: float = 0.0,
        b_pu: float = 0.0,
        name: str = None,
    ):
        if g_pu == 0.0 and b_pu == 0.0:
            raise ValueError("Shunt must have non-zero admittance")

        self.bus = bus
        self.g_pu = g_pu
        self.b_pu = b_pu

        self.name = name or f"Shunt@{bus}"

    # ---------------------------------------------------------
    # DERIVED
    # ---------------------------------------------------------
    @property
    def y_pu(self):
        return complex(self.g_pu, self.b_pu)

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def __repr__(self):
        return (
            f"Shunt({self.name}: bus={self.bus}, "
            f"Y={self.g_pu}+j{self.b_pu})"
        )
