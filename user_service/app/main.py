from __future__ import annotations

from fastapi import FastAPI

from .db import init_db
from .routes import router

app = FastAPI(title="User Service")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
