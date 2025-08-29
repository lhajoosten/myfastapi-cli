# Plugin System

A lightweight plugin loader hook exists under `src/plugins/__init__.py` allowing dynamic registration of additional CLI commands.

## Concept

- Drop a `<name>.py` file into a `plugins/` directory at runtime.
- Provide a `register(app: typer.Typer)` function.
- The CLI will import and execute `register` to attach commands.

## Example Stub

```python
# plugins/sample.py
from __future__ import annotations
import typer

def register(app: typer.Typer) -> None:
    @app.command("sample-hello")
    def sample_hello():
        """Say hello from the sample plugin."""
        typer.echo("Hello from plugin")
```

## Helper Command

Generate a stub plugin file:

```bash
myfastapi make-plugin sampleplug
```

This creates `plugins/sampleplug.py` with a sample command you can adapt.
