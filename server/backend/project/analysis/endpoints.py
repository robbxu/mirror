from uuid import uuid4
from fastapi import APIRouter, Request, Depends
from project.knowledge.models import Category
from project.database import get_db_sess
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from celery.result import AsyncResult

from project.embedding.voyage import voyage_embedding


analysis_router = APIRouter(
    prefix="/analysis",
)
# ------------------------------------------------------------------------------
# INTERACTION ENDPOINTS ********************************************************
# ------------------------------------------------------------------------------
@analysis_router.get("/task/{id}")
async def status(id: str, request: Request):
    app = request.app
    task_result = AsyncResult(id, app=app.celery_app)
    return {
        "task_id": id,
        "task_status": task_result.state,
        "task_result": task_result.result if task_result.state == 'SUCCESS' else None 
    }

@analysis_router.post("/initialize")
async def intialize(request: Request, session: AsyncSession = Depends(get_db_sess)):
    rows = (await session.execute(
        select(Category.id)
    )).all()

    categories = ["Spirituality", 
                  "Health", 
                  "Politics", 
                  "Relationships", 
                  "Hobbies", 
                  "Career", 
                  "Education",
                ]
    embeddings = voyage_embedding(categories, False, single=False)

    inserts = []
    for i in range(len(categories)):
        inserts.append({"name": categories[i], "embedding": embeddings[i]})
    
    result = {"data": "Database already initialized"}
    if len(rows) == 0:
        await session.execute(insert(Category), inserts)
        await session.commit()
        result = {"data": "Database initialized"}
    return result