class DynamicState:

    def __init__(self, generators):

        self.delta = []
        self.omega = []

        for gen in generators:
            self.delta.append(gen.delta)
            self.omega.append(gen.omega)


    def pack(self):

        return self.delta + self.omega


    def unpack(self, x):

        n = len(x)//2

        self.delta = x[:n]
        self.omega = x[n:]
