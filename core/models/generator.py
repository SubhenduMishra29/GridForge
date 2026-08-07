"""
GridForge Generator Model

Represents synchronous generator equipment.

Contains:
    - Electrical parameters
    - Mechanical parameters
    - Dynamic states
    - Control model references

Does NOT solve:
    - Load flow
    - Short circuit
    - Differential equations

Those belong to:
    core/solver
"""


class Generator:


    def __init__(
            self,

            bus: str,

            name: str = None,

            rated_mva: float = 100.0,

            Pm: float = 1.0,

            H: float = 3.5,


            # Electrical parameters

            Xd: float = 1.8,

            Xd_prime: float = 0.3,

            Xq: float = 1.7,


            # Internal voltage

            E: float = 1.1
    ):


        # -------------------------
        # Identification
        # -------------------------

        self.bus = bus

        self.name = (
            name
            if name
            else f"GEN_{bus}"
        )


        self.rated_mva = rated_mva



        # -------------------------
        # Mechanical data
        # -------------------------

        self.Pm = Pm

        self.H = H



        # -------------------------
        # Electrical data
        # -------------------------

        self.Xd = Xd

        self.Xd_prime = Xd_prime

        self.Xq = Xq



        self.E = E



        # -------------------------
        # Dynamic states
        # -------------------------

        # Rotor angle

        self.delta = 0.0


        # Speed deviation

        self.omega = 0.0



        # Field voltage

        self.Efd = E



        # Electrical output

        self.Pe = 0.0



        # -------------------------
        # Control models
        # -------------------------

        self.avr = None

        self.governor = None

        self.pss = None



        # -------------------------
        # Operating state
        # -------------------------

        self.in_service = True



    # =====================================================
    # CONTROL CONNECTION
    # =====================================================

    def attach_avr(
            self,
            avr):

        self.avr = avr



    def attach_governor(
            self,
            governor):

        self.governor = governor



    def attach_pss(
            self,
            pss):

        self.pss = pss



    # =====================================================
    # STATE RESET
    # =====================================================

    def reset_state(self):

        self.delta = 0.0

        self.omega = 0.0

        self.Efd = self.E

        self.Pe = 0.0



    # =====================================================
    # STATUS
    # =====================================================

    def trip(self):

        self.in_service = False



    def close(self):

        self.in_service = True



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (
            f"Generator("
            f"{self.name}, "
            f"Bus={self.bus}, "
            f"Pm={self.Pm}, "
            f"H={self.H}, "
            f"Xd={self.Xd}, "
            f"Efd={self.Efd})"
        )
