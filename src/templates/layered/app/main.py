from __future__ import annotations

from fastapi import FastAPI

from app.presentation.api.routers import all_routers

app = FastAPI(title="{{project_name}}")

for r in all_routers:
    app.include_router(r)


@app.get("/health", tags=["system"])  # simple health endpoint
async def health() -> dict[str, str]:
    return {"status": "ok"}
