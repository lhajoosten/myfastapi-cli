from __future__ import annotations

from fastapi import FastAPI
import importlib
from pathlib import Path
import pkgutil

app = FastAPI(title="{{project_name}} (modular)")


def _discover_and_include_routers() -> None:
    base = Path(__file__).parent
    for pkg in base.iterdir():
        if not pkg.is_dir() or pkg.name in {"__pycache__", "core"}:
            continue
        routers_pkg = f"app.{pkg.name}.presentation.api.routers"
        try:
            module = importlib.import_module(routers_pkg)
        except ImportError:  # pragma: no cover - best effort
            continue
        # Iterate submodules in routers package for APIRouter instances named 'router'
        module_file = getattr(module, "__file__", None)
        if not module_file:  # pragma: no cover - defensive
            continue
        package_path = Path(module_file).parent
        for info in pkgutil.iter_modules([str(package_path)]):
            sub_mod_name = f"{routers_pkg}.{info.name}"
            try:
                sub_mod = importlib.import_module(sub_mod_name)
            except ImportError:  # pragma: no cover
                continue
            router = getattr(sub_mod, "router", None)
            if router is not None:
                app.include_router(router)


_discover_and_include_routers()


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
