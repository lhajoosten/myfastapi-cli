from __future__ import annotations

from pathlib import Path
import tempfile
import sys
import importlib.util

import json
from typing import Any

from typer.testing import CliRunner

from src.cli import app


def _import_generated_app(project_path: Path):
    sys.path.insert(0, str(project_path))
    try:
        spec = importlib.util.spec_from_file_location("generated_main", project_path / "app" / "main.py")
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        assert spec and spec.loader
        spec.loader.exec_module(module)  # type: ignore[assignment]
        return module.app
    finally:
        if str(project_path) in sys.path:
            sys.path.remove(str(project_path))


runner = CliRunner()


def test_new_layered_project():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "sample"
        result = runner.invoke(app, ["new", str(proj)])
        assert result.exit_code == 0, result.output
        assert (proj / "app" / "main.py").exists()
        assert (proj / "app" / "presentation" / "api" / "routers" / "auth.py").exists()


def test_new_modular_project_with_modules():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "sample_mod"
        result = runner.invoke(app, ["new", str(proj), "--modular", "--modules", "auth,inventory"])
        assert result.exit_code == 0, result.output
        assert (proj / "app" / "auth").exists()
        assert (proj / "app" / "inventory").exists()


def test_generate_crud_layered():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "sample"
        result_new = runner.invoke(app, ["new", str(proj)])
        assert result_new.exit_code == 0, result_new.output
    result = runner.invoke(app, ["generate-crud", "Book", "--path", str(proj), "--full"])  # ensure full for tests
    assert result.exit_code == 0, result.output
    service_file = proj / "app" / "application" / "books" / "services" / "book_service.py"
    assert service_file.exists(), list((proj / "app" / "application").rglob("*"))
    assert (proj / "app" / "application" / "books" / "commands" / "create_book.py").exists()
    assert (proj / "app" / "application" / "books" / "queries" / "get_book.py").exists()
    # Extended CRUD files
    assert (proj / "app" / "application" / "books" / "commands" / "update_book.py").exists()
    assert (proj / "app" / "application" / "books" / "commands" / "delete_book.py").exists()
    assert (proj / "app" / "application" / "books" / "queries" / "list_books.py").exists()
    assert (proj / "app" / "presentation" / "api" / "routers" / "book.py").exists()


def test_layered_auth_endpoints_smoke():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "app_proj"
        runner.invoke(app, ["new", str(proj)])
        generated_app = _import_generated_app(proj)
        from fastapi.testclient import TestClient  # inline import to keep dependency local

        client = TestClient(generated_app)
        r = client.post("/auth/register", json={"username": "alice", "password": "pass"})
        assert r.status_code == 201, r.text
        r2 = client.post("/auth/login", json={"username": "alice", "password": "pass"})
        assert r2.status_code == 200, r2.text
        token = r2.json()["access_token"]
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["username"] == "alice"
        # Admin route should be forbidden for normal user
        admin_resp = client.get("/auth/admin/ping", headers={"Authorization": f"Bearer {token}"})
        assert admin_resp.status_code == 403

        # Promote user to admin role and test success
        from app.core.di import get_user_repository as _gur  # type: ignore
        repo = _gur()
        u = repo.get_by_username("alice")
        if u and "admin" not in u.roles:
            u.roles.append("admin")
        # Re-login to get token with admin in claims
        r3 = client.post("/auth/login", json={"username": "alice", "password": "pass"})
        assert r3.status_code == 200
        admin_token = r3.json()["access_token"]
        admin_ok = client.get("/auth/admin/ping", headers={"Authorization": f"Bearer {admin_token}"})
        assert admin_ok.status_code == 200, admin_ok.text


def test_generate_crud_sqlalchemy_layered():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "sample"
        result_new = runner.invoke(app, ["new", str(proj)])
        assert result_new.exit_code == 0, result_new.output
        result = runner.invoke(app, ["generate-crud", "Order", "--path", str(proj), "--sqlalchemy", "--minimal"])
        assert result.exit_code == 0, result.output
        assert (proj / "app" / "domain" / "entities" / "order.py").exists()
        assert (proj / "app" / "infrastructure" / "repositories" / "order_repository.py").exists()
        assert (proj / "app" / "infrastructure" / "db" / "models" / "order.py").exists()
        svc = proj / "app" / "application" / "orders" / "services" / "order_service.py"
        assert svc.exists()
        assert "SQLAlchemy service for Order" in svc.read_text(encoding="utf-8")


def test_modular_crud_generation():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "mod_proj"
        runner.invoke(app, ["new", str(proj), "--modular", "--modules", "auth"])
        mod_root = proj / "app" / "auth"
        result = runner.invoke(app, ["generate-crud", "Item", "--path", str(mod_root), "--modular"])
        assert result.exit_code == 0
        assert (mod_root / "application" / "items" / "services" / "item_service.py").exists()
        # Ensure modular CQRS created
        assert (mod_root / "application" / "common" / "cqrs.py").exists()


def test_make_plugin_and_list_routers():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "sample"
        runner.invoke(app, ["new", str(proj)])
        # Generate CRUD to add router
        runner.invoke(app, ["generate-crud", "Thing", "--path", str(proj)])
        # List routers
        lr = runner.invoke(app, ["list-routers", "--path", str(proj)])
        assert lr.exit_code == 0
        assert "thing.py" in lr.output.lower()
        # Make plugin
        mp = runner.invoke(app, ["make-plugin", "sampleplug", "--path", str(proj)])
        assert mp.exit_code == 0
        assert (proj / "plugins" / "sampleplug.py").exists()
