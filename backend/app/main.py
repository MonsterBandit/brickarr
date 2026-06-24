from __future__ import annotations

import logging
import logging.handlers
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import ensure_initial_api_key
from app.config import settings
from app.crypto import get_fernet
from app.db import SessionLocal
from app.routers import (
    activity,
    auth_routes,
    collection,
    health,
    instructions,
    parts_top,
    sets as sets_router,
    settings_routes,
    system as system_router,
)

log = logging.getLogger("brickarr")


def _configure_logging() -> None:
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)
    fh = logging.handlers.RotatingFileHandler(
        settings.logs_dir / "brickarr.log", maxBytes=5_000_000, backupCount=5
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    _configure_logging()
    get_fernet()
    db = SessionLocal()
    try:
        try:
            ensure_initial_api_key(db)
        except Exception:  # noqa: BLE001
            log.exception("Initial API key bootstrap failed")
    finally:
        db.close()
    yield


app = FastAPI(
    title="Brickarr",
    version="0.1.0-alpha.1",
    default_response_class=JSONResponse,
    lifespan=lifespan,
)


# Mount routers in /api/v1 with response_model_by_alias defaulted to True per-route via APIRoute kwarg.
def _mount(prefix: str = settings.api_v1_prefix) -> None:
    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(auth_routes.router, prefix=prefix, tags=["auth"])
    app.include_router(sets_router.router, prefix=prefix, tags=["sets"])
    app.include_router(instructions.router, prefix=prefix, tags=["instructions"])
    app.include_router(parts_top.router, prefix=prefix, tags=["parts"])
    app.include_router(collection.router, prefix=prefix, tags=["collection"])
    app.include_router(activity.router, prefix=prefix, tags=["activity"])
    app.include_router(system_router.router, prefix=prefix, tags=["system"])
    app.include_router(settings_routes.router, prefix=prefix, tags=["settings"])


_mount()


# Force response_model_by_alias on every API route so camelCase is emitted.
for r in app.router.routes:
    if hasattr(r, "response_model_by_alias"):
        r.response_model_by_alias = True


@app.exception_handler(StarletteHTTPException)
async def _http_exception(_req: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, (dict, list)):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPError", "message": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception(_req: Request, exc: RequestValidationError):
    errors = []
    for e in exc.errors():
        loc = ".".join(str(x) for x in e.get("loc", []) if x != "body")
        errors.append({"propertyName": loc or "body", "errorMessage": e.get("msg", "Invalid")})
    return JSONResponse(status_code=400, content=errors)


_STATIC_DIR = Path(__file__).parent / "static"
_INDEX_FILE = _STATIC_DIR / "index.html"


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path, scope):  # noqa: D401
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and _INDEX_FILE.exists():
                return FileResponse(_INDEX_FILE)
            raise


if _STATIC_DIR.is_dir():
    app.mount("/", SPAStaticFiles(directory=str(_STATIC_DIR), html=True), name="spa")
else:
    log.warning("Static directory %s missing; SPA mount skipped", _STATIC_DIR)
