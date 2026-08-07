"""
GridForge Protection Validation Runner

Executes closed-loop protection tests.

Flow:

Fault Scenario
        ↓
Short Circuit Analysis
        ↓
Relay Evaluation
        ↓
Breaker Operation
        ↓
Result Verification


Does NOT:
- Solve faults
- Operate relays directly
- Modify network models


"""



class ProtectionRunner:



    def __init__(
            self,
            network):


        self.network = network


        self.results = []



    # =====================================================
    # RUN SINGLE CASE
    # =====================================================

    def run_case(
            self,
            case):


        result = {

            "case":
                case.name,

            "fault":
                case.fault_type,

            "location":
                case.fault_location

        }



        # -------------------------------------------------
        # Apply fault
        # -------------------------------------------------

        self.network.apply_fault(

            case.fault_location,

            case.fault_type,

            case.fault_impedance

        )



        # -------------------------------------------------
        # Short circuit calculation
        # -------------------------------------------------

        fault_result = (

            self.network
            .run_short_circuit()

        )


        result["fault_result"] = fault_result



        # -------------------------------------------------
        # Protection operation
        # -------------------------------------------------

        trips = (

            self.network
            .run_protection()

        )


        result["trip_actions"] = trips



        # -------------------------------------------------
        # Network update
        # -------------------------------------------------

        self.network.reconfigure()



        result["status"] = (

            "COMPLETED"

        )


        self.results.append(result)


        return result



    # =====================================================
    # RUN MULTIPLE CASES
    # =====================================================

    def run_all(
            self,
            cases):


        output = []


        for case in cases:


            output.append(

                self.run_case(case)

            )


        return output



    # =====================================================
    # REPORT
    # =====================================================

    def report(self):


        return self.results
