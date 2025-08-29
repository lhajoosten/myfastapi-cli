"""CQRS abstractions + very small in-process mediator.

Generated handlers register themselves with the global `mediator` instance.
Routers then invoke `mediator.send(command)` or `mediator.ask(query)`.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Type, TypeVar, Protocol
import inspect
from .models.result_model import Result  # type: ignore[import-not-found]
import logging

logger = logging.getLogger("app.mediator")

TCommand = TypeVar("TCommand", bound="Command")
TQuery = TypeVar("TQuery", bound="Query")
TResult = TypeVar("TResult")


class Command:  # Marker base
    """Marker class for commands."""


class Query:  # Marker base
    """Marker class for queries."""


CommandHandler = Callable[[TCommand], Any]
QueryHandler = Callable[[TQuery], Any]


class Behavior(Protocol):  # pipeline behavior
    def __call__(self, next_: Callable[[Any], Any], message: Any) -> Any: ...


class Mediator:
    """Mediator with simple pipeline behaviors and Result wrapper support."""

    def __init__(self) -> None:
        self._command_handlers: Dict[Type[Command], CommandHandler] = {}
        self._query_handlers: Dict[Type[Query], QueryHandler] = {}
        self._behaviors: list[Behavior] = []

    # Registration -------------------------------------------------
    def register_command(self, t: Type[TCommand], handler: CommandHandler[TCommand]) -> None:  # type: ignore[misc]
        self._command_handlers[t] = handler

    def register_query(self, t: Type[TQuery], handler: QueryHandler[TQuery]) -> None:  # type: ignore[misc]
        self._query_handlers[t] = handler

    def add_behavior(self, behavior: Behavior) -> None:
        self._behaviors.append(behavior)

    # Internal -----------------------------------------------------
    def _invoke(self, message: Any, handler: Callable[[Any], Any]) -> Any:
        def call_chain(index: int, msg: Any) -> Any:
            if index == len(self._behaviors):
                return handler(msg)
            return self._behaviors[index](lambda m: call_chain(index + 1, m), msg)

        try:
            result = call_chain(0, message)
            return result
        except Exception as exc:  # pragma: no cover - generic safety
            logger.exception("Mediator handler error: %s", exc)
            return Result.fail(str(exc))

    # Dispatch -----------------------------------------------------
    def send(self, command: Command) -> Result[Any]:
        handler = self._command_handlers.get(type(command))
        if not handler:
            return Result.fail(f"No handler registered for command {type(command).__name__}")
        res = self._invoke(command, handler)
        return res if isinstance(res, Result) else Result.ok(res)

    async def send_async(self, command: Command) -> Result[Any]:  # pragma: no cover - thin wrapper
        handler = self._command_handlers.get(type(command))
        if not handler:
            return Result.fail(f"No handler registered for command {type(command).__name__}")
        res = self._invoke(command, handler)
        if inspect.iscoroutine(res):  # type: ignore[arg-type]
            res = await res  # type: ignore[assignment]
        return res if isinstance(res, Result) else Result.ok(res)

    def ask(self, query: Query) -> Result[Any]:
        handler = self._query_handlers.get(type(query))
        if not handler:
            return Result.fail(f"No handler registered for query {type(query).__name__}")
        res = self._invoke(query, handler)
        return res if isinstance(res, Result) else Result.ok(res)

    async def ask_async(self, query: Query) -> Result[Any]:  # pragma: no cover - thin wrapper
        handler = self._query_handlers.get(type(query))
        if not handler:
            return Result.fail(f"No handler registered for query {type(query).__name__}")
        res = self._invoke(query, handler)
        if inspect.iscoroutine(res):  # type: ignore[arg-type]
            res = await res  # type: ignore[assignment]
        return res if isinstance(res, Result) else Result.ok(res)


mediator = Mediator()

# Default logging behavior example
def _logging_behavior(next_: Callable[[Any], Any], message: Any) -> Any:
    logger.debug("Handling %s", type(message).__name__)
    result = next_(message)
    logger.debug("Handled %s", type(message).__name__)
    return result

mediator.add_behavior(_logging_behavior)
