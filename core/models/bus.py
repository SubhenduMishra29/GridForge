"""
GridForge Bus Model

Represents an electrical bus/node.

Bus types:
    SLACK:
        Voltage magnitude and angle fixed

    PV:
        Active power and voltage magnitude fixed

    PQ:
        Active and reactive power fixed


This class stores:
    - Electrical parameters
    - Operating state
    - Limits
    - Connectivity metadata

It does NOT perform:
    - Load flow calculation
    - Fault calculation
    - Dynamic simulation

Those belong to core/solver.
"""


class Bus:

    VALID_TYPES = {
        "SLACK",
        "PV",
        "PQ"
    }


    def __init__(
            self,
            bus_id: str,
            bus_type: str,
            name=None,

            base_kv=11.0,

            V=1.0,
            theta=0.0,

            P=0.0,
            Q=0.0,

            V_min=0.9,
            V_max=1.1
    ):


        if bus_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid bus type {bus_type}"
            )


        # -------------------------
        # Identity
        # -------------------------

        self.id = bus_id

        self.name = (
            name
            if name
            else bus_id
        )


        # -------------------------
        # Bus classification
        # -------------------------

        self.type = bus_type


        # -------------------------
        # Base quantities
        # -------------------------

        self.base_kv = base_kv



        # -------------------------
        # Specified values
        # -------------------------

        self.V_spec = V

        self.theta_spec = theta

        self.P_spec = P

        self.Q_spec = Q



        # -------------------------
        # Solved state
        # -------------------------

        self.V = V

        self.theta = theta

        self.P = P

        self.Q = Q



        # -------------------------
        # Voltage limits
        # -------------------------

        self.V_min = V_min

        self.V_max = V_max



        # -------------------------
        # Shunt admittance
        # -------------------------

        self.G_shunt = 0.0

        self.B_shunt = 0.0



        # -------------------------
        # Connected equipment
        # -------------------------

        self.generators = []

        self.loads = []

        self.lines = []

        self.transformers = []



    # =====================================================
    # STATE MANAGEMENT
    # =====================================================

    def reset(self):

        """
        Reset bus state to specified values.
        """

        self.V = self.V_spec

        self.theta = self.theta_spec

        self.P = self.P_spec

        self.Q = self.Q_spec



    def update_voltage(
            self,
            V,
            theta):

        self.V = V

        self.theta = theta



    def update_power(
            self,
            P,
            Q):

        self.P = P

        self.Q = Q



    # =====================================================
    # EQUIPMENT CONNECTION
    # =====================================================

    def add_generator(
            self,
            generator):

        self.generators.append(
            generator
        )


    def add_load(
            self,
            load):

        self.loads.append(
            load
        )


    # =====================================================
    # BUS TYPE HELPERS
    # =====================================================

    def is_slack(self):

        return self.type == "SLACK"



    def is_pv(self):

        return self.type == "PV"



    def is_pq(self):

        return self.type == "PQ"



    # =====================================================
    # VALIDATION
    # =====================================================

    def voltage_ok(self):

        return (
            self.V_min
            <= self.V
            <= self.V_max
        )



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (
            f"Bus("
            f"id={self.id}, "
            f"type={self.type}, "
            f"V={self.V:.4f}, "
            f"θ={self.theta:.4f}, "
            f"P={self.P:.4f}, "
            f"Q={self.Q:.4f})"
        )
