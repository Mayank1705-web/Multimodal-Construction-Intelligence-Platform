from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import get_settings
from .errors import AppError
from .routes import router

log = logging.getLogger("construction")
settings = get_settings()

app = FastAPI(title="Multimodal Construction Intelligence Platform", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_methods=["*"], allow_headers=["*"])


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"status": "error", "error": {"code": code, "message": message}})


@app.exception_handler(AppError)
async def app_error(_: Request, exc: AppError) -> JSONResponse:
    return _error(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    where = ".".join(str(p) for p in first.get("loc", []) if p not in ("body", "query"))
    return _error(422, "invalid_request", f"{where or 'Request'}: {first.get('msg', 'invalid value')}")


@app.exception_handler(StarletteHTTPException)
async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(Exception)
async def unexpected(_: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error", exc_info=exc)
    return _error(500, "internal_error", "Something went wrong on the server. Please try again.")


app.include_router(router)

# Serve the built frontend when present so one process can host the whole demo.
dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
