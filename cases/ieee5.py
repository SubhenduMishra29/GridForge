# cases/ieee5.py

"""
IEEE 5-Bus Test Case (GridForge Format)

Base: 100 MVA
"""

from core.network.network import Network
from core.elements.bus import Bus
from core.elements.line import Line
from core.elements.generator import Generator
from core.per_unit import PerUnitSystem


def build_ieee5():
    base_mva = 100
    pu = PerUnitSystem(base_mva)

    net = Network(pu)

    # ------------------------------------------------------------------
    # BUSES
    # ------------------------------------------------------------------

    b1 = Bus(id=1, type="Slack", vm=1.06, va=0.0)
    b2 = Bus(id=2, type="PV", vm=1.04)
    b3 = Bus(id=3, type="PQ", p_spec=-0.9, q_spec=-0.3)
    b4 = Bus(id=4, type="PQ", p_spec=-1.0, q_spec=-0.35)
    b5 = Bus(id=5, type="PQ", p_spec=-0.6, q_spec=-0.2)

    for b in [b1, b2, b3, b4, b5]:
        net.add_bus(b)

    # ------------------------------------------------------------------
    # GENERATORS
    # ------------------------------------------------------------------

    g1 = Generator(
        bus=b1,
        p_mw=0,            # Slack will absorb mismatch
        v_set=1.06,
        q_min_mvar=-999,
        q_max_mvar=999,
        base_mva=base_mva
    )

    g2 = Generator(
        bus=b2,
        p_mw=40,
        v_set=1.04,
        q_min_mvar=-40,
        q_max_mvar=50,
        base_mva=base_mva
    )

    net.add_generator(g1)
    net.add_generator(g2)

    # ------------------------------------------------------------------
    # LINES (R, X in ohms — assumed base_kv = 230)
    # ------------------------------------------------------------------

    kv = 230

    lines = [
        (b1, b2, 0.02, 0.06),
        (b1, b3, 0.08, 0.24),
        (b2, b3, 0.06, 0.18),
        (b2, b4, 0.06, 0.18),
        (b2, b5, 0.04, 0.12),
        (b3, b4, 0.01, 0.03),
        (b4, b5, 0.08, 0.24),
    ]

    for fb, tb, r, x in lines:
        net.add_line(Line(
            from_bus=fb,
            to_bus=tb,
            r_ohm=r,
            x_ohm=x,
            b_siemens=0.0,
            base_kv=kv
        ))

    return net
