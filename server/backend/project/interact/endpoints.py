import random
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException, Response, status, UploadFile, File

from sqlalchemy import update, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from celery import chain

from project.database import get_db_sess

from project.interact.models import Memory, Interaction, Exchange
from project.interact.utils import load_history, extract_context, record_exchange, validate_file_extension
from project.knowledge.utils import get_topics, extract_knowledge, format_knowledge
from project.embedding.voyage import voyage_embedding
from project.prompt.claude import claude_call, claude_belief_prompt, claude_style_prompt
from project.analysis import tasks

from opentelemetry import trace
from opentelemetry.propagate import inject, extract
from opentelemetry.trace import Status, StatusCode

interact_router = APIRouter(
    prefix="/interact",
)
# ------------------------------------------------------------------------------
# INTERACTION ENDPOINTS ********************************************************
# ------------------------------------------------------------------------------
@interact_router.post("/message")
async def message_self(request: Request, session: AsyncSession = Depends(get_db_sess)):
    data = await request.json()

    res = (await session.execute(
        select(Exchange.id, Exchange.text)
        .where(Exchange.interaction_id == data["id"])
        .order_by(Exchange.created_time.asc())
    )).all()

    history = load_history(res)
    message = data["message"].strip()
    history.append({"role": "user", "content": message} )
    context = extract_context(history, 1000)
    
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("interact_message", openinference_span_kind="chain") as span:
        span.set_input({"prompt": data})
        with tracer.start_as_current_span("get_knowledge", openinference_span_kind="retriever") as retrieve_span:
            retrieve_span.set_input({"context": context})
            context_embedding = voyage_embedding([context], query=False)
            topic_ids = await get_topics(context_embedding, session)
            knowledge_dict = await extract_knowledge(context_embedding, topic_ids, session)
            knowledge = format_knowledge(knowledge_dict)

            for topic in knowledge_dict:
                for i in range(len(knowledge_dict[topic]["beliefs"])):
                    retrieve_span.set_attribute(f"retrieval.documents.{i}.document.content", "\n\n".join(knowledge_dict[topic]["beliefs"][i]["memories"]))
                    retrieve_span.set_attribute(f"retrieval.documents.{i}.document.id", knowledge_dict[topic]["beliefs"][i]["belief"])
            retrieve_span.set_status(StatusCode.OK)
            
        with tracer.start_as_current_span("gen_beliefs", openinference_span_kind="llm") as belief_span:
            belief_span.set_input({"knowledge": knowledge})
            belief_prompt = claude_belief_prompt(knowledge, history)
            generation = claude_call(belief_prompt)
            belief_span.set_output({"result": str(generation)})

        with tracer.start_as_current_span("gen_styles", openinference_span_kind="llm") as style_span:
            style_span.set_input({"beliefs": generation})
            rows = (await session.execute(
                select(Memory.text)
            )).all()
            memories = [row[0] for row in rows]
            sample = random.sample(memories, 1)
            outline = {
                "message": generation,
                "writing_samples": sample
            }
            outline = claude_style_prompt(outline)
            generation = claude_call(outline)
            style_span.set_output({"result": str(generation)})
    
        span.set_output({"result": str(generation)})
        span.set_status(StatusCode.OK)
    await record_exchange(message, generation, data["id"], session)
    return {"response": generation}

@interact_router.post("/create")
async def interact(session: AsyncSession = Depends(get_db_sess)):
    id = uuid4()
    to_add = Interaction(id=str(id))
    session.add(to_add)
    await session.commit()
    
    return {"interaction_id": str(id)}


@interact_router.get("/interaction/all")
async def get_interactions(session: AsyncSession = Depends(get_db_sess)):
    ids = (await session.execute(
        select(Interaction.id)
        .order_by(Interaction.created_time.desc())
    )).all()
    
    result = []
    for row in ids:
        result.append(row[0])
    return {"interaction_ids": result}

@interact_router.get("/interaction/{id}")
async def get_interactions(id: str, session: AsyncSession = Depends(get_db_sess)):
    res = (await session.scalars(
        select(Interaction)
        .where(Interaction.id == id)
    )).first()
   
    result = {
        "id": res.id,
        "personality": res.personality,
        "personality_confidence": res.personality_confidence,
        "mood_baseline": res.mood_baseline,
        "comm_style": res.comm_style,
        "behavior": res.behavior
    }
    return result

# ------------------------------------------------------------------------------
# MEMORY ENDPOINTS ********************************************************
# ------------------------------------------------------------------------------

@interact_router.post("/memory/update")
async def update_memory(request: Request, session: AsyncSession = Depends(get_db_sess)):
    data = await request.json() 
    embedding = voyage_embedding([data["text"]], query=False)

    try:
        await session.execute(
            update(Memory)
            .where(Memory.id == data["id"])
            .values(text=data["text"], summary=data["summmary"],
                    embedding=embedding)
        )
        await session.commit()
        return {"id": data["id"]}
    except:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Database encountered error'
        )


@interact_router.get("/memory/all")
async def get_my_memories(session: AsyncSession = Depends(get_db_sess)):
    ids = (await session.execute(
        select(Memory.id)
        .order_by(Memory.created_time.desc())
    )).all()
    
    result = []
    for row in ids:
        result.append(row[0])
    return {"memory_ids": result}

@interact_router.get("/interaction/{id}/memories")
async def get_int_memories(id: str, session: AsyncSession = Depends(get_db_sess)):
    ids = (await session.execute(
        select(Memory.id)
        .where(Interaction.id == id)
        .order_by(Memory.created_time.desc())
    )).all()
    
    result = []
    for row in ids:
        result.append(row[0])
    return {"memory_ids": result}


@interact_router.get("/memory/{id}")
async def get_memories(id: str, session: AsyncSession = Depends(get_db_sess)):
    res = (await session.scalars(
        select(Memory)
        .where(Memory.id == id,)
    )).first()
    
    result = {
        "id": res.id,
        "text": res.text,
        "impact": res.impact
    }
    return result


@interact_router.post("/upload")
async def upload_memories(file: UploadFile = File(...)) -> dict:    
    ALLOWED_EXTENSIONS = { 
        '.txt',  # Text files
        '.docx',  # Microsoft Word (new)
        '.odt',  # OpenDocument
    }
    # Validate file type
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("UPLOAD") as span:
        span.set_input({"filename": file.filename, "content_size": len(content)})
        headers = {}
        inject(headers)
        # celery task
        pipe = chain(tasks.gen_file_memories.s(content, file.filename), 
                    tasks.gen_new_knowledge.s(headers=headers),
                    tasks.cluster_memories.s()).apply_async()
        span.set_status(StatusCode.OK)
    return {"task_id": str(pipe.id)}
