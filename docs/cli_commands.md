# CLI Commands

## new

Scaffold a new project.

Usage:

```bash
myfastapi new <name> [--modular] [--modules auth,inventory]
```

## add-module

Add a module to an existing modular project.

```bash
myfastapi add-module <name> --path .
```

## generate-crud

Generate CRUD skeleton (command, query, service, router) for an entity.

```bash
myfastapi generate-crud Book --path myproject --full      # default full CRUD (create/get/update/delete/list)
myfastapi generate-crud Book --path myproject --minimal   # only create + get
myfastapi generate-crud Item --path myproject/app/inventory --modular
myfastapi generate-crud Order --path myproject --sqlalchemy  # also scaffold SQLAlchemy repo + service skeleton
myfastapi generate-crud Product --path myproject --fields "name:str,price:float,in_stock:bool"  # custom fields
```

Creates (layered):

- application/ENTITY_PLURAL/commands/create_ENTITY.py (+ update/delete if --full)
- application/ENTITY_PLURAL/queries/get_ENTITY.py (+ list if --full)
- application/ENTITY_PLURAL/services/ENTITY_service.py (in-memory or SQLAlchemy skeleton)
- presentation/api/routers/entity.py (FastAPI router using mediator + Result)
- (if --sqlalchemy) domain/entities/entity.py + infrastructure/repositories/entity_repository.py

Handlers return a `Result` object (`Result.ok(value)` or `Result.fail(code)`). Routers now use `unwrap_or_raise` from `presentation/api/utils/result_adapter.py` to convert a `Result` into a successful response or raise `HTTPException` with a mapped status code (default 400, or custom when provided, e.g. 404 on not found).

## list-routers

List router Python files in a layered project.

```bash
myfastapi list-routers --path myproject
```

## make-plugin

Create a plugin stub file under `plugins/`.

```bash
myfastapi make-plugin sampleplug --path myproject
```

Produces `plugins/sampleplug.py` with a sample command.

## Planned (future)

- Async generation flag (`--async`) for handlers/services
- Relationship scaffold (one-to-many / many-to-many helpers)
