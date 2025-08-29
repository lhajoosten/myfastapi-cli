"""Plugin system scaffold.

Place additional Python modules under this package that expose a
`register(app: typer.Typer)` function to dynamically add CLI commands.
They will be discovered automatically when the CLI starts.
"""
from __future__ import annotations

import importlib
import pkgutil
import typer


def load_plugins(app: typer.Typer, namespace: str = __name__) -> None:
    """Discover plugin submodules providing a register() hook.

    Best-effort import: failures in optional plugins are ignored so the
    core CLI remains functional.
    """
    for modinfo in pkgutil.iter_modules(__path__, prefix=f"{namespace}."):  # type: ignore[name-defined]
        try:  # pragma: no cover - defensive path
            module = importlib.import_module(modinfo.name)
        except Exception:  # noqa: BLE001 - ignore any plugin import issue
            continue
        register = getattr(module, "register", None)
        if callable(register):  # pragma: no branch - trivial
            try:
                register(app)
            except Exception:  # noqa: BLE001 - ignore plugin registration errors
                continue
