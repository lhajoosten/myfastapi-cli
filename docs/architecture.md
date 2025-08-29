# Architecture Overview

This CLI scaffolds FastAPI backends following Clean Architecture principles, optionally in a vertical slice (modular) mode.

## Layers (Layered Template)

- Domain: Entities & value objects (pure business models)
- Application: CQRS commands/queries, services, orchestration
- Infrastructure: External concerns (repositories, DB, messaging, gateways)
- Presentation: FastAPI routers, middleware, HTTP specifics
- Core: Cross-cutting concerns (config, DI, security, logging, exceptions)

## Modular (Vertical Slice) Mode

Each module replicates its own mini clean architecture (domain, application, infrastructure, presentation) enabling high cohesion and low coupling. Shared cross-cutting utilities still reside in `app/core`.

## CQRS & Mediator

The generator uses Commands / Queries whose handlers register with a lightweight in-process mediator (`application/common/cqrs.py`).

Key points:

- Handlers register themselves on import (side-effect) with `mediator.register_command` / `register_query`.
- A simple pipeline supports behaviors (logging added by default). Add custom behaviors via `mediator.add_behavior(callable)`.
- Handlers return either raw values or a `Result` object. Raw values are wrapped into `Result.ok(value)` automatically.
- Exceptions are caught and transformed into `Result.fail(message)`; routers translate failure codes to HTTP status codes.

Result Pattern:

```python
Result.ok(value)       # success wrapper
Result.fail(error_code_or_message)
```

Routers check `res.success` and map `NOT_FOUND` to 404, defaulting to 400 / 500 where appropriate.

## Authentication

The layered template ships with JWT auth: register/login/me endpoints, role-based dependency helper `require_roles`. In modular mode an `auth` module is always created (or inserted) to supply similar capabilities.

## Extensibility

- Add modules (modular mode): `myfastapi add-module <name>`
- Generate CRUD skeletons: `myfastapi generate-crud EntityName --path <project>`
- Replace in-memory repositories with real implementations (e.g. SQLAlchemy) under `infrastructure/`.

## Future Roadmap Items

- Rich mediator with pipeline behaviors
- Pluggable persistence adapters
- Background job / task abstraction
- Event sourcing / outbox pattern helpers
- Frontend scaffold generator
