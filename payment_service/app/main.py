from __future__ import annotations

from fastapi import FastAPI

from .db import init_db
from .routes import router

app = FastAPI(title="Payment Service")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "payment_service ok"}
