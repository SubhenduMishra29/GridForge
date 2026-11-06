# ============================================================
# File: ui/tools/tool_events.py
# GridForge V2 — Tool Event Bus
# ============================================================
"""
Event bus for normalized GridForge V2 tool events.

This module is intentionally distinct from ``tool_event.py``.

    tool_event.py
        Defines the immutable ToolEvent data contract.

    tool_events.py
        Provides the event-dispatch mechanism used to publish
        and subscribe to ToolEvent instances.

Architecture
------------

    GraphicsView / InteractionController
                    │
                    ▼
                ToolEvent
                    │
                    ▼
              ToolEventBus
               ┌────┼─────┐
               ▼    ▼     ▼
             Tool   UI   Controller
             logic       observers

The event bus is a UI coordination mechanism only.

It does NOT:

    - mutate Core;
    - execute commands;
    - validate electrical topology;
    - own tool state;
    - replace ToolManager;
    - replace CommandManager;
    - discover plugins.

No Qt dependency is required in this module.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, DefaultDict, Optional

from ui.tools.tool_event import ToolEvent, ToolEventType


ToolEventHandler = Callable[[ToolEvent], None]


@dataclass(frozen=True, slots=True)
class ToolEventSubscription:
    """
    Immutable subscription handle.

    The handle can be retained by the caller and passed to
    ``ToolEventBus.unsubscribe()`` to remove the subscription.
    """

    subscription_id: int
    event_type: ToolEventType

    @property
    def id(self) -> int:
        """
        Return the stable subscription identifier.
        """

        return self.subscription_id


class ToolEventBus:
    """
    Lightweight synchronous event bus for ToolEvent instances.

    Dispatch is deterministic:

        1. handlers registered for the specific event type;
        2. wildcard handlers registered for all event types.

    Handlers are invoked in registration order.

    The bus does not swallow handler exceptions. Exceptions are
    propagated to the caller so that controller/application layers
    can decide how failures should be handled.
    """

    def __init__(self) -> None:
        """
        Initialize an empty event bus.
        """

        self._handlers: DefaultDict[
            ToolEventType,
            list[tuple[int, ToolEventHandler]],
        ] = defaultdict(list)

        self._wildcard_handlers: list[
            tuple[int, ToolEventHandler]
        ] = []

        self._next_subscription_id = 1

    # ========================================================
    # SUBSCRIPTION
    # ========================================================

    def subscribe(
        self,
        event_type: ToolEventType,
        handler: ToolEventHandler,
    ) -> ToolEventSubscription:
        """
        Subscribe to one event type.

        Parameters
        ----------
        event_type:
            Event type to observe.

        handler:
            Callable accepting one ToolEvent.

        Returns
        -------
        ToolEventSubscription
            Subscription handle used for unsubscription.
        """

        self._validate_event_type(
            event_type
        )

        self._validate_handler(
            handler
        )

        subscription_id = self._allocate_id()

        self._handlers[event_type].append(
            (
                subscription_id,
                handler,
            )
        )

        return ToolEventSubscription(
            subscription_id=subscription_id,
            event_type=event_type,
        )

    # --------------------------------------------------------

    def subscribe_all(
        self,
        handler: ToolEventHandler,
    ) -> ToolEventSubscription:
        """
        Subscribe to all ToolEvent types.
        """

        self._validate_handler(
            handler
        )

        subscription_id = self._allocate_id()

        self._wildcard_handlers.append(
            (
                subscription_id,
                handler,
            )
        )

        # ``ToolEventType`` has no wildcard member. The event type
        # stored in the handle is therefore intentionally represented
        # by the first enum member only for structural compatibility.
        #
        # ``unsubscribe()`` uses the subscription ID as the
        # authoritative identity.
        return ToolEventSubscription(
            subscription_id=subscription_id,
            event_type=ToolEventType.RESET,
        )

    # ========================================================
    # UNSUBSCRIPTION
    # ========================================================

    def unsubscribe(
        self,
        subscription: ToolEventSubscription,
    ) -> bool:
        """
        Remove a subscription.

        Returns
        -------
        bool
            True when a subscription was removed, otherwise False.
        """

        if not isinstance(
            subscription,
            ToolEventSubscription,
        ):
            raise TypeError(
                "subscription must be a ToolEventSubscription."
            )

        subscription_id = subscription.subscription_id

        for event_type, handlers in self._handlers.items():
            for index, (
                current_id,
                _handler,
            ) in enumerate(handlers):
                if current_id == subscription_id:
                    del handlers[index]
                    return True

        for index, (
            current_id,
            _handler,
        ) in enumerate(
            self._wildcard_handlers
        ):
            if current_id == subscription_id:
                del self._wildcard_handlers[index]
                return True

        return False

    # --------------------------------------------------------

    def unsubscribe_handler(
        self,
        event_type: ToolEventType,
        handler: ToolEventHandler,
    ) -> int:
        """
        Remove all matching subscriptions for an event type.

        Returns
        -------
        int
            Number of removed subscriptions.
        """

        self._validate_event_type(
            event_type
        )

        self._validate_handler(
            handler
        )

        handlers = self._handlers.get(
            event_type,
            [],
        )

        original_count = len(
            handlers
        )

        self._handlers[event_type] = [
            (
                subscription_id,
                registered_handler,
            )
            for subscription_id, registered_handler in handlers
            if registered_handler is not handler
        ]

        return (
            original_count
            - len(
                self._handlers[event_type]
            )
        )

    # --------------------------------------------------------

    def unsubscribe_all(
        self,
        handler: ToolEventHandler,
    ) -> int:
        """
        Remove all wildcard subscriptions for a handler.

        Returns
        -------
        int
            Number of removed subscriptions.
        """

        self._validate_handler(
            handler
        )

        original_count = len(
            self._wildcard_handlers
        )

        self._wildcard_handlers = [
            (
                subscription_id,
                registered_handler,
            )
            for subscription_id, registered_handler
            in self._wildcard_handlers
            if registered_handler is not handler
        ]

        return (
            original_count
            - len(
                self._wildcard_handlers
            )
        )

    # ========================================================
    # PUBLICATION
    # ========================================================

    def publish(
        self,
        event: ToolEvent,
    ) -> int:
        """
        Publish a ToolEvent synchronously.

        Returns
        -------
        int
            Number of handlers invoked.

        Notes
        -----
        A snapshot of the current handlers is taken before
        dispatch. This means handlers may safely subscribe or
        unsubscribe during dispatch without corrupting iteration.
        """

        if not isinstance(
            event,
            ToolEvent,
        ):
            raise TypeError(
                "event must be a ToolEvent."
            )

        specific_handlers = tuple(
            self._handlers.get(
                event.event_type,
                (),
            )
        )

        wildcard_handlers = tuple(
            self._wildcard_handlers
        )

        count = 0

        for _subscription_id, handler in specific_handlers:
            handler(event)
            count += 1

        for _subscription_id, handler in wildcard_handlers:
            handler(event)
            count += 1

        return count

    # --------------------------------------------------------

    def emit(
        self,
        event: ToolEvent,
    ) -> int:
        """
        Alias for ``publish()``.
        """

        return self.publish(
            event
        )

    # ========================================================
    # TOOL-SPECIFIC DISPATCH
    # ========================================================

    def publish_for_tool(
        self,
        tool_id: str,
        event: ToolEvent,
    ) -> int:
        """
        Publish an event while adding its tool ID as event data.

        The original ToolEvent is immutable, so a derived event is
        created when necessary.

        This method does not modify the event's existing semantic
        fields.
        """

        if not isinstance(
            tool_id,
            str,
        ) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        if not isinstance(
            event,
            ToolEvent,
        ):
            raise TypeError(
                "event must be a ToolEvent."
            )

        if event.get(
            "tool_id"
        ) == tool_id:
            return self.publish(
                event
            )

        derived_event = event.with_data(
            tool_id=tool_id
        )

        return self.publish(
            derived_event
        )

    # ========================================================
    # MANAGEMENT
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove every subscription.
        """

        self._handlers.clear()
        self._wildcard_handlers.clear()

    # --------------------------------------------------------

    def clear_event_type(
        self,
        event_type: ToolEventType,
    ) -> None:
        """
        Remove all subscriptions for one event type.
        """

        self._validate_event_type(
            event_type
        )

        self._handlers.pop(
            event_type,
            None,
        )

    # ========================================================
    # QUERIES
    # ========================================================

    def has_subscribers(
        self,
        event_type: Optional[ToolEventType] = None,
    ) -> bool:
        """
        Return whether subscribers exist.

        If ``event_type`` is None, any subscriber is sufficient.
        """

        if event_type is not None:
            self._validate_event_type(
                event_type
            )

            return bool(
                self._handlers.get(
                    event_type
                )
                or self._wildcard_handlers
            )

        return any(
            self._handlers.values()
        ) or bool(
            self._wildcard_handlers
        )

    # --------------------------------------------------------

    def subscriber_count(
        self,
        event_type: Optional[ToolEventType] = None,
    ) -> int:
        """
        Return the number of subscribers.

        When an event type is supplied, wildcard subscribers are
        included because they also receive that event.
        """

        if event_type is None:
            return (
                sum(
                    len(handlers)
                    for handlers in self._handlers.values()
                )
                + len(
                    self._wildcard_handlers
                )
            )

        self._validate_event_type(
            event_type
        )

        return (
            len(
                self._handlers.get(
                    event_type,
                    (),
                )
            )
            + len(
                self._wildcard_handlers
            )
        )

    # --------------------------------------------------------

    def subscription_count(
        self,
    ) -> int:
        """
        Return the total number of active subscriptions.
        """

        return self.subscriber_count()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, object]:
        """
        Return a deterministic diagnostic snapshot.
        """

        handlers_by_type = {
            event_type.value: len(handlers)
            for event_type, handlers
            in self._handlers.items()
            if handlers
        }

        return {
            "subscription_count": self.subscription_count(),
            "wildcard_subscription_count": len(
                self._wildcard_handlers
            ),
            "handlers_by_event": handlers_by_type,
        }

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return the total number of subscriptions.
        """

        return self.subscription_count()

    # --------------------------------------------------------

    def __bool__(
        self,
    ) -> bool:
        """
        Return True when at least one subscription exists.
        """

        return self.has_subscribers()

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _allocate_id(
        self,
    ) -> int:
        """
        Allocate the next subscription ID.
        """

        subscription_id = (
            self._next_subscription_id
        )

        self._next_subscription_id += 1

        return subscription_id

    # --------------------------------------------------------

    @staticmethod
    def _validate_event_type(
        event_type: ToolEventType,
    ) -> None:
        """
        Validate an event type.
        """

        if not isinstance(
            event_type,
            ToolEventType,
        ):
            raise TypeError(
                "event_type must be a ToolEventType."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_handler(
        handler: ToolEventHandler,
    ) -> None:
        """
        Validate an event handler.
        """

        if not callable(
            handler
        ):
            raise TypeError(
                "handler must be callable."
            )


__all__ = [
    "ToolEventHandler",
    "ToolEventSubscription",
    "ToolEventBus",
]
