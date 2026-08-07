class DynamicState:

    def __init__(self, generators):

        self.delta = []
        self.omega = []

        self.Efd = []
        self.Pm = []

        self.pss_state = []


        for gen in generators:

            self.delta.append(gen.delta)
            self.omega.append(gen.omega)

            self.Efd.append(gen.Efd)
            self.Pm.append(gen.Pm)

            self.pss_state.append(0.0)


    def pack(self):

        return (
            self.delta
            +
            self.omega
            +
            self.Efd
            +
            self.Pm
            +
            self.pss_state
        )
