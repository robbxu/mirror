import orjson as json
from uuid import uuid4
from celery import shared_task, chord
from sqlalchemy import delete, select, insert, update, func
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from project.database import get_sync_sess

from project.interact.models import Memory, Interaction, Exchange
from project.knowledge.models import Belief, Topic, TopicBelief, Category, BeliefMemory
from project.embedding.voyage import voyage_embedding
from project.prompt.claude import claude_norm_exchange, claude_call, claude_belief_analysis
from project.analysis.utils import chunk_file
from project.analysis.schemas import get_belief_analysis_schema

from opentelemetry.propagate import inject, extract
from opentelemetry import trace
from opentelemetry.trace.status import StatusCode


# https://stackoverflow.com/questions/39815771/how-to-combine-celery-with-asyncio
@shared_task(max_retries=3, default_retry_delay=60)
def gen_file_memories(content: bytes, filename: str, chunk_size: int = 750):
    ## Process uploaded text file into memories
    with get_sync_sess() as db_session:
        try:
            chunks = chunk_file(content, filename, chunk_size)
            # print(f"Worker Debug: Created {len(chunks)} chunks")
            memory_ids = []

            for chunk in chunks:
                memory_id = str(uuid4())
                embedding = voyage_embedding([chunk], query=False) 
                # print(f"Worker Debug: Embedding type: {type(embedding)}, shape: {len(embedding) if isinstance(embedding, list) else 'not a list'}")
                memory = Memory(
                    id=memory_id,
                    text=chunk,
                    embedding=embedding,
                    impact=0.0
                )
                db_session.add(memory)
                memory_ids.append(memory_id)

            db_session.commit()
            return memory_ids

        except Exception as e:
            print(f"Worker Debug: Error in process_upload: {str(e)}")
            db_session.rollback()
            raise


