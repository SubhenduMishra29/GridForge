"""
GridForge Contingency Case

Defines a single outage event.

Examples:

    Line outage
    Transformer outage
    Generator outage


Used by:

    contingency_analyzer.py
    n_minus_one.py

"""


class ContingencyCase:


    VALID_TYPES = {

        "LINE",
        "TRANSFORMER",
        "GENERATOR",
        "BUS"

    }



    def __init__(
            self,
            element_type,
            element_id,
            description=None):


        element_type = element_type.upper()



        if element_type not in self.VALID_TYPES:

            raise ValueError(

                f"Invalid contingency type: "
                f"{element_type}"

            )



        self.element_type = element_type

        self.element_id = element_id


        self.description = (
            description
            or
            f"{element_type} outage {element_id}"
        )


        # State tracking

        self.applied = False



    # =====================================================
    # APPLY
    # =====================================================

    def apply(
            self,
            network):


        """
        Remove element from active network.

        Actual switching is handled by:

            topology.py
            breaker_manager

        """


        element = self._find_element(
            network
        )


        if element is None:

            raise ValueError(

                f"Element not found: "
                f"{self.element_id}"

            )


        element.in_service = False


        self.applied = True



    # =====================================================
    # RESTORE
    # =====================================================

    def restore(
            self,
            network):


        element = self._find_element(
            network
        )


        if element:

            element.in_service = True



        self.applied = False



    # =====================================================
    # FIND ELEMENT
    # =====================================================

    def _find_element(
            self,
            network):


        collection = None



        if self.element_type == "LINE":

            collection = network.lines



        elif self.element_type == "TRANSFORMER":

            collection = network.transformers



        elif self.element_type == "GENERATOR":

            collection = network.generators



        elif self.element_type == "BUS":

            collection = network.buses



        for element in collection:


            if getattr(
                element,
                "id",
                getattr(
                    element,
                    "name",
                    None
                )
            ) == self.element_id:


                return element



        return None



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (

            f"Contingency("
            f"{self.element_type}:"
            f"{self.element_id})"

        )
