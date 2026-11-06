# ============================================================
# File: ui/tools/tool_hooks.py
# GridForge V2 — Tool Hooks
# ============================================================
"""
Lifecycle hooks for GridForge V2 tools.

ToolHooks provides an explicit, framework-neutral hook contract for
tool lifecycle and interaction notifications.

The hook layer deliberately does not own:
    - tool state;
    - tool activation policy;
    - event dispatch;
    - command execution;
    - rendering;
    - Core/domain mutation.

Those responsibilities remain with ToolManager, ToolDispatcher,
CommandController, RenderSystem, and Core respectively.

Hooks are notification points. They may observe lifecycle transitions
and interaction phases, but they must not become a hidden application
event bus.

Design goals
------------
- deterministic lifecycle ordering;
- explicit hook names;
- no Qt dependency;
- no global state;
- safe default no-op implementations;
- support for concrete tools and tool adapters;
- optional hook failure isolation;
- compatibility with the existing ToolContext/ToolEnvironment model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Optional, Protocol


# ============================================================
# HOOK PHASE
# ============================================================


class ToolHookPhase(str, Enum):
    """
    Lifecycle phase associated with a tool hook.
    """

    BEFORE_ACTIVATE = "before_activate"
    AFTER_ACTIVATE = "after_activate"

    BEFORE_DEACTIVATE = "before_deactivate"
    AFTER_DEACTIVATE = "after_deactivate"

    BEFORE_SUSPEND = "before_suspend"
    AFTER_SUSPEND = "after_suspend"

    BEFORE_RESUME = "before_resume"
    AFTER_RESUME = "after_resume"

    BEFORE_RESET = "before_reset"
    AFTER_RESET = "after_reset"

    BEFORE_CANCEL = "before_cancel"
    AFTER_CANCEL = "after_cancel"

    BEFORE_EVENT = "before_event"
    AFTER_EVENT = "after_event"

    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"

    ERROR = "error"


# ============================================================
# HOOK RESULT
# ============================================================


class ToolHookResult(str, Enum):
    """
    Result returned by a hook invocation.

    Hooks are primarily observational. A BLOCK result is supported
    for lifecycle policies that explicitly opt into veto semantics.
    """

    CONTINUE = "continue"
    BLOCK = "block"


# ============================================================
# HOOK ERROR POLICY
# ============================================================


class ToolHookErrorPolicy(str, Enum):
    """
    Defines how hook exceptions are handled.
    """

    PROPAGATE = "propagate"
    IGNORE = "ignore"
    COLLECT = "collect"


# ============================================================
# HOOK CONTEXT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolHookContext:
    """
    Immutable context supplied to a hook.

    The payload is deliberately generic because the hook layer must
    not depend on concrete Qt event classes or specific tool
    implementations.
    """

    phase: ToolHookPhase

    tool: Any = None

    previous_tool: Any = None

    next_tool: Any = None

    context: Any = None

    event: Any = None

    result: Any = None

    error: Optional[BaseException] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def failed(self) -> bool:
        """Return whether the hook context represents an error."""

        return self.error is not None

    def with_metadata(
        self,
        **metadata: Any,
    ) -> ToolHookContext:
        """Return a copy with merged metadata."""

        merged = dict(self.metadata)
        merged.update(metadata)

        return ToolHookContext(
            phase=self.phase,
            tool=self.tool,
            previous_tool=self.previous_tool,
            next_tool=self.next_tool,
            context=self.context,
            event=self.event,
            result=self.result,
            error=self.error,
            metadata=merged,
        )


# ============================================================
# HOOK PROTOCOL
# ============================================================


class ToolHook(Protocol):
    """
    Protocol implemented by objects participating in tool hooks.
    """

    def __call__(
        self,
        context: ToolHookContext,
    ) -> ToolHookResult | None:
        """
        Execute a hook.

        Returning None is equivalent to CONTINUE.
        """
        ...


# ============================================================
# HOOK RECORD
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolHookRecord:
    """
    Registered hook descriptor.
    """

    name: str

    callback: ToolHook

    phases: frozenset[ToolHookPhase]

    priority: int = 0

    enabled: bool = True

    once: bool = False

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def matches(
        self,
        phase: ToolHookPhase,
    ) -> bool:
        """Return whether this hook applies to a phase."""

        return (
            self.enabled
            and phase in self.phases
        )


# ============================================================
# HOOK ERROR
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolHookError:
    """
    Captured hook execution error.
    """

    hook_name: str

    phase: ToolHookPhase

    exception: BaseException

    context: ToolHookContext

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "hook_name": self.hook_name,
            "phase": self.phase.value,
            "exception_type": type(
                self.exception
            ).__name__,
            "message": str(
                self.exception
            ),
        }


# ============================================================
# HOOK EXECUTION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolHookExecution:
    """
    Aggregate result of dispatching hooks for one phase.
    """

    phase: ToolHookPhase

    result: ToolHookResult = (
        ToolHookResult.CONTINUE
    )

    executed: tuple[str, ...] = ()

    errors: tuple[ToolHookError, ...] = ()

    blocked_by: Optional[str] = None

    @property
    def blocked(self) -> bool:
        """Return whether hook execution was blocked."""

        return self.result == ToolHookResult.BLOCK

    @property
    def failed(self) -> bool:
        """Return whether any hook failed."""

        return bool(self.errors)

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "phase": self.phase.value,
            "result": self.result.value,
            "executed": list(self.executed),
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "blocked_by": self.blocked_by,
        }


# ============================================================
# HOOK COLLECTION
# ============================================================


class ToolHooks:
    """
    Explicit registry and dispatcher for tool lifecycle hooks.

    ToolHooks is intentionally local to a tool manager/controller or
    tool instance. It is not a process-wide event bus.
    """

    def __init__(
        self,
        *,
        error_policy: ToolHookErrorPolicy = (
            ToolHookErrorPolicy.PROPAGATE
        ),
    ) -> None:
        if not isinstance(
            error_policy,
            ToolHookErrorPolicy,
        ):
            raise TypeError(
                "error_policy must be ToolHookErrorPolicy."
            )

        self._error_policy = error_policy

        self._hooks: dict[
            str,
            ToolHookRecord,
        ] = {}

        self._counter = 0

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def error_policy(self) -> ToolHookErrorPolicy:
        """Return the active hook error policy."""

        return self._error_policy

    @property
    def count(self) -> int:
        """Return the number of registered hooks."""

        return len(self._hooks)

    @property
    def names(self) -> tuple[str, ...]:
        """Return registered hook names."""

        return tuple(
            self._hooks
        )

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        callback: ToolHook,
        *,
        name: Optional[str] = None,
        phases: Iterable[
            ToolHookPhase
        ] = (
            ToolHookPhase.BEFORE_EVENT,
            ToolHookPhase.AFTER_EVENT,
        ),
        priority: int = 0,
        enabled: bool = True,
        once: bool = False,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
        replace: bool = False,
    ) -> str:
        """
        Register a hook.

        Higher priority hooks execute first.

        Registration returns the canonical hook name.
        """

        if not callable(callback):
            raise TypeError(
                "callback must be callable."
            )

        normalized_phases = frozenset(
            phases
        )

        if not normalized_phases:
            raise ValueError(
                "At least one hook phase is required."
            )

        if any(
            not isinstance(
                phase,
                ToolHookPhase,
            )
            for phase in normalized_phases
        ):
            raise TypeError(
                "All phases must be ToolHookPhase values."
            )

        if name is None:
            name = self._generate_name(
                callback
            )
        else:
            name = name.strip()

            if not name:
                raise ValueError(
                    "Hook name must not be empty."
                )

        if (
            name in self._hooks
            and not replace
        ):
            raise ValueError(
                f"Hook {name!r} is already registered."
            )

        self._hooks[name] = ToolHookRecord(
            name=name,
            callback=callback,
            phases=normalized_phases,
            priority=priority,
            enabled=enabled,
            once=once,
            metadata=dict(
                metadata or {}
            ),
        )

        return name

    def unregister(
        self,
        name: str,
    ) -> bool:
        """Unregister a hook by name."""

        return (
            self._hooks.pop(
                name,
                None,
            )
            is not None
        )

    def clear(self) -> None:
        """Remove all hooks."""

        self._hooks.clear()

    # ========================================================
    # ENABLE / DISABLE
    # ========================================================

    def enable(
        self,
        name: str,
    ) -> bool:
        """Enable a registered hook."""

        record = self._hooks.get(
            name
        )

        if record is None:
            return False

        self._hooks[name] = ToolHookRecord(
            name=record.name,
            callback=record.callback,
            phases=record.phases,
            priority=record.priority,
            enabled=True,
            once=record.once,
            metadata=record.metadata,
        )

        return True

    def disable(
        self,
        name: str,
    ) -> bool:
        """Disable a registered hook."""

        record = self._hooks.get(
            name
        )

        if record is None:
            return False

        self._hooks[name] = ToolHookRecord(
            name=record.name,
            callback=record.callback,
            phases=record.phases,
            priority=record.priority,
            enabled=False,
            once=record.once,
            metadata=record.metadata,
        )

        return True

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether a hook is registered."""

        return name in self._hooks

    # ========================================================
    # DISPATCH
    # ========================================================

    def dispatch(
        self,
        context: ToolHookContext,
    ) -> ToolHookExecution:
        """
        Dispatch all matching hooks for a phase.

        Hooks are ordered by descending priority and then by
        registration order.
        """

        if not isinstance(
            context,
            ToolHookContext,
        ):
            raise TypeError(
                "context must be ToolHookContext."
            )

        records = sorted(
            (
                record
                for record in self._hooks.values()
                if record.matches(
                    context.phase
                )
            ),
            key=lambda record: (
                -record.priority,
                self._registration_order(
                    record.name
                ),
            ),
        )

        executed: list[str] = []
        errors: list[ToolHookError] = []

        for record in records:
            executed.append(
                record.name
            )

            try:
                result = record.callback(
                    context
                )

                if result is None:
                    result = ToolHookResult.CONTINUE

                if not isinstance(
                    result,
                    ToolHookResult,
                ):
                    result = ToolHookResult(
                        str(result)
                    )

            except BaseException as exc:
                error = ToolHookError(
                    hook_name=record.name,
                    phase=context.phase,
                    exception=exc,
                    context=context,
                )

                if (
                    self._error_policy
                    == ToolHookErrorPolicy.PROPAGATE
                ):
                    raise

                errors.append(
                    error
                )

                result = ToolHookResult.CONTINUE

            if record.once:
                self.unregister(
                    record.name
                )

            if result == ToolHookResult.BLOCK:
                return ToolHookExecution(
                    phase=context.phase,
                    result=ToolHookResult.BLOCK,
                    executed=tuple(
                        executed
                    ),
                    errors=tuple(
                        errors
                    ),
                    blocked_by=record.name,
                )

        return ToolHookExecution(
            phase=context.phase,
            result=ToolHookResult.CONTINUE,
            executed=tuple(
                executed
            ),
            errors=tuple(
                errors
            ),
        )

    # ========================================================
    # CONVENIENCE DISPATCHERS
    # ========================================================

    def before_activate(
        self,
        *,
        tool: Any,
        previous_tool: Any = None,
        next_tool: Any = None,
        context: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_ACTIVATE."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_ACTIVATE,
                tool=tool,
                previous_tool=previous_tool,
                next_tool=next_tool,
                context=context,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_activate(
        self,
        *,
        tool: Any,
        previous_tool: Any = None,
        context: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_ACTIVATE."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_ACTIVATE,
                tool=tool,
                previous_tool=previous_tool,
                context=context,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def before_deactivate(
        self,
        *,
        tool: Any,
        context: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_DEACTIVATE."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_DEACTIVATE,
                tool=tool,
                context=context,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_deactivate(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any
        ]] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_DEACTIVATE."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_DEACTIVATE,
                tool=tool,
                context=context,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def before_suspend(
        self,
        *,
        tool: Any,
        context: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_SUSPEND."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_SUSPEND,
                tool=tool,
                context=context,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_suspend(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_SUSPEND."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_SUSPEND,
                tool=tool,
                context=context,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def before_resume(
        self,
        *,
        tool: Any,
        context: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_RESUME."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_RESUME,
                tool=tool,
                context=context,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_resume(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_RESUME."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_RESUME,
                tool=tool,
                context=context,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def before_reset(
        self,
        *,
        tool: Any,
        context: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_RESET."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_RESET,
                tool=tool,
                context=context,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_reset(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_RESET."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_RESET,
                tool=tool,
                context=context,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def before_cancel(
        self,
        *,
        tool: Any,
        context: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_CANCEL."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_CANCEL,
                tool=tool,
                context=context,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_cancel(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_CANCEL."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_CANCEL,
                tool=tool,
                context=context,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def before_event(
        self,
        *,
        tool: Any,
        event: Any,
        context: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_EVENT."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_EVENT,
                tool=tool,
                event=event,
                context=context,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_event(
        self,
        *,
        tool: Any,
        event: Any,
        context: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_EVENT."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_EVENT,
                tool=tool,
                event=event,
                context=context,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def before_execute(
        self,
        *,
        tool: Any,
        context: Any = None,
        event: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch BEFORE_EXECUTE."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.BEFORE_EXECUTE,
                tool=tool,
                context=context,
                event=event,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def after_execute(
        self,
        *,
        tool: Any,
        context: Any = None,
        event: Any = None,
        result: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch AFTER_EXECUTE."""

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.AFTER_EXECUTE,
                tool=tool,
                context=context,
                event=event,
                result=result,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def error(
        self,
        *,
        tool: Any,
        error: BaseException,
        context: Any = None,
        event: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolHookExecution:
        """Dispatch ERROR."""

        if not isinstance(
            error,
            BaseException,
        ):
            raise TypeError(
                "error must be a BaseException."
            )

        return self.dispatch(
            ToolHookContext(
                phase=ToolHookPhase.ERROR,
                tool=tool,
                context=context,
                event=event,
                error=error,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _generate_name(
        self,
        callback: Callable[..., Any],
    ) -> str:
        """Generate a deterministic unique hook name."""

        self._counter += 1

        callback_name = getattr(
            callback,
            "__name__",
            callback.__class__.__name__,
        )

        return (
            f"{callback_name}:{self._counter}"
        )

    def _registration_order(
        self,
        name: str,
    ) -> int:
        """
        Return registration order.

        The numeric suffix generated by this class is used when
        possible. Explicitly named hooks retain deterministic
        insertion order through dictionary ordering.
        """

        try:
            suffix = name.rsplit(
                ":",
                1,
            )[-1]

            return int(
                suffix
            )
        except (
            ValueError,
            TypeError,
        ):
            try:
                return tuple(
                    self._hooks
                ).index(
                    name
                )
            except ValueError:
                return 0


# ============================================================
# FUNCTION ADAPTER
# ============================================================


def hook(
    callback: Callable[
        [ToolHookContext],
        ToolHookResult | None,
    ],
) -> ToolHook:
    """
    Adapt a normal callable to the ToolHook protocol.

    This function intentionally performs no wrapping because Python's
    callable protocol already matches the hook contract.
    """

    if not callable(callback):
        raise TypeError(
            "callback must be callable."
        )

    return callback


# ============================================================
# BUILT-IN NO-OP HOOKS
# ============================================================


class NullToolHooks:
    """
    No-op hook implementation.

    Useful for tools that do not need lifecycle notifications while
    avoiding conditional checks in higher-level orchestration.
    """

    def dispatch(
        self,
        context: ToolHookContext,
    ) -> ToolHookExecution:
        """Return an empty successful hook execution."""

        return ToolHookExecution(
            phase=context.phase,
            result=ToolHookResult.CONTINUE,
        )

    def before_activate(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_ACTIVATE
        )

    def after_activate(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_ACTIVATE
        )

    def before_deactivate(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_DEACTIVATE
        )

    def after_deactivate(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_DEACTIVATE
        )

    def before_suspend(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_SUSPEND
        )

    def after_suspend(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_SUSPEND
        )

    def before_resume(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_RESUME
        )

    def after_resume(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_RESUME
        )

    def before_reset(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_RESET
        )

    def after_reset(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_RESET
        )

    def before_cancel(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_CANCEL
        )

    def after_cancel(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_CANCEL
        )

    def before_event(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_EVENT
        )

    def after_event(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_EVENT
        )

    def before_execute(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.BEFORE_EXECUTE
        )

    def after_execute(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.AFTER_EXECUTE
        )

    def error(self, **kwargs: Any) -> ToolHookExecution:
        return self._empty(
            ToolHookPhase.ERROR
        )

    @staticmethod
    def _empty(
        phase: ToolHookPhase,
    ) -> ToolHookExecution:
        return ToolHookExecution(
            phase=phase,
            result=ToolHookResult.CONTINUE,
        )


__all__ = [
    "ToolHookPhase",
    "ToolHookResult",
    "ToolHookErrorPolicy",
    "ToolHookContext",
    "ToolHook",
    "ToolHookRecord",
    "ToolHookError",
    "ToolHookExecution",
    "ToolHooks",
    "hook",
    "NullToolHooks",
]
