"""
GridForge Relay Coordination Engine


Functions:

    - Primary/backup relay coordination
    - Coordination time interval checking
    - TMS adjustment framework


Used for:

    - Protection studies
    - Relay grading
    - Automatic optimisation (future)


"""


class RelayCoordination:



    def __init__(
            self,
            CTI=0.3):


        self.CTI = CTI


        self.relay_pairs = []



    # =====================================================
    # ADD RELAY PAIR
    # =====================================================

    def add_coordination_pair(
            self,
            primary,
            backup):


        self.relay_pairs.append({

            "primary":
                primary,

            "backup":
                backup

        })



    # =====================================================
    # CHECK COORDINATION
    # =====================================================

    def check_pair(
            self,
            primary,
            backup,
            fault_current):


        primary_time = (

            primary.operating_time()

        )


        backup_time = (

            backup.operating_time()

        )



        margin = (

            backup_time
            -
            primary_time

        )



        return {


            "primary":

                primary.id,


            "backup":

                backup.id,


            "primary_time":

                primary_time,


            "backup_time":

                backup_time,


            "margin":

                margin,


            "coordinated":

                margin >= self.CTI

        }



    # =====================================================
    # RUN STUDY
    # =====================================================

    def evaluate(
            self,
            fault_current):


        results = []



        for pair in self.relay_pairs:


            result = self.check_pair(

                pair["primary"],

                pair["backup"],

                fault_current

            )


            results.append(result)



        return results



    # =====================================================
    # TMS ADJUSTMENT FRAMEWORK
    # =====================================================

    def suggest_TMS_change(
            self,
            result):


        """
        Future optimisation hook.

        Used later with:

            MILP
            Genetic Algorithm
            Particle Swarm Optimisation


        """


        if result["coordinated"]:


            return {

                "action":
                    "NO_CHANGE"

            }



        else:


            return {

                "action":
                    "INCREASE_BACKUP_DELAY"

            }
