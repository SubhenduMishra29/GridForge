class RK4Integrator:
    def step(self, system, V, dt):
        """
        Generic RK4 wrapper for multi-machine system
        """
        # For now, fallback to simple stepping (extend later)
        return system.step(V, dt)
