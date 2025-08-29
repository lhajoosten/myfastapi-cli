# Mediator Behaviors

Mediator behaviors are pipeline components that wrap command/query handler execution.

They can be used for logging, metrics, tracing, authorization checks, caching, retries, etc.

## How It Works

1. Handlers register with the global `mediator`.
2. When `mediator.send()` or `mediator.ask()` is invoked, the mediator constructs a call chain of behaviors.
3. Each behavior receives `(next_, message)` where:
   - `next_` is a callable to invoke the next behavior / final handler
   - `message` is the command or query instance
4. A behavior can short‑circuit (return early) or modify the result.

## Example

```python
from app.application.common.cqrs import mediator, Behavior
from app.application.common.models.result_model import Result

def timing_behavior(next_, message):
    import time
    start = time.perf_counter()
    res = next_(message)
    duration = (time.perf_counter() - start) * 1000
    # Replace with structured log / metrics emitter
    print(f"Handled {type(message).__name__} in {duration:.2f} ms")
    return res

mediator.add_behavior(timing_behavior)
```

## Error Handling

Unhandled exceptions inside handlers are caught and converted into `Result.fail("<error>")`.

## Writing Reusable Behaviors

Patterns:

- **Logging**: log before/after with correlation ids.
- **Metrics**: record durations grouped by message type.
- **Validation**: detect invalid command state and return `Result.fail("VALIDATION_ERROR")`.
- **Caching (queries)**: return cached response when available; only call `next_` on miss.

```python
def cache_behavior(next_, message):
    if type(message).__name__.startswith("Get"):  # naive example
        key = (type(message).__name__, tuple(sorted(message.model_dump().items())))
        if key in CACHE:
            return CACHE[key]
        res = next_(message)
        if res.success:
            CACHE[key] = res
        return res
    return next_(message)
```

## Order Matters

Behaviors are executed in the order added. Add higher-level cross-cutting concerns (tracing, auth) first, then logging / metrics, then caching.

## Testing Behaviors

You can unit test a behavior by invoking it with a fake `next_`:

```python
def test_logging_behavior():
    logs = []
    def log_behavior(next_, message):
        logs.append(f"before:{type(message).__name__}")
        res = next_(message)
        logs.append(f"after:{type(message).__name__}")
        return res
    class Dummy: pass
    def handler(msg): return Result.ok(1)
    # Manually compose
    res = log_behavior(handler, Dummy())
    assert res.success and logs == ["before:Dummy", "after:Dummy"]
```

---

See also: `docs/architecture.md` for an overview and `generate-crud` output for usage patterns.
