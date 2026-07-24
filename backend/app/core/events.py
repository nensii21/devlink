import asyncio
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    A simple centralized Event Bus for handling decoupled publish/subscribe events.
    Supports both synchronous and asynchronous event handlers.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Subscribe a handler function to a specific event name."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to event {event_name}")

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """Unsubscribe a handler from a specific event name."""
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)
            logger.debug(f"Unsubscribed {handler.__name__} from event {event_name}")

    def publish(self, event_name: str, **kwargs: Any) -> None:
        """
        Publish an event, calling all subscribed handlers with the provided keyword arguments.
        If a handler is a coroutine function, it will be scheduled as an asyncio task.
        """
        handlers = self._subscribers.get(event_name, [])
        logger.debug(f"Publishing event {event_name} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(
                        self._safe_async_call(handler, event_name, **kwargs)
                    )
                else:
                    handler(**kwargs)
            except Exception as e:
                logger.error(
                    f"Error executing handler {handler.__name__} for event {event_name}: {e}",
                    exc_info=True,
                )

    async def _safe_async_call(
        self, handler: Callable, event_name: str, **kwargs: Any
    ) -> None:
        try:
            await handler(**kwargs)
        except Exception as e:
            logger.error(
                f"Error executing async handler {handler.__name__} for event {event_name}: {e}",
                exc_info=True,
            )


# Global instance to be used across the application
event_bus = EventBus()
