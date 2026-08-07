from dynamics.avr import AVR
from dynamics.governor import Governor
from dynamics.pss import PSS



class DynamicGenerator:


    def __init__(
        self,
        bus,
        H,
        Efd=1.0
    ):

        self.bus=bus

        self.H=H

        self.delta=0
        self.omega=0

        self.Efd=Efd
        self.Pm=1.0


        self.avr=AVR()
        self.gov=Governor()
        self.pss=PSS()



    def derivatives(
        self,
        Vt,
        Pe
    ):


        # Rotor equations

        ddelta = self.omega


        domega = (
            self.Pm-Pe
        )/(2*self.H)



        # AVR

        dEfd = self.avr.derivative(
            self.Efd,
            abs(Vt)
        )


        # Governor

        dPm = self.gov.derivative(
            self.Pm,
            self.omega
        )


        return {
            "delta":ddelta,
            "omega":domega,
            "Efd":dEfd,
            "Pm":dPm
        }
