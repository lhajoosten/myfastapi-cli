"""CLI entrypoint using Typer.

Commands:
    new         Create a new FastAPI project (layered by default, modular with --modular)
    add-module  Add a module (vertical slice) to an existing modular project
"""
from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import typer
from .plugins import load_plugins

app = typer.Typer(help="Scaffold Clean Architecture FastAPI backend projects.")
load_plugins(app)


TEMPLATE_ROOT = Path(__file__).parent / "templates"


def _copy_tree(src: Path, dst: Path, substitutions: dict[str, str]) -> None:
    """Copy a template directory tree performing naive text substitutions.

    Any file whose size is < 200KB is treated as text and has placeholder
    substitutions applied. Others are copied verbatim.
    """
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        for d in dirs:
            (dst / rel / d).mkdir(parents=True, exist_ok=True)
        for f in files:
            src_file = Path(root) / f
            rel_file = dst / rel / f
            rel_file.parent.mkdir(parents=True, exist_ok=True)
            data = src_file.read_bytes()
            if len(data) < 200_000:  # treat as text
                text = data.decode("utf-8")
                for k, v in substitutions.items():
                    text = text.replace(f"{{{{{k}}}}}", v)
                rel_file.write_text(text, encoding="utf-8")
            else:
                shutil.copy2(src_file, rel_file)


