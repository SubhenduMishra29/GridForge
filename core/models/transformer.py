# core/models/transformer.py

class Transformer:
    """
    Transformer Model (Per-Unit)

    Assumptions:
    - Series impedance in pu
    - Off-nominal tap ratio (real, no phase shift yet)
    - Tap located at FROM side
    """

    def __init__(
        self,
        from_bus: str,
        to_bus: str,
        r_pu: float,
        x_pu: float,
        tap_ratio: float = 1.0,
        name: str = None,
    ):
        if from_bus == to_bus:
            raise ValueError("Transformer cannot connect a bus to itself")

        if r_pu == 0 and x_pu == 0:
            raise ValueError("Transformer impedance cannot be zero")

        if tap_ratio <= 0:
            raise ValueError("Tap ratio must be positive")

        self.from_bus = from_bus
        self.to_bus = to_bus

        self.r_pu = r_pu
        self.x_pu = x_pu
        self.tap_ratio = tap_ratio

        self.name = name or f"{from_bus}-{to_bus}"

    # ---------------------------------------------------------
    # DERIVED
    # ---------------------------------------------------------
    @property
    def z_pu(self):
        return complex(self.r_pu, self.x_pu)

    @property
    def y_pu(self):
        return 1 / self.z_pu

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def __repr__(self):
        return (
            f"Transformer({self.name}: {self.from_bus} → {self.to_bus}, "
            f"Z={self.r_pu}+j{self.x_pu}, tap={self.tap_ratio})"
        )
