# ui/controllers/network_controller.py

from core.network.network import Network
from core.models.bus import Bus
from core.models.line import Line


class NetworkController:
    """
    Handles interaction between UI and GridForge Core
    """

    def __init__(self):
        self.network = Network()
        self.ui_bus_map = {}  # UI ID -> Core Bus ID

    # ---------------------------------------------------------
    # BUS HANDLING
    # ---------------------------------------------------------
    def create_bus(self, ui_id, bus_type="PQ"):
        bus_id = f"BUS_{len(self.network.buses) + 1}"

        bus = Bus(bus_id, bus_type)
        self.network.add_bus(bus)

        self.ui_bus_map[ui_id] = bus_id

        return bus_id

    # ---------------------------------------------------------
    # LINE HANDLING
    # ---------------------------------------------------------
    def create_line(self, ui_from_id, ui_to_id, r=0.01, x=0.05, b=0.02):
        from_bus = self.ui_bus_map[ui_from_id]
        to_bus = self.ui_bus_map[ui_to_id]

        line = Line(from_bus, to_bus, r, x, b)
        self.network.add_line(line)

    # ---------------------------------------------------------
    # SIMULATION
    # ---------------------------------------------------------
    def run_simulation(self):
        return self.network.run_load_flow()

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def summary(self):
        return self.network.summary()
