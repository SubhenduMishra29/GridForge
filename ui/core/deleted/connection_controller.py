# ============================================================
# File: ui/core/connection_controller.py
# GridForge V2 — Connection Controller
# ============================================================
"""
Connection Controller for GridForge V2.

Architectural role
------------------
ConnectionController is the UI/domain command boundary for
electrical connection requests.

Navigation / Canvas
        │
        ▼
InteractionManager
        │
        ▼
ConnectTool
        │
        ▼
SnapSystem
        │
        ▼
ConnectionController
        │
        ▼
GridForge Core Network / Topology

Responsibilities
----------------
ConnectionController owns:

    - connection request orchestration;
    - source terminal identification;
    - target terminal identification;
    - connection request lifecycle;
    - Core invocation;
    - validation responses;
    - success/failure result normalization;
    - disconnect requests;
    - connection modification requests;
    - command-level coordination.

ConnectionController does NOT own:

    - electrical topology;
    - terminal ownership;
    - equipment state;
    - electrical rules;
    - solver calculations;
    - connection persistence;
    - rendering;
    - graphical routing;
    - preview geometry;
    - snapping;
    - independent connection state.

Core is authoritative for:

    - topology;
    - connection validity;
    - connection creation;
    - connection removal;
    - authoritative connection identity.

Frozen request contract
-----------------------
ConnectionRequest contains:

    source_terminal_id
    target_terminal_id
    connection_type
    presentation_hint

Primary operation
-----------------
The primary connection operation is:

    terminal → terminal

Graphical route and preview data remain presentation concerns.

Qt architecture
----------------
No Qt dependency is required by this controller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


# ============================================================
# CONNECTION REQUEST
# ============================================================


@dataclass(frozen=True)
class ConnectionRequest:
    """
    Immutable request to connect two electrical terminals.

    The request contains identifiers and request metadata only.
    It does not contain graphical items or domain objects.
    """

    source_terminal_id: Any
    target_terminal_id: Any

    connection_type: Any = None

    presentation_hint: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.source_terminal_id is None:
            raise ValueError(
                "source_terminal_id must not be None."
            )

        if self.target_terminal_id is None:
            raise ValueError(
                "target_terminal_id must not be None."
            )

        if self.presentation_hint is not None:
            if not isinstance(
                self.presentation_hint,
                Mapping,
            ):
                raise TypeError(
                    "presentation_hint must be a mapping or None."
                )


# ============================================================
# CONNECTION RESULT
# ============================================================


@dataclass(frozen=True)
class ConnectionResult:
    """
    Normalized result returned by ConnectionController.

    The controller deliberately exposes a stable result contract
    instead of leaking Core-specific result objects into the UI.
    """

    success: bool

    operation: str

    connection_id: Any = None

    error: Any = None

    validation: Any = None

    data: Mapping[str, Any] = field(
        default_factory=dict
    )

    @classmethod
    def succeeded(
        cls,
        operation: str,
        *,
        connection_id: Any = None,
        validation: Any = None,
        data: Mapping[str, Any] | None = None,
    ) -> "ConnectionResult":
        return cls(
            success=True,
            operation=operation,
            connection_id=connection_id,
            validation=validation,
            data=(
                {}
                if data is None
                else dict(data)
            ),
        )

    @classmethod
    def failed(
        cls,
        operation: str,
        error: Any,
        *,
        validation: Any = None,
        data: Mapping[str, Any] | None = None,
    ) -> "ConnectionResult":
        return cls(
            success=False,
            operation=operation,
            error=error,
            validation=validation,
            data=(
                {}
                if data is None
                else dict(data)
            ),
        )


# ============================================================
# CONNECTION CONTROLLER
# ============================================================


class ConnectionController:
    """
    UI/domain boundary for electrical connection commands.

    The controller contains orchestration logic only.

    It delegates authoritative electrical decisions to the
    supplied Core interface.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        core: Any,
    ) -> None:
        """
        Initialize the connection controller.

        Parameters
        ----------
        core:
            Core/network command boundary.

        The controller intentionally accepts the dependency
        through an abstraction boundary rather than importing
        a concrete Core implementation.
        """

        if core is None:
            raise ValueError(
                "core must not be None."
            )

        self._core = core

        self._disposed = False

        self._last_result: ConnectionResult | None = None

        self._request_count = 0
        self._success_count = 0
        self._failure_count = 0

    # ========================================================
    # ACCESS
    # ========================================================

    @property
    def core(self) -> Any:
        """
        Return the supplied Core boundary.
        """

        return self._core

    def get_core(self) -> Any:
        """
        Return the supplied Core boundary.
        """

        return self._core

    # ========================================================
    # CONNECTION REQUEST
    # ========================================================

    def request_connection(
        self,
        source_terminal_id: Any,
        target_terminal_id: Any,
        *,
        connection_type: Any = None,
        presentation_hint: Mapping[str, Any] | None = None,
    ) -> ConnectionResult:
        """
        Request a terminal-to-terminal connection.

        Core remains authoritative for validation and creation.
        """

        self._ensure_active()

        request = ConnectionRequest(
            source_terminal_id=source_terminal_id,
            target_terminal_id=target_terminal_id,
            connection_type=connection_type,
            presentation_hint=presentation_hint,
        )

        self._request_count += 1

        validation = self.validate_connection(
            request
        )

        if not self._validation_succeeded(
            validation
        ):
            result = ConnectionResult.failed(
                "connect",
                self._extract_error(
                    validation,
                    "Connection validation failed.",
                ),
                validation=validation,
            )

            self._record_failure(
                result
            )

            return result

        try:
            response = self._execute_connection(
                request
            )

        except Exception as exc:
            result = ConnectionResult.failed(
                "connect",
                exc,
                validation=validation,
            )

            self._record_failure(
                result
            )

            return result

        result = self._normalize_result(
            "connect",
            response,
            validation=validation,
        )

        self._record_result(
            result
        )

        return result

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_connection(
        self,
        request: ConnectionRequest,
    ) -> Any:
        """
        Ask Core to validate a connection request.

        No electrical validation is performed locally.
        """

        self._ensure_active()

        if not isinstance(
            request,
            ConnectionRequest,
        ):
            raise TypeError(
                "request must be a ConnectionRequest."
            )

        validator = getattr(
            self._core,
            "validate_connection",
            None,
        )

        if callable(
            validator
        ):
            return validator(
                request
            )

        # ----------------------------------------------------
        # Some Core command boundaries expose validation under
        # an explicit network/topology interface.
        # ----------------------------------------------------

        network = self._resolve_network_boundary()

        validator = getattr(
            network,
            "validate_connection",
            None,
        )

        if callable(
            validator
        ):
            return validator(
                request
            )

        # ----------------------------------------------------
        # No local validation fallback is permitted.
        # ----------------------------------------------------

        raise AttributeError(
            "Core does not expose validate_connection()."
        )

    # ========================================================
    # DISCONNECT
    # ========================================================

    def request_disconnect(
        self,
        connection_id: Any,
    ) -> ConnectionResult:
        """
        Request removal of an authoritative connection.
        """

        self._ensure_active()

        if connection_id is None:
            raise ValueError(
                "connection_id must not be None."
            )

        self._request_count += 1

        try:
            response = self._execute_disconnect(
                connection_id
            )

        except Exception as exc:
            result = ConnectionResult.failed(
                "disconnect",
                exc,
            )

            self._record_failure(
                result
            )

            return result

        result = self._normalize_result(
            "disconnect",
            response,
            connection_id=connection_id,
        )

        self._record_result(
            result
        )

        return result

    # ========================================================
    # MODIFY
    # ========================================================

    def request_modify_connection(
        self,
        connection_id: Any,
        presentation_data: Mapping[str, Any] | None = None,
    ) -> ConnectionResult:
        """
        Request modification of connection presentation data.

        Electrical topology remains owned by Core.

        Graphical routing/presentation data are passed through
        as opaque metadata.
        """

        self._ensure_active()

        if connection_id is None:
            raise ValueError(
                "connection_id must not be None."
            )

        if presentation_data is None:
            presentation_data = {}

        if not isinstance(
            presentation_data,
            Mapping,
        ):
            raise TypeError(
                "presentation_data must be a mapping or None."
            )

        self._request_count += 1

        try:
            response = self._execute_modify(
                connection_id,
                dict(presentation_data),
            )

        except Exception as exc:
            result = ConnectionResult.failed(
                "modify",
                exc,
                connection_id=connection_id,
            )

            self._record_failure(
                result
            )

            return result

        result = self._normalize_result(
            "modify",
            response,
            connection_id=connection_id,
        )

        self._record_result(
            result
        )

        return result

    # ========================================================
    # CORE DISPATCH
    # ========================================================

    def _execute_connection(
        self,
        request: ConnectionRequest,
    ) -> Any:
        """
        Dispatch a connection request to Core.

        The controller supports the canonical Core API first.
        """

        method = getattr(
            self._core,
            "request_connection",
            None,
        )

        if callable(
            method
        ):
            return method(
                request
            )

        method = getattr(
            self._core,
            "connect",
            None,
        )

        if callable(
            method
        ):
            return method(
                request
            )

        network = self._resolve_network_boundary()

        method = getattr(
            network,
            "connect",
            None,
        )

        if callable(
            method
        ):
            return method(
                request
            )

        raise AttributeError(
            "Core does not expose a connection operation."
        )

    # --------------------------------------------------------

    def _execute_disconnect(
        self,
        connection_id: Any,
    ) -> Any:
        """
        Dispatch a disconnect request to Core.
        """

        method = getattr(
            self._core,
            "request_disconnect",
            None,
        )

        if callable(
            method
        ):
            return method(
                connection_id
            )

        method = getattr(
            self._core,
            "disconnect",
            None,
        )

        if callable(
            method
        ):
            return method(
                connection_id
            )

        network = self._resolve_network_boundary()

        method = getattr(
            network,
            "disconnect",
            None,
        )

        if callable(
            method
        ):
            return method(
                connection_id
            )

        raise AttributeError(
            "Core does not expose a disconnect operation."
        )

    # --------------------------------------------------------

    def _execute_modify(
        self,
        connection_id: Any,
        presentation_data: Mapping[str, Any],
    ) -> Any:
        """
        Dispatch a connection modification to Core.
        """

        method = getattr(
            self._core,
            "request_modify_connection",
            None,
        )

        if callable(
            method
        ):
            return method(
                connection_id,
                presentation_data,
            )

        method = getattr(
            self._core,
            "modify_connection",
            None,
        )

        if callable(
            method
        ):
            return method(
                connection_id,
                presentation_data,
            )

        network = self._resolve_network_boundary()

        method = getattr(
            network,
            "modify_connection",
            None,
        )

        if callable(
            method
        ):
            return method(
                connection_id,
                presentation_data,
            )

        raise AttributeError(
            "Core does not expose a connection modification "
            "operation."
        )

    # ========================================================
    # NETWORK BOUNDARY
    # ========================================================

    def _resolve_network_boundary(self) -> Any:
        """
        Resolve an optional Core network/topology boundary.

        This method performs dependency discovery only.
        It does not create or own a network object.
        """

        network = getattr(
            self._core,
            "network",
            None,
        )

        if network is not None:
            return network

        getter = getattr(
            self._core,
            "get_network",
            None,
        )

        if callable(
            getter
        ):
            network = getter()

            if network is not None:
                return network

        topology = getattr(
            self._core,
            "topology",
            None,
        )

        if topology is not None:
            return topology

        getter = getattr(
            self._core,
            "get_topology",
            None,
        )

        if callable(
            getter
        ):
            topology = getter()

            if topology is not None:
                return topology

        raise AttributeError(
            "Core does not expose a network or topology boundary."
        )

    # ========================================================
    # RESULT NORMALIZATION
    # ========================================================

    def _normalize_result(
        self,
        operation: str,
        response: Any,
        *,
        connection_id: Any = None,
        validation: Any = None,
    ) -> ConnectionResult:
        """
        Convert a Core response into ConnectionResult.
        """

        if isinstance(
            response,
            ConnectionResult,
        ):
            return response

        if response is None:
            return ConnectionResult.succeeded(
                operation,
                connection_id=connection_id,
                validation=validation,
            )

        if isinstance(
            response,
            bool,
        ):
            if response:
                return ConnectionResult.succeeded(
                    operation,
                    connection_id=connection_id,
                    validation=validation,
                )

            return ConnectionResult.failed(
                operation,
                "Core rejected the operation.",
                connection_id=connection_id,
                validation=validation,
            )

        if isinstance(
            response,
            Mapping,
        ):
            success = response.get(
                "success",
                response.get(
                    "ok",
                    True,
                ),
            )

            response_connection_id = response.get(
                "connection_id",
                connection_id,
            )

            error = response.get(
                "error"
            )

            response_validation = response.get(
                "validation",
                validation,
            )

            if success:
                return ConnectionResult.succeeded(
                    operation,
                    connection_id=response_connection_id,
                    validation=response_validation,
                    data=response,
                )

            return ConnectionResult.failed(
                operation,
                (
                    error
                    if error is not None
                    else "Core rejected the operation."
                ),
                validation=response_validation,
                data=response,
            )

        success = getattr(
            response,
            "success",
            None,
        )

        if success is False:
            return ConnectionResult.failed(
                operation,
                getattr(
                    response,
                    "error",
                    "Core rejected the operation.",
                ),
                validation=getattr(
                    response,
                    "validation",
                    validation,
                ),
            )

        response_connection_id = getattr(
            response,
            "connection_id",
            connection_id,
        )

        return ConnectionResult.succeeded(
            operation,
            connection_id=response_connection_id,
            validation=getattr(
                response,
                "validation",
                validation,
            ),
            data={
                "response": response,
            },
        )

    # ========================================================
    # VALIDATION HELPERS
    # ========================================================

    @staticmethod
    def _validation_succeeded(
        validation: Any,
    ) -> bool:
        """
        Interpret a Core validation response.

        A boolean response is interpreted directly.

        Mapping/object responses may expose:

            valid
            success
            ok
        """

        if isinstance(
            validation,
            bool,
        ):
            return validation

        if isinstance(
            validation,
            Mapping,
        ):
            if "valid" in validation:
                return bool(
                    validation["valid"]
                )

            if "success" in validation:
                return bool(
                    validation["success"]
                )

            if "ok" in validation:
                return bool(
                    validation["ok"]
                )

            return True

        valid = getattr(
            validation,
            "valid",
            None,
        )

        if valid is not None:
            return bool(
                valid
            )

        success = getattr(
            validation,
            "success",
            None,
        )

        if success is not None:
            return bool(
                success
            )

        return True

    # --------------------------------------------------------

    @staticmethod
    def _extract_error(
        response: Any,
        default: Any,
    ) -> Any:
        """
        Extract an error from a validation response.
        """

        if isinstance(
            response,
            Mapping,
        ):
            return response.get(
                "error",
                response.get(
                    "reason",
                    default,
                ),
            )

        error = getattr(
            response,
            "error",
            None,
        )

        if error is not None:
            return error

        reason = getattr(
            response,
            "reason",
            None,
        )

        if reason is not None:
            return reason

        return default

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_last_result(
        self,
    ) -> ConnectionResult | None:
        """
        Return the most recent normalized operation result.
        """

        return self._last_result

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic controller state.

        This is diagnostic information only and is not an
        electrical model state representation.
        """

        return {
            "has_core": self._core is not None,
            "disposed": self._disposed,
            "request_count": self._request_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "has_last_result": (
                self._last_result is not None
            ),
        }

    # ========================================================
    # RESULT TRACKING
    # ========================================================

    def _record_result(
        self,
        result: ConnectionResult,
    ) -> None:
        self._last_result = result

        if result.success:
            self._success_count += 1
        else:
            self._failure_count += 1

    def _record_failure(
        self,
        result: ConnectionResult,
    ) -> None:
        self._last_result = result
        self._failure_count += 1

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose the controller.

        The Core object itself is never destroyed.
        """

        if self._disposed:
            return

        self._disposed = True

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        if self._disposed:
            raise RuntimeError(
                "ConnectionController has been disposed."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        return (
            "ConnectionController("
            f"disposed={self._disposed}, "
            f"requests={self._request_count}, "
            f"successes={self._success_count}, "
            f"failures={self._failure_count}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ConnectionRequest",
    "ConnectionResult",
    "ConnectionController",
]
