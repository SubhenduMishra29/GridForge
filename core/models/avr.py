class AVR:

    def __init__(
        self,
        Ka=200,
        Ta=0.02,
        Vref=1.0
    ):

        self.Ka=Ka
        self.Ta=Ta
        self.Vref=Vref


    def derivative(
        self,
        Efd,
        Vt
    ):

        return (
            self.Ka*(self.Vref-Vt)
            -
            Efd
        ) / self.Ta
