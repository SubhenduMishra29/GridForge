    # =================================================================
    # NETWORK ELEMENT REMOVAL
    # =================================================================

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Remove a registered Bus from the Network.

        Parameters
        ----------
        bus : Bus
            Canonical Bus object registered on this Network.

        Raises
        ------
        ValueError
            If the bus is None, is not registered, or is still
            referenced by another registered network element.

        Notes
        -----
        Bus removal is deliberately strict.

        A Bus cannot be removed while another canonical element
        references it because doing so would leave dangling
        topology/model references.

        The Network owns:

            * canonical collection membership;
            * registration indexes;
            * topology invalidation;
            * Y-bus invalidation.

        Therefore removal is implemented here rather than in:

            * Application;
            * TopologyManager;
            * UI;
            * plugins.

        Engineering/domain validation remains outside Network.
        """

        if bus is None:
            raise ValueError(
                "Bus cannot be None."
            )

        # -------------------------------------------------------------
        # REGISTRATION CHECK
        # -------------------------------------------------------------

        if bus not in self.buses:
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "is not registered on this Network."
            )

        # -------------------------------------------------------------
        # REFERENCE CHECK — LINES
        # -------------------------------------------------------------

        for line in self.lines:

            if (
                getattr(line, "from_bus", None) is bus
                or getattr(line, "to_bus", None) is bus
            ):
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Line '{line.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — TRANSFORMERS
        # -------------------------------------------------------------

        for transformer in self.transformers:

            if (
                getattr(transformer, "from_bus", None) is bus
                or getattr(transformer, "to_bus", None) is bus
            ):
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Transformer '{transformer.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — GENERATORS
        # -------------------------------------------------------------

        for generator in self.generators:

            if getattr(generator, "bus", None) is bus:
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Generator '{generator.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — LOADS
        # -------------------------------------------------------------

        for load in self.loads:

            if getattr(load, "bus", None) is bus:
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Load '{load.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — SHUNTS
        # -------------------------------------------------------------

        for shunt in self.shunts:

            if getattr(shunt, "bus", None) is bus:
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Shunt '{shunt.id}' references it."
                )

        # -------------------------------------------------------------
        # REMOVE FROM CANONICAL COLLECTION
        # -------------------------------------------------------------

        self.buses.remove(bus)

        # -------------------------------------------------------------
        # UPDATE BUS INDEX
        # -------------------------------------------------------------

        if getattr(self, "bus_index", None) is not None:

            bus_id = getattr(bus, "id", None)

            if bus_id in self.bus_index:
                del self.bus_index[bus_id]

        # -------------------------------------------------------------
        # INVALIDATE DERIVED NETWORK STATE
        # -------------------------------------------------------------

        self._invalidate_topology()