@shared_task(max_retries=3, default_retry_delay=60)
def gen_new_knowledge(memory_ids: list, headers):
    tracer = trace.get_tracer(__name__)
    context = extract(headers)
    
    # If task takes long we need a lock to prevent multiple instances created updates at the same time
    # https://docs.celeryq.dev/en/latest/tutorials/task-cookbook.html#cookbook-task-serial
    with get_sync_sess() as db_session:  # execute until yield. Session is yielded value
        try:
            rows = db_session.execute(
                select(Memory.id, Memory.text, Memory.summary, Memory.embedding)
                .where(Memory.id.in_(memory_ids))
                .order_by(Memory.created_time.desc())
            ).all()
             
            knowledge_map = {}
            for row in rows:
                memory_id = str(row[0])
                text = row[1]
                # Call helper functions using memory attributes to extract beliefs
                with tracer.start_as_current_span("ChatAnthropic", context=context) as span:
                    schema = get_belief_analysis_schema()
                    analysis_prompt = claude_belief_analysis(schema, text)
                    analysis_raw = claude_call(analysis_prompt)
                    analysis = json.loads(analysis_raw)
                    span.set_input({"text": text, "schema": schema})
                    span.set_output({"analysis": analysis})
                    span.set_status(StatusCode.OK)

                analysis = analysis["topics"]["topics"]
                for item in analysis:
                    topic = item["topic"]
                    if topic not in knowledge_map:
                        knowledge_map[topic] = {"beliefs": []}

                    additions = item["beliefs"]
                    for belief in additions:
                        if belief["type"] == "core belief":
                            belief["type"] = "value"
                        elif belief["type"] == "key opinion":
                            belief["type"] = "opinion"
                        elif belief["type"] == "emotional reflection":
                            belief["type"] = "emotion"
                    knowledge_map[topic]["beliefs"] += additions
            
            topics = [topic for topic in knowledge_map]
            topic_ids = [str(uuid4()) for topic in topics]

            topic_map = {}
            for idx, topic in enumerate(topics):
                topic_map[topic] = topic_ids[idx]

            existing = db_session.execute(
                select(Topic.id, Topic.name)
                .where(Topic.name.in_(topics))
            ).all()
            old_topics = [str(row[1]) for row in existing]
            new_topics = [topic for topic in topics if topic not in old_topics]
            topic_embeddings = voyage_embedding(new_topics, False, single=False)

            old_topic_ids = [str(row[0]) for row in existing]
            for idx, topic in enumerate(old_topics):
                topic_map[topic] = old_topic_ids[idx]
            
            topic_inserts = []
            for idx, topic in enumerate(new_topics):
                topic_inserts.append({"id": topic_map[topic],
                                      "name": topic, 
                                      "embedding": topic_embeddings[idx]})
            
            db_session.execute(insert(Topic), topic_inserts)
            db_session.commit()

            subquery = ( 
                select(Topic.id.label("topic_id"), Category.id.label("category_id"), 
                    func.rank().over(
                        order_by=Category.embedding.l2_distance(Topic.embedding),
                        partition_by=Topic.id
                    ).label('rank'))
                .where(Topic.id.in_(topic_ids))
                .join_from(Topic, Category, Topic.category_id.is_(None))
                .subquery()
            )
            rows = db_session.execute(
                select(subquery.c.topic_id, subquery.c.category_id, subquery.c.rank)
                .where(subquery.c.rank < 2)
            ).all()

            topic_updates = []
            for row in rows:
                topic_id = str(row[0])
                category_id = str(row[1])
                topic_updates.append({"id": topic_id, "category_id": category_id})
            db_session.execute(update(Topic), topic_updates)
            db_session.commit()


            # Update the database with extracted beliefs
            belief_inserts = []
            topic_belief_inserts = []
            for topic in knowledge_map:
                beliefs = knowledge_map[topic]["beliefs"]
                embeddings = voyage_embedding([belief["belief"] for belief in beliefs], False, single=False)
                for idx, belief in enumerate(beliefs):
                    belief_id = str(uuid4())
                    belief_inserts.append({"id": belief_id, 
                                           "text": belief["belief"], 
                                           "embedding": embeddings[idx], 
                                           "type": belief["type"]})
                    topic_belief_inserts.append({"topic_id": topic_map[topic], 
                                                 "belief_id": belief_id})

            db_session.execute(insert(Belief), belief_inserts)
            db_session.execute(insert(TopicBelief), topic_belief_inserts)
            db_session.commit()
            return memory_ids
        except Exception as exc:
            db_session.rollback()
            print(exc)


@shared_task(max_retries=3, default_retry_delay=60)
def cluster_memories(memory_ids: list):
    # If task takes long we need a lock to prevent multiple instances created updates at the same time
    # https://docs.celeryq.dev/en/latest/tutorials/task-cookbook.html#cookbook-task-serial
    with get_sync_sess() as db_session:  # execute until yield. Session is yielded value
        try:
            rows = db_session.execute(
                select(Memory.id, Memory.text, Memory.summary, Memory.embedding)
                .where(Memory.id.in_(memory_ids))
                .order_by(Memory.created_time.desc())
            ).all()
            
            subquery = ( 
                select(Belief.id.label("belief_id"), Memory.id.label("memory_id"), 
                    func.rank().over(
                        order_by=Belief.embedding.l2_distance(Memory.embedding),
                        partition_by=Belief.id
                    ).label('rank'))
                .where(Memory.id.in_(memory_ids))
                .join_from(Belief, Memory, Memory.id.is_not(None))
                .subquery()
            )
            rows = db_session.execute(
                select(subquery.c.belief_id, subquery.c.memory_id, subquery.c.rank)
                .where(subquery.c.rank <= 3)
            ).all()

            belief_memory_inserts = []
            for row in rows:
                belief_id = str(row[0])
                memory_id = str(row[1])
                belief_memory_inserts.append({"belief_id": belief_id, "memory_id": memory_id})
            db_session.execute(insert(BeliefMemory), belief_memory_inserts)
            db_session.commit()
        except Exception as exc:
            db_session.rollback()
            print(exc)
