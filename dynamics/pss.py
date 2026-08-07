class PSS:


    def __init__(
        self,
        Kpss=10,
        Tw=10
    ):

        self.Kpss=Kpss
        self.Tw=Tw


    def output(
        self,
        omega
    ):

        return self.Kpss * omega
