# core/elements/generator.py

"""
GridForge Generator Model (Steady-State)

Supports:
- PV bus operation
- Reactive power limits
- Automatic PV → PQ switching
"""

class Generator:
    def __init__(
        self,
        bus,
        p_mw,
        v_set,
        q_min_mvar,
        q_max_mvar,
        base_mva
    ):
        self.bus = bus

        # Convert to per-unit
        self.p = p_mw / base_mva
        self.v_set = v_set

        self.q_min = q_min_mvar / base_mva
        self.q_max = q_max_mvar / base_mva

        # Runtime state
        self.q = 0.0
        self.is_active = True

    def enforce_voltage(self):
        """
        Enforce voltage magnitude at PV bus
        """
        if self.bus.is_pv:
            self.bus.vm = self.v_set

    def check_q_limits(self):
        """
        Enforce reactive power limits.
        Switch PV → PQ if violated.
        """
        if not self.bus.is_pv:
            return

        if self.q < self.q_min:
            self.q = self.q_min
            self._convert_to_pq()

        elif self.q > self.q_max:
            self.q = self.q_max
            self._convert_to_pq()

    def _convert_to_pq(self):
        """
        Switch bus type when Q limits are hit
        """
        self.bus.type = "PQ"
        self.bus.q_spec = self.q
