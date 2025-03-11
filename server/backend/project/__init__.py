from celery import Celery
from celery.schedules import crontab
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from project.celery_utils import create_celery
from project.websockets import asgi, manager
from project.database import manage_conn_pools
from project.config import settings


# https://testdriven.io/blog/fastapi-and-celery/
def create_app() -> FastAPI:
    app = FastAPI(lifespan=manage_conn_pools)
    # do this before loading routes
    app.celery_app = create_celery()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # can alter with time
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from project.interact.endpoints import interact_router
    from project.knowledge.endpoints import knowledge_router
    from project.analysis.endpoints import analysis_router

    version_router = APIRouter(prefix="/api/v1")
    version_router.include_router(interact_router)
    version_router.include_router(knowledge_router)
    version_router.include_router(analysis_router)
    app.include_router(version_router)

    # Define root behavior so can verify externally if api is up
    @app.get("/")
    async def root():
        return {"Connected": "API access to Mirror."}
    
    # Return fully configured app
    return app
