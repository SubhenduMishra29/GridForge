"""
GridForge Contingency Violation Checker

Checks post-contingency operating conditions.

Evaluates:

    - Voltage violations
    - Line overloads
    - Transformer overloads
    - Generator limits


Used by:

    contingency_analyzer.py

"""


class ViolationChecker:


    def __init__(
            self,
            network):


        self.network = network


        # Default industrial limits

        self.V_MIN = 0.90

        self.V_MAX = 1.10


        self.LOADING_LIMIT = 1.0



    # =====================================================
    # CHECK ALL
    # =====================================================

    def check(self):


        violations = []


        violations.extend(

            self.check_voltage()

        )


        violations.extend(

            self.check_lines()

        )


        violations.extend(

            self.check_transformers()

        )


        violations.extend(

            self.check_generators()

        )


        return violations



    # =====================================================
    # BUS VOLTAGE
    # =====================================================

    def check_voltage(self):


        violations = []


        for bus in self.network.buses:


            V = abs(bus.V)



            if V < self.V_MIN:


                violations.append({

                    "type":
                        "LOW_VOLTAGE",


                    "element":
                        bus.id,


                    "value":
                        V,


                    "limit":
                        self.V_MIN

                })



            elif V > self.V_MAX:


                violations.append({

                    "type":
                        "HIGH_VOLTAGE",


                    "element":
                        bus.id,


                    "value":
                        V,


                    "limit":
                        self.V_MAX

                })



        return violations



    # =====================================================
    # LINE LOADING
    # =====================================================

    def check_lines(self):


        violations = []


        for line in self.network.lines:


            loading = getattr(

                line,

                "loading",

                0.0

            )


            if loading > self.LOADING_LIMIT:


                violations.append({

                    "type":
                        "LINE_OVERLOAD",


                    "element":
                        line.name,


                    "loading":
                        loading

                })



        return violations



    # =====================================================
    # TRANSFORMER LOADING
    # =====================================================

    def check_transformers(self):


        violations = []


        for trafo in self.network.transformers:


            loading = getattr(

                trafo,

                "loading",

                0.0

            )



            if loading > self.LOADING_LIMIT:


                violations.append({

                    "type":
                        "TRANSFORMER_OVERLOAD",


                    "element":
                        trafo.name,


                    "loading":
                        loading

                })



        return violations



    # =====================================================
    # GENERATOR LIMITS
    # =====================================================

    def check_generators(self):


        violations = []


        for gen in self.network.generators:


            P = getattr(

                gen,

                "P",

                None

            )


            Pmax = getattr(

                gen,

                "Pmax",

                None

            )



            if (

                P is not None

                and

                Pmax is not None

                and

                P > Pmax

            ):


                violations.append({

                    "type":
                        "GENERATOR_LIMIT",


                    "element":
                        gen.bus,


                    "value":
                        P,


                    "limit":
                        Pmax

                })



        return violations
