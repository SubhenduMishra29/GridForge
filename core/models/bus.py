# core/models/bus.py

class Bus:
    """
    Core Bus Model for GridForge

    Types:
    - SLACK: V, theta fixed
    - PV: P, V fixed
    - PQ: P, Q fixed
    """

    VALID_TYPES = {"SLACK", "PV", "PQ"}

    def __init__(
        self,
        bus_id: str,
        bus_type: str,
        V: float = 1.0,
        theta: float = 0.0,
        P: float = 0.0,
        Q: float = 0.0,
    ):
        if bus_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid bus type: {bus_type}")

        self.id = bus_id
        self.type = bus_type

        # Specified values
        self.P_spec = P
        self.Q_spec = Q
        self.V_spec = V
        self.theta_spec = theta

        # State variables (updated during simulation)
        self.V = V
        self.theta = theta
        self.P = P
        self.Q = Q

    # ---------------------------------------------------------
    # STATE MANAGEMENT
    # ---------------------------------------------------------
    def reset(self):
        """Reset to specified values"""
        self.V = self.V_spec
        self.theta = self.theta_spec
        self.P = self.P_spec
        self.Q = self.Q_spec

    def update_power(self, P_calc, Q_calc):
        """Update calculated power"""
        self.P = P_calc
        self.Q = Q_calc

    # ---------------------------------------------------------
    # TYPE HELPERS
    # ---------------------------------------------------------
    def is_slack(self):
        return self.type == "SLACK"

    def is_pv(self):
        return self.type == "PV"

    def is_pq(self):
        return self.type == "PQ"

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def __repr__(self):
        return (
            f"Bus(id={self.id}, type={self.type}, "
            f"V={self.V:.4f}, θ={self.theta:.4f}, "
            f"P={self.P:.4f}, Q={self.Q:.4f})"
        )
