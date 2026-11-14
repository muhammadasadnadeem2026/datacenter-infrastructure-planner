from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import calculate, constants, exports, projects
from app.api.rate_limit import RateLimitMiddleware
from app.config import get_settings
from app.version import APP_NAME, CALC_ENGINE_VERSION


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=f"{APP_NAME} API",
        version=CALC_ENGINE_VERSION,
        description=(
            "Data center power, cooling, electrical infrastructure and capacity planning engine. "
            "Every result carries its formula, substituted calculation, units, assumptions and references."
        ),
    )
    app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    for r in (calculate.router, constants.router, constants.meta_router, projects.router, exports.router):
        app.include_router(r)
    return app


app = create_app()
