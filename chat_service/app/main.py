from __future__ import annotations

import logging

from fastapi import FastAPI

from .routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Chat Service")
app.include_router(router)


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "chat_service ok"}
