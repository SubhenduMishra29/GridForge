import numpy as np


class ClassicalMachine:


    def __init__(self,
                 bus,
                 H,
                 D,
                 Pm,
                 E):

        self.bus = bus

        self.H = H
        self.D = D

        self.Pm = Pm
        self.E = E


    def derivatives(self,
                    delta,
                    omega,
                    Pe,
                    fbase=50):


        domega = (
            np.pi*fbase/self.H *
            (self.Pm-Pe-self.D*omega)
        )


        ddelta = (
            2*np.pi*fbase *
            omega
        )


        return ddelta, domega
