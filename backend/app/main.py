from fastapi import FastAPI
import asyncpg
from app.db import engine, Base
from app.routers import review, auth
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.middleware.rate_limit import limiter


allow_origins = settings.allowed_origins

async def ensure_database_exists():
    db_url = settings.database_url.replace("postgresql+asyncpg://", "")
    creds, rest = db_url.split("@")
    host_port, db_name = rest.rsplit("/", 1)
    user, password = creds.split(":")
    host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")

    conn = await asyncpg.connect(
        host=host, port=int(port),
        user=user, password=password,
        database="postgres"
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"[startup] Database '{db_name}' created.")
        else:
            print(f"[startup] Database '{db_name}' already exists.")
    finally:
        await conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_database_exists()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title='PR Review API',
    description='An API that takes a GitHub PR URL or a raw diff, runs a structured AI review, and outputs a scored report',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(review.router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
def root():
    return {"message": "Welcome to the PR Review API!"}