def _ensure_project_not_exists(path: Path) -> None:
    if path.exists():
        typer.secho(f"Path '{path}' already exists.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


def _generate_secret() -> str:
    return secrets.token_urlsafe(32)


@app.command()
def new(
    name: str = typer.Argument(..., help="Project name / directory to create"),
    modular: bool = typer.Option(False, "--modular", help="Generate modular (vertical slice) architecture"),
    modules: Optional[str] = typer.Option(None, "--modules", help="Comma separated list of initial modules (only if --modular)"),
    force: bool = typer.Option(False, "--force", help="Delete existing target directory if it exists"),
) -> None:
    """Create a new FastAPI project directory."""

    target_dir = Path(name).resolve()
    if target_dir.exists():
        if not force:
            _ensure_project_not_exists(target_dir)
        else:
            shutil.rmtree(target_dir)

    template_type = "modular" if modular else "layered"
    template_dir = TEMPLATE_ROOT / template_type
    if not template_dir.exists():
        typer.secho("Template directory missing – installation corrupted.", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    selected_modules: List[str] = []
    if modular:
        if modules:
            selected_modules = [m.strip() for m in modules.split(",") if m.strip()]
        else:
            answer = typer.prompt("Enter initial module names (comma separated)", default="auth")
            selected_modules = [m.strip() for m in answer.split(",") if m.strip()]
        # Ensure 'auth' present for built-in auth scaffold
        if "auth" not in selected_modules:
            selected_modules.insert(0, "auth")

    # Escape backslashes for safe inclusion in Python string literals (Windows paths)
    safe_name = name.replace("\\", "\\\\")
    substitutions = {
        "project_name": safe_name,
        "secret_key": _generate_secret(),
        "created_ts": datetime.now(timezone.utc).isoformat(),
    }

    _copy_tree(template_dir, target_dir, substitutions)

    if modular:
        modules_root = target_dir / "app"
        for module in selected_modules:
            _scaffold_module(modules_root, module, substitutions)

    typer.secho(f"Project '{name}' created using {template_type} template.", fg=typer.colors.GREEN)
    if modular:
        typer.echo(f"Modules: {', '.join(selected_modules)}")
    typer.echo("Next steps:\n  1. cd " + name + "\n  2. uvicorn app.main:app --reload")


def _scaffold_module(app_root: Path, module: str, substitutions: dict[str, str]) -> None:
    """Create a module skeleton inside a modular project."""
    module_dir = app_root / module
    if module_dir.exists():
        typer.secho(f"Module '{module}' already exists, skipping.", fg=typer.colors.YELLOW)
        return

    paths = [
        module_dir / "__init__.py",
        module_dir / "domain" / "entities" / "__init__.py",
        module_dir / "domain" / "value_objects" / "__init__.py",
        module_dir / "application" / "__init__.py",
        module_dir / "application" / "common" / "__init__.py",
        module_dir / "application" / "common" / "interfaces" / "__init__.py",
        module_dir / "application" / "common" / "models" / "__init__.py",
        module_dir / "application" / "services" / "__init__.py",
        module_dir / "infrastructure" / "__init__.py",
        module_dir / "infrastructure" / "repositories" / "__init__.py",
        module_dir / "presentation" / "__init__.py",
        module_dir / "presentation" / "api" / "routers" / "__init__.py",
    ]
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == ".py":
            if not p.exists():
                p.write_text("""""", encoding="utf-8")

    # Auth specific scaffolding
    if module == "auth":
        _write_auth_scaffold(module_dir, substitutions)
    else:
        _write_sample_endpoint(module_dir, module)


def _write_auth_scaffold(module_dir: Path, substitutions: dict[str, str]) -> None:
    """Richer auth scaffold for modular projects."""
    (module_dir / "application" / "services").mkdir(parents=True, exist_ok=True)
    (module_dir / "infrastructure" / "repositories").mkdir(parents=True, exist_ok=True)
    (module_dir / "presentation" / "api" / "routers").mkdir(parents=True, exist_ok=True)
    (module_dir / "domain" / "entities").mkdir(parents=True, exist_ok=True)

    (module_dir / "domain" / "entities" / "user.py").write_text(
        """from __future__ import annotations\nfrom dataclasses import dataclass, field\nfrom typing import List\n\n@dataclass(slots=True)\nclass User:\n    id: int\n    username: str\n    password_hash: str\n    roles: List[str] = field(default_factory=list)\n""",
        encoding="utf-8",
    )

    (module_dir / "infrastructure" / "repositories" / "user_repository.py").write_text(
        """from __future__ import annotations\nfrom typing import Protocol, runtime_checkable, Dict, List, Optional\nfrom .. ..domain.entities.user import User  # type: ignore[import-not-found]\n\n@runtime_checkable\nclass UserRepositoryProtocol(Protocol):\n    def create(self, username: str, password_hash: str, roles: List[str]) -> User: ...\n    def get_by_username(self, username: str) -> Optional[User]: ...\n    def get_by_id(self, user_id: int) -> Optional[User]: ...\n\nclass InMemoryUserRepository(UserRepositoryProtocol):\n    def __init__(self) -> None:\n        self._by_id: Dict[int, User] = {}\n        self._by_username: Dict[str, int] = {}\n        self._next_id = 1\n    def create(self, username: str, password_hash: str, roles: List[str]) -> User:\n        user = User(id=self._next_id, username=username, password_hash=password_hash, roles=roles)\n        self._by_id[self._next_id] = user\n        self._by_username[username] = self._next_id\n        self._next_id += 1\n        return user\n    def get_by_username(self, username: str) -> Optional[User]:\n        _id = self._by_username.get(username)\n        if _id is None: return None\n        return self._by_id.get(_id)\n    def get_by_id(self, user_id: int) -> Optional[User]:\n        return self._by_id.get(user_id)\n""",
        encoding="utf-8",
    )

    (module_dir / "application" / "services" / "auth_service.py").write_text(
        f"""from __future__ import annotations\nfrom datetime import timedelta\nfrom passlib.context import CryptContext\nfrom .. ..infrastructure.repositories.user_repository import InMemoryUserRepository\nfrom jose import jwt\nPWD_CONTEXT = CryptContext(schemes=['bcrypt'], deprecated='auto')\nALGORITHM='HS256'\nSECRET_KEY='{substitutions['secret_key']}'\n\nclass AuthService:\n    def __init__(self) -> None:\n        self._repo = InMemoryUserRepository()\n    def register(self, username: str, password: str):\n        if self._repo.get_by_username(username):\n            raise ValueError('User exists')\n        return self._repo.create(username, PWD_CONTEXT.hash(password), ['user'])\n    def authenticate(self, username: str, password: str) -> bool:\n        u = self._repo.get_by_username(username)\n        return bool(u and PWD_CONTEXT.verify(password, u.password_hash))\n    def create_access_token(self, user_id: int, username: str, roles: list[str]):\n        return jwt.encode({{'sub': str(user_id), 'username': username, 'roles':[r.lower() for r in roles]}}, SECRET_KEY, algorithm=ALGORITHM)\nAUTH_SERVICE = AuthService()\n""",
        encoding="utf-8",
    )

    (module_dir / "presentation" / "api" / "routers" / "auth.py").write_text(
        """from __future__ import annotations\nfrom fastapi import APIRouter, HTTPException\nfrom pydantic import BaseModel\nfrom ...application.services.auth_service import AUTH_SERVICE\nrouter = APIRouter(prefix='/auth', tags=['auth'])\nclass RegisterRequest(BaseModel): username: str; password: str\nclass LoginRequest(BaseModel): username: str; password: str\n@router.post('/register', status_code=201)\ndef register(req: RegisterRequest):\n    try: user = AUTH_SERVICE.register(req.username, req.password); return {'id': user.id, 'username': user.username}\n    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))\n@router.post('/login')\ndef login(req: LoginRequest):\n    if not AUTH_SERVICE.authenticate(req.username, req.password):\n        raise HTTPException(status_code=401, detail='invalid credentials')\n    user = AUTH_SERVICE._repo.get_by_username(req.username)  # noqa\n    token = AUTH_SERVICE.create_access_token(user.id, user.username, user.roles)  # type: ignore\n    return {'access_token': token, 'token_type': 'bearer'}\n""",
        encoding="utf-8",
    )


def _write_sample_endpoint(module_dir: Path, module: str) -> None:
    (module_dir / "presentation" / "api" / "routers").mkdir(parents=True, exist_ok=True)
    (module_dir / "presentation" / "api" / "routers" / f"{module}.py").write_text(
        f"""from __future__ import annotations\n\nfrom fastapi import APIRouter\n\nrouter = APIRouter(prefix=\"/{module}\", tags=[\"{module}\"])\n\n@router.get(\"/ping\")\nasync def ping():\n    return {{\"module\": \"{module}\", \"status\": \"ok\"}}\n""",
        encoding="utf-8",
    )


@app.command("add-module")
def add_module(
    name: str = typer.Argument(..., help="Module name (e.g., payments)"),
    path: Path = typer.Option(Path("."), "--path", help="Root of existing modular project"),
) -> None:
    """Add a vertical-slice module to an existing modular project (expects modular layout)."""
    app_root = path / "app"
    if not app_root.exists():
        typer.secho("Could not locate 'app' directory – are you in a project root?", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    substitutions = {"secret_key": _generate_secret()}
    _scaffold_module(app_root, name, substitutions)
    typer.secho(f"Module '{name}' added.", fg=typer.colors.GREEN)


@app.command("generate-crud")
def generate_crud(
    entity: str = typer.Argument(..., help="Entity name, e.g. 'Book'"),
    path: Path = typer.Option(Path("."), help="Root of layered project (or module if modular)"),
    modular: bool = typer.Option(False, help="Treat path as a module root inside a modular project"),
    full: bool = typer.Option(True, "--full/--minimal", help="Generate full CRUD (create,get,update,delete,list)"),
    sqlalchemy: bool = typer.Option(False, help="Also scaffold a SQLAlchemy repository template for the entity"),
    fields: str = typer.Option("name:str", help="Comma separated list of field definitions for create/update (e.g. 'name:str,price:float')"),
    async_mode: bool = typer.Option(False, "--async", help="Generate async handlers + service (in-memory only)"),
) -> None:
    """Generate a simple CRUD command/query/service + router skeleton for an entity.

    This is an early placeholder implementation demonstrating CQRS layout.
    """
    # Determine roots
    if modular:
        # Path should point to app/<module>
        app_root = path
        presentation_router_dir = app_root / "presentation" / "api" / "routers"
        application_dir = app_root / "application"
    else:
        app_root = path / "app"
        presentation_router_dir = app_root / "presentation" / "api" / "routers"
        application_dir = app_root / "application"

    entity_lower = entity.lower()
    entity_plural = entity_lower + "s"

    # Guard: async + sqlalchemy not yet supported (would require async ORM setup)
    if async_mode and sqlalchemy:
        typer.secho("--async with --sqlalchemy not yet supported; falling back to synchronous generation.", fg=typer.colors.YELLOW)
        async_mode = False

    # Ensure directories (and for modular ensure local cqrs mediator exists)
    (application_dir / entity_plural / "commands").mkdir(parents=True, exist_ok=True)
    (application_dir / entity_plural / "queries").mkdir(parents=True, exist_ok=True)
    (application_dir / entity_plural / "services").mkdir(parents=True, exist_ok=True)
    presentation_router_dir.mkdir(parents=True, exist_ok=True)
    if modular:
        common_dir = application_dir / "common"
        cqrs_file = common_dir / "cqrs.py"
        models_dir = common_dir / "models"
        result_model_file = models_dir / "result_model.py"
        if not models_dir.exists():
            models_dir.mkdir(parents=True)
        if not result_model_file.exists():
            result_model_file.write_text(
                """from __future__ import annotations\nfrom dataclasses import dataclass\nfrom typing import Generic, TypeVar, Optional\nT = TypeVar('T')\n@dataclass(slots=True)\nclass Result(Generic[T]):\n    success: bool\n    value: Optional[T] = None\n    error: Optional[str] = None\n    @classmethod\n    def ok(cls, value: T | None = None) -> 'Result[T]': return cls(True, value=value)\n    @classmethod\n    def fail(cls, error: str) -> 'Result[T]': return cls(False, error=error)\n""",
                encoding="utf-8",
            )
        if not cqrs_file.exists():
            cqrs_file.write_text(
                """from __future__ import annotations\nfrom typing import Any, Callable, Dict, Type, Protocol\nfrom .models.result_model import Result  # type: ignore[import-not-found]\nimport logging, inspect\nlogger = logging.getLogger('app.mediator')\nclass Command: ...\nclass Query: ...\nclass Behavior(Protocol):\n    def __call__(self, next_: Callable[[Any], Any], message: Any) -> Any: ...\nclass Mediator:\n    def __init__(self) -> None:\n        self._c: Dict[type, Callable] = {}\n        self._q: Dict[type, Callable] = {}\n        self._b: list[Behavior] = []\n    def register_command(self, t: Type, h: Callable) -> None: self._c[t] = h\n    def register_query(self, t: Type, h: Callable) -> None: self._q[t] = h\n    def add_behavior(self, b: Behavior) -> None: self._b.append(b)\n    def _invoke(self, msg: Any, handler: Callable[[Any], Any]) -> Any:\n        def chain(i: int, m: Any) -> Any:\n            if i == len(self._b): return handler(m)\n            return self._b[i](lambda mm: chain(i+1, mm), m)\n        try: return chain(0, msg)\n        except Exception as exc:  # pragma: no cover\n            logger.exception('Mediator error: %s', exc); return Result.fail(str(exc))\n    def send(self, c: Command) -> Result[Any]:\n        h = self._c.get(type(c))\n        if not h: return Result.fail(f'No handler for {type(c).__name__}')\n        r = self._invoke(c, h); return r if isinstance(r, Result) else Result.ok(r)\n    async def send_async(self, c: Command) -> Result[Any]:\n        h = self._c.get(type(c))\n        if not h: return Result.fail(f'No handler for {type(c).__name__}')\n        r = self._invoke(c, h)\n        if inspect.iscoroutine(r): r = await r\n        return r if isinstance(r, Result) else Result.ok(r)\n    def ask(self, q: Query) -> Result[Any]:\n        h = self._q.get(type(q))\n        if not h: return Result.fail(f'No handler for {type(q).__name__}')\n        r = self._invoke(q, h); return r if isinstance(r, Result) else Result.ok(r)\n    async def ask_async(self, q: Query) -> Result[Any]:\n        h = self._q.get(type(q))\n        if not h: return Result.fail(f'No handler for {type(q).__name__}')\n        r = self._invoke(q, h)\n        if inspect.iscoroutine(r): r = await r\n        return r if isinstance(r, Result) else Result.ok(r)\nmediator = Mediator()\ndef _log_behavior(next_, msg):\n    logger.debug('Handling %s', type(msg).__name__); res = next_(msg); logger.debug('Handled %s', type(msg).__name__); return res\nmediator.add_behavior(_log_behavior)\n""",
                encoding="utf-8",
            )
    # Relative import path (same for both currently; kept for future divergence)
    cqrs_rel = "...common.cqrs"

    # Parse fields
    def _parse_fields(spec: str) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for raw in spec.split(','):
            raw = raw.strip()
            if not raw:
                continue
            if ':' in raw:
                n, t = raw.split(':', 1)
            else:
                n, t = raw, 'str'
            n = n.strip()
            t = t.strip() or 'str'
            out.append((n, t))
        return out or [('name', 'str')]

    field_pairs = _parse_fields(fields)
    field_annotations = "\n    ".join(f"{n}: {t}" for n, t in field_pairs)
    create_model_fields = field_annotations
    update_model_fields = field_annotations

    # Base Commands + handler (register with mediator)
    create_handler = ("async def handle(command: Create{e}Command) -> Result[int]:\n    data = command.model_dump()\n    new_id = await SERVICE.create(**data)\n    return Result.ok(new_id)\n" if async_mode and not sqlalchemy else "def handle(command: Create{e}Command) -> Result[int]:\n    data = command.model_dump()\n    new_id = SERVICE.create(**data)\n    return Result.ok(new_id)\n").replace('{e}', entity)
    (application_dir / entity_plural / "commands" / f"create_{entity_lower}.py").write_text(f"from __future__ import annotations\nfrom pydantic import BaseModel\nfrom {cqrs_rel} import Command, mediator\nfrom ..services.{entity_lower}_service import SERVICE\nfrom ...common.models.result_model import Result\n\nclass Create{entity}Command(Command, BaseModel):\n    {create_model_fields}\n\n\n{create_handler}mediator.register_command(Create{entity}Command, handle)\n", encoding="utf-8")

    # Base Query + handler (register with mediator)
    get_handler = ("async def handle(query: Get{e}Query) -> Result[dict | None]:\n    item = await SERVICE.get(query.id)\n    if item is None:\n        return Result.fail('NOT_FOUND')\n    return Result.ok(item)\n" if async_mode and not sqlalchemy else "def handle(query: Get{e}Query) -> Result[dict | None]:\n    item = SERVICE.get(query.id)\n    if item is None:\n        return Result.fail('NOT_FOUND')\n    return Result.ok(item)\n").replace('{e}', entity)
    get_query_path = application_dir / entity_plural / "queries" / f"get_{entity_lower}.py"
    get_query_path.write_text(f"from __future__ import annotations\nfrom pydantic import BaseModel\nfrom {cqrs_rel} import Query, mediator\nfrom ..services.{entity_lower}_service import SERVICE\nfrom ...common.models.result_model import Result\n\nclass Get{entity}Query(Query, BaseModel):\n    id: int\n\n\n{get_handler}mediator.register_query(Get{entity}Query, handle)\n", encoding="utf-8")

    if full:
        update_handler = ("async def handle(command: Update{e}Command) -> Result[bool]:\n    data = command.model_dump(); _id = data.pop('id')\n    ok = await SERVICE.update(_id, **data)\n    return Result.ok(ok) if ok else Result.fail('NOT_FOUND')\n" if async_mode and not sqlalchemy else "def handle(command: Update{e}Command) -> Result[bool]:\n    data = command.model_dump(); _id = data.pop('id')\n    ok = SERVICE.update(_id, **data)\n    return Result.ok(ok) if ok else Result.fail('NOT_FOUND')\n").replace('{e}', entity)
        (application_dir / entity_plural / "commands" / f"update_{entity_lower}.py").write_text(f"from __future__ import annotations\nfrom pydantic import BaseModel\nfrom {cqrs_rel} import Command, mediator\nfrom ..services.{entity_lower}_service import SERVICE\nfrom ...common.models.result_model import Result\n\nclass Update{entity}Command(Command, BaseModel):\n    id: int\n    {update_model_fields}\n\n\n{update_handler}mediator.register_command(Update{entity}Command, handle)\n", encoding="utf-8")
        delete_handler = ("async def handle(command: Delete{e}Command) -> Result[bool]:\n    ok = await SERVICE.delete(command.id)\n    return Result.ok(True) if ok else Result.fail('NOT_FOUND')\n" if async_mode and not sqlalchemy else "def handle(command: Delete{e}Command) -> Result[bool]:\n    ok = SERVICE.delete(command.id)\n    return Result.ok(True) if ok else Result.fail('NOT_FOUND')\n").replace('{e}', entity)
        (application_dir / entity_plural / "commands" / f"delete_{entity_lower}.py").write_text(f"from __future__ import annotations\nfrom pydantic import BaseModel\nfrom {cqrs_rel} import Command, mediator\nfrom ..services.{entity_lower}_service import SERVICE\nfrom ...common.models.result_model import Result\n\nclass Delete{entity}Command(Command, BaseModel):\n    id: int\n\n\n{delete_handler}mediator.register_command(Delete{entity}Command, handle)\n", encoding="utf-8")
        list_handler = ("async def handle(query: List{e}Query) -> Result[list[tuple[int,str]]]:\n    return Result.ok(await SERVICE.list())\n" if async_mode and not sqlalchemy else "def handle(query: List{e}Query) -> Result[list[tuple[int,str]]]:\n    return Result.ok(SERVICE.list())\n").replace('{e}', entity)
        (application_dir / entity_plural / "queries" / f"list_{entity_plural}.py").write_text(f"from __future__ import annotations\nfrom {cqrs_rel} import Query, mediator\nfrom ..services.{entity_lower}_service import SERVICE\nfrom ...common.models.result_model import Result\n\nclass List{entity}Query(Query):\n    pass\n\n\n{list_handler}mediator.register_query(List{entity}Query, handle)\n", encoding="utf-8")
    # Service (in-memory or SQLAlchemy stub)
    if not (application_dir / entity_plural / "services").exists():
        (application_dir / entity_plural / "services").mkdir(parents=True)
    service_file = application_dir / entity_plural / "services" / f"{entity_lower}_service.py"
    if not service_file.exists():
        if sqlalchemy:
            service_file.write_text(
                f"""from __future__ import annotations\n\n# SQLAlchemy service for {entity} (placeholder – user to implement persistence logic)\nclass {entity}Service:\n    def __init__(self, repo=None):\n        self._repo = repo  # expected to conform to repository protocol\n\n    def create(self, **data):  # sync placeholder\n        # Integrate with repository / unit of work here\n        return 0\n\n    def get(self, _id: int):\n        return None\n\nSERVICE = {entity}Service()\n""",
                encoding="utf-8",
            )
        else:
            if async_mode:
                service_file.write_text(f"from __future__ import annotations\nfrom typing import Dict, Any, List, Tuple\n\nclass InMemory{entity}Service:  # simplistic async in-memory service\n    def __init__(self):\n        self._data: Dict[int, Dict[str, Any]] = {{}}\n        self._next_id = 1\n\n    async def create(self, **data) -> int:\n        _id = self._next_id; self._next_id += 1\n        self._data[_id] = {{'id': _id, **data}}\n        return _id\n\n    async def get(self, _id: int) -> Dict[str, Any] | None:\n        return self._data.get(_id)\n\n    async def update(self, _id: int, **data) -> bool:\n        if _id not in self._data: return False\n        self._data[_id].update(data)\n        return True\n\n    async def delete(self, _id: int) -> bool:\n        return self._data.pop(_id, None) is not None\n\n    async def list(self) -> List[Tuple[int, str]]:\n        return [(i, str(v.get('id'))) for i, v in self._data.items()]\n\nSERVICE = InMemory{entity}Service()\n", encoding="utf-8")
            else:
                service_file.write_text(f"from __future__ import annotations\nfrom typing import Dict, Any, List, Tuple\n\nclass InMemory{entity}Service:  # simplistic in-memory service\n    def __init__(self):\n        self._data: Dict[int, Dict[str, Any]] = {{}}\n        self._next_id = 1\n\n    def create(self, **data) -> int:\n        _id = self._next_id; self._next_id += 1\n        self._data[_id] = {{'id': _id, **data}}\n        return _id\n\n    def get(self, _id: int) -> Dict[str, Any] | None:\n        return self._data.get(_id)\n\n    def update(self, _id: int, **data) -> bool:\n        if _id not in self._data: return False\n        self._data[_id].update(data)\n        return True\n\n    def delete(self, _id: int) -> bool:\n        return self._data.pop(_id, None) is not None\n\n    def list(self) -> List[Tuple[int, str]]:\n        return [(i, str(v.get('id'))) for i, v in self._data.items()]\n\nSERVICE = InMemory{entity}Service()\n", encoding="utf-8")

    # Optional SQLAlchemy repository skeleton
    if sqlalchemy:
        if modular:
            infra_repo_dir = app_root / "infrastructure" / "repositories"
            domain_entities_dir = app_root / "domain" / "entities"
        else:
            infra_repo_dir = app_root / "infrastructure" / "repositories"
            domain_entities_dir = app_root / "domain" / "entities"
        infra_repo_dir.mkdir(parents=True, exist_ok=True)
        domain_entities_dir.mkdir(parents=True, exist_ok=True)
        # Ensure ORM base & models package
        db_models_dir = app_root / "infrastructure" / "db" / "models"
        db_models_dir.mkdir(parents=True, exist_ok=True)
        base_file = app_root / "infrastructure" / "db" / "base.py"
        if not base_file.exists():
            base_file.write_text(
                """from __future__ import annotations\ntry:  # pragma: no cover - optional dependency path\n    from sqlalchemy.orm import DeclarativeBase
except Exception:  # noqa: BLE001
    class DeclarativeBase:  # type: ignore
        pass
class Base(DeclarativeBase):
    pass
""",
                encoding="utf-8",
            )
        domain_entity_file = domain_entities_dir / f"{entity_lower}.py"
        if not domain_entity_file.exists():
            domain_entity_file.write_text(
                f"""from __future__ import annotations\nfrom dataclasses import dataclass\n\n@dataclass(slots=True)\nclass {entity}:\n    id: int\n    name: str\n""",
                encoding="utf-8",
            )
        orm_model_file = db_models_dir / f"{entity_lower}.py"
        if not orm_model_file.exists():
            orm_model_file.write_text(
                f"""from __future__ import annotations\nfrom sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base  # type: ignore[import-not-found]\n\nclass {entity}Model(Base):  # type: ignore[misc]
    __tablename__ = '{entity_plural}'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
""",
                encoding="utf-8",
            )
        repo_file = infra_repo_dir / f"{entity_lower}_repository.py"
        if not repo_file.exists():
            repo_file.write_text(
                f"""from __future__ import annotations\nfrom typing import Protocol, runtime_checkable, Optional, List, Iterable\ntry:  # pragma: no cover - optional dependency path\n    from sqlalchemy.orm import Session\nexcept Exception:  # noqa: BLE001\n    Session = object  # type: ignore\n\nfrom app.domain.entities.{entity_lower} import {entity}  # type: ignore[import-not-found]\n\n@runtime_checkable\nclass {entity}RepositoryProtocol(Protocol):  # noqa: D401
    def add(self, name: str) -> int: ...\n    def get(self, _id: int) -> Optional[{entity}]: ...\n    def list(self) -> List[{entity}]: ...\n    def delete(self, _id: int) -> bool: ...\n\nclass InMemory{entity}Repository({entity}RepositoryProtocol):\n    def __init__(self) -> None:\n        self._data: dict[int, {entity}] = {{}}\n        self._next_id = 1\n    def add(self, name: str) -> int:\n        _id = self._next_id; self._data[_id] = {entity}(id=_id, name=name); self._next_id += 1; return _id\n    def get(self, _id: int) -> Optional[{entity}]: return self._data.get(_id)\n    def list(self) -> List[{entity}]: return list(self._data.values())\n    def delete(self, _id: int) -> bool: return self._data.pop(_id, None) is not None\n\n# Placeholder SQLAlchemy repository implementation skeleton\nclass SQLAlchemy{entity}Repository({entity}RepositoryProtocol):  # pragma: no cover - template\n    def __init__(self, session_factory):\n        self._session_factory = session_factory\n    def add(self, name: str) -> int:  # TODO: implement ORM persistence\n        with self._session_factory() as session:  # type: ignore[attr-defined]\n            return 0\n    def get(self, _id: int) -> Optional[{entity}]:\n        with self._session_factory() as session:  # type: ignore[attr-defined]\n            return None\n    def list(self) -> List[{entity}]:\n        with self._session_factory() as session:  # type: ignore[attr-defined]\n            return []\n    def delete(self, _id: int) -> bool:\n        with self._session_factory() as session:  # type: ignore[attr-defined]\n            return False\n""",
                encoding="utf-8",
            )

    # Router
    # Maintain original naming convention (<entity>.py) so __init__ updater works
    router_file = presentation_router_dir / f"{entity_lower}.py"
    if not router_file.exists():
        if async_mode and not sqlalchemy:
            router_file.write_text(f"from fastapi import APIRouter, Depends\nfrom ..application.{entity_plural}.commands.create_{entity_lower} import Create{entity}Command\nfrom ..application.{entity_plural}.queries.get_{entity_lower} import Get{entity}Query\nfrom ..application.common.cqrs import mediator as _m\nfrom ..application.common.models.result_adapter import adapter\nfrom pydantic import BaseModel\n\nrouter = APIRouter(prefix='/{entity_plural}', tags=['{entity_plural}'])\n\nclass Create{entity}DTO(BaseModel):\n    {create_model_fields}\n\n@router.post('/')\nasync def create_{entity_lower}(dto: Create{entity}DTO):\n    cmd = Create{entity}Command(**dto.model_dump())\n    res = await _m.send_async(cmd)\n    return adapter(res)\n\n@router.get('/{id}')\nasync def get_{entity_lower}(id: int):\n    res = await _m.ask_async(Get{entity}Query(id=id))\n    return adapter(res)\n", encoding="utf-8")
        else:
            router_file.write_text(f"from fastapi import APIRouter, Depends\nfrom ..application.{entity_plural}.commands.create_{entity_lower} import Create{entity}Command\nfrom ..application.{entity_plural}.queries.get_{entity_lower} import Get{entity}Query\nfrom ..application.common.cqrs import mediator as _m\nfrom ..application.common.models.result_adapter import adapter\nfrom pydantic import BaseModel\n\nrouter = APIRouter(prefix='/{entity_plural}', tags=['{entity_plural}'])\n\nclass Create{entity}DTO(BaseModel):\n    {create_model_fields}\n\n@router.post('/')\ndef create_{entity_lower}(dto: Create{entity}DTO):\n    cmd = Create{entity}Command(**dto.model_dump())\n    res = _m.send(cmd)\n    return adapter(res)\n\n@router.get('/{id}')\ndef get_{entity_lower}(id: int):\n    res = _m.ask(Get{entity}Query(id=id))\n    return adapter(res)\n", encoding="utf-8")

    # Update routers __init__ (layered only) to include new router automatically
    if not modular:
        routers_init = presentation_router_dir / "__init__.py"
        if routers_init.exists():
            text = routers_init.read_text(encoding="utf-8")
            import_line = f"from .{entity_lower} import router as {entity_lower}"  # noqa: E501
            if import_line not in text:
                # Insert before all_routers definition if present; else append
                if "all_routers" in text:
                    lines = text.splitlines()
                    for idx, line in enumerate(lines):
                        if line.strip().startswith("all_routers"):
                            lines.insert(idx, import_line)
                            break
                    else:  # pragma: no cover
                        lines.append(import_line)
                    # Update list
                    for idx, line in enumerate(lines):
                        if line.strip().startswith("all_routers") and "[" in line:
                            # naive append inside list representation
                            if line.rstrip().endswith("]"):
                                if line.strip().endswith("]"):
                                    if "]" in line:
                                        lines[idx] = line.replace("]", f", {entity_lower}]")
                            break
                    text = "\n".join(lines) + "\n"
                else:
                    if not text.endswith("\n"):
                        text += "\n"
                    text += f"\n{import_line}\nall_routers.append({entity_lower})\n"
                routers_init.write_text(text, encoding="utf-8")

    typer.secho(f"CRUD skeleton for entity '{entity}' generated.", fg=typer.colors.GREEN)


@app.command("list-routers")
def list_routers(path: Path = typer.Option(Path("."), help="Project root")) -> None:
    """List router python files in a layered project."""
    routers_dir = path / "app" / "presentation" / "api" / "routers"
    if not routers_dir.exists():
        typer.secho("Routers directory not found", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    files = sorted(p.name for p in routers_dir.glob("*.py") if p.name != "__init__.py")
    for f in files:
        typer.echo(f)


@app.command("make-plugin")
def make_plugin(name: str, path: Path = typer.Option(Path("."), help="Root where to place plugins directory")) -> None:
    """Create a plugin stub file under ./plugins."""
    plugins_dir = path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    plugin_file = plugins_dir / f"{name}.py"
    if plugin_file.exists():
        typer.secho("Plugin already exists", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    plugin_file.write_text(
        f"""from __future__ import annotations\nimport typer\n\n# Auto-generated plugin stub\n\ndef register(app: typer.Typer) -> None:\n    @app.command('{name}-hello')\n    def _plugin_cmd():\n        \"\"\"Example plugin command.\n        Extend or remove in real usage.\n        \"\"\"\n        typer.echo('Hello from plugin {name}!')\n""",
        encoding="utf-8",
    )
    typer.secho(f"Plugin '{name}' created.", fg=typer.colors.GREEN)


if __name__ == "__main__":  # pragma: no cover
    app()
