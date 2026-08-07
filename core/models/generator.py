# ============================================
# File: gridforge/models/generator.py
# Description: Generator data container
# ============================================

class GeneratorData:
    def __init__(self, bus, Pm, H, E=1.1):
        self.bus = bus
        self.Pm = Pm
        self.H = H
        self.E = E
