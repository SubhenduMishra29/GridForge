class Governor:


    def __init__(
        self,
        R=0.05,
        Tg=0.5,
        Pref=1.0
    ):

        self.R=R
        self.Tg=Tg
        self.Pref=Pref


    def derivative(
        self,
        Pm,
        omega
    ):

        return (
            self.Pref
            -
            Pm
            -
            omega/self.R
        ) / self.Tg
