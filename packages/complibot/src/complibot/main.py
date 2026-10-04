from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from complibot.config import get_settings
from complibot.db.base import Base
from complibot.db.session import engine
from complibot.exceptions import AppError
from complibot.routers import auth, projects, reviews
from complibot.ws.review_socket import router as ws_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from pathlib import Path

    url = get_settings().database_url
    if url.startswith("sqlite"):
        Path(".data").mkdir(exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Compliance Review Copilot", version="0.1.0", lifespan=lifespan)
settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={"type": f"https://complibot.dev/errors/{exc.code}", "title": exc.code, "detail": exc.message},
    )


app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(reviews.router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
