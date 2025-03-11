from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException, Response, status

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from project.database import get_db_sess

from project.knowledge.models import Topic, TopicBelief, Belief
from project.embedding.voyage import voyage_embedding

knowledge_router = APIRouter(
    prefix="/knowledge",
)

@knowledge_router.post("/belief/update")
async def update_beliefs(request: Request, session: AsyncSession = Depends(get_db_sess)):
    data = await request.json() 
    embedding = voyage_embedding(data["text"], query=False)

    try:
        await session.execute(
            update(Belief)
            .where(Belief.id == data["id"])
            .values(text=data["text"], embedding=embedding, type=None)
        )
        await session.commit()
        return {"id": data["id"]}
    except:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Database encountered error'
        )
    
@knowledge_router.get("/topic/all")
async def get_topics(session: AsyncSession = Depends(get_db_sess)):
    topics = (await session.execute(
        select(Topic.id, Topic.name)
    )).all()

    result = []
    for row in topics:
        result.append({"id": row[0], "topic": row[1]})
    return {"topics": result}

@knowledge_router.get("/belief/all")
async def get_my_beliefs(session: AsyncSession = Depends(get_db_sess)):
    beliefs = (await session.execute(
        select(TopicBelief.belief_id, Belief.text, Belief.type,Topic.name)
        .join_from(TopicBelief, Belief, TopicBelief.belief_id == Belief.id)
        .join_from(TopicBelief, Topic, TopicBelief.topic_id == Topic.id)
    )).all()

    result = {}
    for row in beliefs:
        topic = row[3]
        if topic not in result:
            result[topic] = []
        result[topic].append({"id": row[0], "belief": row[1], "type": row[2]})
    return {"beliefs": result}

@knowledge_router.get("/belief/{id}")
async def get_beliefs(id: str, session: AsyncSession = Depends(get_db_sess)):
    res = (await session.scalars(
        select(Belief)
        .where(Belief.id == id)
    )).first()
    
    result = {
        "id": res.id,
        "text": res.text,
        "type": res.type,
    }
    return result
