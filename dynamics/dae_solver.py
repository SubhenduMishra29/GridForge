class DAESolver:


    def __init__(self,
                 network,
                 machines,
                 integrator):

        self.network=network
        self.machines=machines
        self.integrator=integrator



    def step(self,state,dt):


        # -------------------------
        # 1. Calculate generator currents
        # -------------------------

        currents={}


        for gen in self.machines:

            currents[gen.bus]=(
                gen.E *
                complex(
                    1,
                    0
                )
            )



        # -------------------------
        # 2. Solve network algebra
        # -------------------------

        V=self.network_solver.solve(
            currents
        )



        # -------------------------
        # 3. Calculate Pe
        # -------------------------

        Pe=[]


        for gen in self.machines:

            S=V[gen.bus]*currents[gen.bus].conjugate()

            Pe.append(
                S.real
            )


        # -------------------------
        # 4. Differential update
        # -------------------------

        dx=[]


        for idx,gen in enumerate(self.machines):

            ddelta,domega=gen.derivatives(
                state.delta[idx],
                state.omega[idx],
                Pe[idx]
            )


            dx.append(ddelta)
            dx.append(domega)



        # Integrate

        return self.integrator.integrate(
            state,
            dx,
            dt
        )
