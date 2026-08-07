"""
GridForge Contingency Analyzer

Performs:

    N-1 security analysis


Workflow:

    1. Create outage
    2. Apply outage
    3. Rebuild network
    4. Solve load flow
    5. Check violations
    6. Restore system


"""


from core.solver.contingency.contingency_case import (
    ContingencyCase
)

from core.solver.contingency.violation_checker import (
    ViolationChecker
)



class ContingencyAnalyzer:


    def __init__(
            self,
            network,
            load_flow_solver):


        self.network = network

        self.load_flow_solver = load_flow_solver


        self.results = []



    # =====================================================
    # SINGLE CONTINGENCY
    # =====================================================

    def run_case(
            self,
            contingency):


        result = {

            "contingency":
                contingency.description,

            "success":
                False,

            "violations":
                []

        }



        try:


            # ---------------------------------
            # Apply outage
            # ---------------------------------

            contingency.apply(
                self.network
            )



            # ---------------------------------
            # Rebuild electrical model
            # ---------------------------------

            self.network.build_ybus()



            # ---------------------------------
            # Solve load flow
            # ---------------------------------

            solver = self.load_flow_solver(

                self.network

            )


            solver.solve()



            # ---------------------------------
            # Check violations
            # ---------------------------------

            checker = ViolationChecker(

                self.network

            )


            result["violations"] = (
                checker.check()
            )


            result["success"] = True



        finally:


            # ---------------------------------
            # Restore original network
            # ---------------------------------

            contingency.restore(

                self.network

            )


            self.network.build_ybus()



        return result



    # =====================================================
    # N-1 LINE ANALYSIS
    # =====================================================

    def run_n_minus_1(self):


        self.results = []



        # Lines

        for line in self.network.lines:


            case = ContingencyCase(

                "LINE",

                line.name

            )


            self.results.append(

                self.run_case(case)

            )



        # Transformers

        for trafo in self.network.transformers:


            case = ContingencyCase(

                "TRANSFORMER",

                trafo.name

            )


            self.results.append(

                self.run_case(case)

            )



        # Generators

        for gen in self.network.generators:


            case = ContingencyCase(

                "GENERATOR",

                getattr(
                    gen,
                    "id",
                    gen.bus
                )

            )


            self.results.append(

                self.run_case(case)

            )



        return self.results
