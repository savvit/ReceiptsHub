from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.auth.router import router as auth_router
from src.checks.router import router as checks_router
from src.database import Base, async_engine


async def init_models():
    """
    Initialize database models by creating all tables defined in Base metadata.
    Connects to the database using the asynchronous engine and executes schema creation.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for FastAPI application lifespan.
    Performs initialization tasks, such as setting up database models,
    and ensures proper cleanup if required in the future.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    await init_models()
    yield


def create_app() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.

    This function defines the application's lifespan, includes all necessary routers,
    and returns a ready-to-use FastAPI instance.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """

    app = FastAPI(lifespan=lifespan)
    app.include_router(auth_router)
    app.include_router(checks_router)
    return app


app = create_app()
