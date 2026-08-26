# ============================================================
# BRANCH
# ============================================================

CREATE_BRANCH = "model.create_branch"
UPDATE_BRANCH = "model.update_branch"
DELETE_BRANCH = "model.delete_branch"


class CreateBranchCommand(Command):
    """Request creation of a generic Core Branch."""

    def __init__(
        self,
        *,
        branch_id: str,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        name: str = "",
        rate_mva: float | None = None,
        tap: float = 1.0,
        shift: float = 0.0,
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_BRANCH,
            payload={
                "branch_id": branch_id,
                "r": r,
                "x": x,
                "b": b,
                "name": name,
                "rate_mva": rate_mva,
                "tap": tap,
                "shift": shift,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateBranchCommand(Command):
    """Request mutation of an existing Core Branch."""

    def __init__(
        self,
        *,
        branch_id: str,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        name: str | None = None,
        rate_mva: float | None = None,
        tap: float | None = None,
        shift: float | None = None,
        in_service: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                r,
                x,
                b,
                name,
                rate_mva,
                tap,
                shift,
                in_service,
            )
        ):
            raise ValueError(
                "UpdateBranchCommand requires at least one "
                "mutable Branch field."
            )

        super().__init__(
            command_type=UPDATE_BRANCH,
            payload={
                "branch_id": branch_id,
                "r": r,
                "x": x,
                "b": b,
                "name": name,
                "rate_mva": rate_mva,
                "tap": tap,
                "shift": shift,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteBranchCommand(Command):
    """Request deletion of a Core Branch."""

    def __init__(
        self,
        *,
        branch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_BRANCH,
            payload={"branch_id": branch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# CABLE
# ============================================================

CREATE_CABLE = "model.create_cable"
UPDATE_CABLE = "model.update_cable"
DELETE_CABLE = "model.delete_cable"


class CreateCableCommand(Command):
    """Request creation of a physical Core Cable."""

    def __init__(
        self,
        *,
        cable_id: str,
        name: str = "",
        length_km: float = 0.0,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float = 0.0,
        x1_ohm_per_km: float = 0.0,
        b1_us_per_km: float = 0.0,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_CABLE,
            payload={
                "cable_id": cable_id,
                "name": name,
                "length_km": length_km,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
                "r1_ohm_per_km": r1_ohm_per_km,
                "x1_ohm_per_km": x1_ohm_per_km,
                "b1_us_per_km": b1_us_per_km,
                "r0_ohm_per_km": r0_ohm_per_km,
                "x0_ohm_per_km": x0_ohm_per_km,
                "b0_us_per_km": b0_us_per_km,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateCableCommand(Command):
    """Request mutation of an existing Core Cable."""

    def __init__(
        self,
        *,
        cable_id: str,
        name: str | None = None,
        length_km: float | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float | None = None,
        x1_ohm_per_km: float | None = None,
        b1_us_per_km: float | None = None,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                name,
                length_km,
                rated_voltage_kv,
                rated_current_a,
                r1_ohm_per_km,
                x1_ohm_per_km,
                b1_us_per_km,
                r0_ohm_per_km,
                x0_ohm_per_km,
                b0_us_per_km,
                in_service,
            )
        ):
            raise ValueError(
                "UpdateCableCommand requires at least one "
                "mutable Cable field."
            )

        super().__init__(
            command_type=UPDATE_CABLE,
            payload={
                "cable_id": cable_id,
                "name": name,
                "length_km": length_km,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
                "r1_ohm_per_km": r1_ohm_per_km,
                "x1_ohm_per_km": x1_ohm_per_km,
                "b1_us_per_km": b1_us_per_km,
                "r0_ohm_per_km": r0_ohm_per_km,
                "x0_ohm_per_km": x0_ohm_per_km,
                "b0_us_per_km": b0_us_per_km,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteCableCommand(Command):
    """Request deletion of a Core Cable."""

    def __init__(
        self,
        *,
        cable_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_CABLE,
            payload={"cable_id": cable_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# SWITCH
# ============================================================

CREATE_SWITCH = "model.create_switch"
UPDATE_SWITCH = "model.update_switch"
DELETE_SWITCH = "model.delete_switch"
OPEN_SWITCH = "model.open_switch"
CLOSE_SWITCH = "model.close_switch"
PUT_SWITCH_IN_SERVICE = "model.put_switch_in_service"
TAKE_SWITCH_OUT_OF_SERVICE = "model.take_switch_out_of_service"


class CreateSwitchCommand(Command):
    """Request creation of a Core Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        name: str = "",
        closed: bool = False,
        in_service: bool = True,
        normally_closed: bool | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_SWITCH,
            payload={
                "switch_id": switch_id,
                "name": name,
                "closed": closed,
                "in_service": in_service,
                "normally_closed": normally_closed,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateSwitchCommand(Command):
    """Request mutation of local Switch configuration/state."""

    def __init__(
        self,
        *,
        switch_id: str,
        name: str | None = None,
        closed: bool | None = None,
        in_service: bool | None = None,
        normally_closed: bool | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                name,
                closed,
                in_service,
                normally_closed,
                rated_voltage_kv,
                rated_current_a,
            )
        ):
            raise ValueError(
                "UpdateSwitchCommand requires at least one "
                "mutable Switch field."
            )

        super().__init__(
            command_type=UPDATE_SWITCH,
            payload={
                "switch_id": switch_id,
                "name": name,
                "closed": closed,
                "in_service": in_service,
                "normally_closed": normally_closed,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteSwitchCommand(Command):
    """Request deletion of a Core Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_SWITCH,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class OpenSwitchCommand(Command):
    """Request opening a Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=OPEN_SWITCH,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class CloseSwitchCommand(Command):
    """Request closing a Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CLOSE_SWITCH,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class PutSwitchInServiceCommand(Command):
    """Request placing a Switch in service."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=PUT_SWITCH_IN_SERVICE,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class TakeSwitchOutOfServiceCommand(Command):
    """Request taking a Switch out of service."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=TAKE_SWITCH_OUT_OF_SERVICE,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# DISCONNECTOR
# ============================================================

CREATE_DISCONNECTOR = "model.create_disconnector"
UPDATE_DISCONNECTOR = "model.update_disconnector"
DELETE_DISCONNECTOR = "model.delete_disconnector"
OPEN_DISCONNECTOR = "model.open_disconnector"
CLOSE_DISCONNECTOR = "model.close_disconnector"
PUT_DISCONNECTOR_IN_SERVICE = "model.put_disconnector_in_service"
TAKE_DISCONNECTOR_OUT_OF_SERVICE = (
    "model.take_disconnector_out_of_service"
)


class CreateDisconnectorCommand(Command):
    """Request creation of a Core Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        voltage_kv: float,
        rated_current_a: float,
        operating_time: float = 1.0,
        closed: bool = True,
        in_service: bool = True,
        name: str = "",
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_DISCONNECTOR,
            payload={
                "disconnector_id": disconnector_id,
                "voltage_kv": voltage_kv,
                "rated_current_a": rated_current_a,
                "operating_time": operating_time,
                "closed": closed,
                "in_service": in_service,
                "name": name,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateDisconnectorCommand(Command):
    """Request mutation of local Disconnector state/configuration."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        operating_time: float | None = None,
        closed: bool | None = None,
        in_service: bool | None = None,
        name: str | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                voltage_kv,
                rated_current_a,
                operating_time,
                closed,
                in_service,
                name,
            )
        ):
            raise ValueError(
                "UpdateDisconnectorCommand requires at least one "
                "mutable Disconnector field."
            )

        super().__init__(
            command_type=UPDATE_DISCONNECTOR,
            payload={
                "disconnector_id": disconnector_id,
                "voltage_kv": voltage_kv,
                "rated_current_a": rated_current_a,
                "operating_time": operating_time,
                "closed": closed,
                "in_service": in_service,
                "name": name,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteDisconnectorCommand(Command):
    """Request deletion of a Core Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_DISCONNECTOR,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class OpenDisconnectorCommand(Command):
    """Request opening a Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=OPEN_DISCONNECTOR,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class CloseDisconnectorCommand(Command):
    """Request closing a Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CLOSE_DISCONNECTOR,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class PutDisconnectorInServiceCommand(Command):
    """Request placing a Disconnector in service."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=PUT_DISCONNECTOR_IN_SERVICE,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class TakeDisconnectorOutOfServiceCommand(Command):
    """Request taking a Disconnector out of service."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=TAKE_DISCONNECTOR_OUT_OF_SERVICE,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# FUSE
# ============================================================

CREATE_FUSE = "model.create_fuse"
UPDATE_FUSE = "model.update_fuse"
DELETE_FUSE = "model.delete_fuse"
BLOW_FUSE = "model.blow_fuse"
RESET_FUSE = "model.reset_fuse"
PUT_FUSE_IN_SERVICE = "model.put_fuse_in_service"
TAKE_FUSE_OUT_OF_SERVICE = "model.take_fuse_out_of_service"


class CreateFuseCommand(Command):
    """Request creation of a Core Fuse."""

    def __init__(
        self,
        *,
        fuse_id: str,
        name: str = "",
        rated_current_a: float = 1.0,
        rated_voltage_v: float = 1.0,
        interrupting_rating_ka: float = 0.0,
        in_service: bool = True,
        blown: bool = False,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_FUSE,
            payload={
                "fuse_id": fuse_id,
                "name": name,
                "rated_current_a": rated_current_a,
                "rated_voltage_v": rated_voltage_v,
                "interrupting_rating_ka": interrupting_rating_ka,
                "in_service": in_service,
                "blown": blown,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateFuseCommand(Command):
    """Request mutation of local Fuse state/configuration."""

    def __init__(
        self,
        *,
        fuse_id: str,
        name: str | None = None,
        rated_current_a: float | None = None,
        rated_voltage_v: float | None = None,
        interrupting_rating_ka: float | None = None,
        in_service: bool | None = None,
        blown: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                name,
                rated_current_a,
                rated_voltage_v,
                interrupting_rating_ka,
                in_service,
                blown,
            )
        ):
            raise ValueError(
                "UpdateFuseCommand requires at least one "
                "mutable Fuse field."
            )

        super().__init__(
            command_type=UPDATE_FUSE,
            payload={
                "fuse_id": fuse_id,
                "name": name,
                "rated_current_a": rated_current_a,
                "rated_voltage_v": rated_voltage_v,
                "interrupting_rating_ka": interrupting_rating_ka,
                "in_service": in_service,
                "blown": blown,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteFuseCommand(Command):
    """Request deletion of a Core Fuse."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_FUSE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class BlowFuseCommand(Command):
    """Request operation of a Fuse element."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=BLOW_FUSE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class ResetFuseCommand(Command):
    """Request reset of a Fuse element."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=RESET_FUSE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class PutFuseInServiceCommand(Command):
    """Request placing a Fuse in service."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=PUT_FUSE_IN_SERVICE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class TakeFuseOutOfServiceCommand(Command):
    """Request taking a Fuse out of service."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=TAKE_FUSE_OUT_OF_SERVICE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
