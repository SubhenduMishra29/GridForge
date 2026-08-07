"""
GridForge N-1 Security Analysis Interface


Example:

    analysis = NMinusOne(network)

    report = analysis.run()


"""


from core.solver.contingency.contingency_analyzer import (
    ContingencyAnalyzer
)



class NMinusOne:


    def __init__(
            self,
            network,
            load_flow_solver):


        self.network = network

        self.load_flow_solver = load_flow_solver


        self.analyzer = ContingencyAnalyzer(

            network,

            load_flow_solver

        )


        self.report = None



    # =====================================================
    # RUN ANALYSIS
    # =====================================================

    def run(self):


        self.report = (

            self.analyzer
            .run_n_minus_1()

        )


        return self.report



    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self):


        if self.report is None:

            return {

                "status":
                    "NOT_RUN"

            }



        total = len(
            self.report
        )


        failed = sum(

            1

            for item in self.report

            if len(
                item["violations"]
            ) > 0

        )


        return {


            "total_cases":

                total,


            "violated_cases":

                failed,


            "secure":

                failed == 0

        }



    # =====================================================
    # CRITICAL EVENTS
    # =====================================================

    def critical_cases(self):


        if self.report is None:

            return []



        return [

            case

            for case in self.report

            if case["violations"]

        ]
