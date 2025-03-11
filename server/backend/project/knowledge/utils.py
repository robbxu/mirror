from datetime import datetime, timezone
from fastapi import HTTPException

from sqlalchemy import update, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from project.interact.models import Memory, Exchange, Interaction
from project.knowledge.models import TopicBelief, Topic, Belief, BeliefMemory
from project.embedding.voyage import voyage_embedding
from project.analysis.utils import truncate
from project.analysis import tasks


async def get_topics(context_embedding: list, session: AsyncSession):
    subquery = (
        select(Topic.id, Topic.name, Topic.category_id,
            Topic.embedding.l2_distance(context_embedding).label('distance'),
            func.rank().over(
                order_by=Topic.embedding.l2_distance(context_embedding),
                partition_by=Topic.category_id
            ).label('rank'))
        .subquery()
    )
    topics = (await session.execute(
        select(subquery.c.id, subquery.c.name, subquery.c.category_id,
                subquery.c.rank, subquery.c.distance)
        .where(subquery.c.rank <= 2)
        .order_by(subquery.c.distance)
        .limit(4)
    )).all()

    topic_ids = []
    for row in topics:
        topic_ids.append(str(row[0]))

    return topic_ids

async def extract_knowledge(context_embedding: list, topics: list, 
                            session: AsyncSession):
    subquery = (
        select(TopicBelief.belief_id, Belief.text, Belief.type,
            Topic.name.label('topic'), 
            func.rank().over(
                order_by=Belief.embedding.l2_distance(context_embedding),
                partition_by=TopicBelief.topic_id
            ).label('rank'))
        .where(TopicBelief.topic_id.in_(topics))
        .join_from(TopicBelief, Belief, TopicBelief.belief_id == Belief.id)
        .join_from(TopicBelief, Topic, TopicBelief.topic_id == Topic.id)
        .subquery()
    )
    beliefs = (await session.execute(
        select(subquery.c.belief_id, subquery.c.text, subquery.c.type,
                subquery.c.topic, subquery.c.rank)
        .where(subquery.c.rank <= 50)
        .order_by(subquery.c.rank)
    )).all()

    topic_map = {}
    belief_map = {}
    belief_ids = []

    for row in beliefs:
        topic = row[3]
        type = row[2]
        text = row[1]
        if topic not in topic_map:
            topic_map[topic] = {"ids": [], "beliefs": [], "opinion": 0, 
                              "emotion": 0, "value": 0, "total": 0}
        
        if topic_map[topic][type] < 2 and topic_map[topic]["total"] < 4:
            topic_map[topic]["ids"].append(str(row[0]))
            topic_map[topic]["beliefs"].append(text)
            topic_map[topic][type] += 1
            topic_map[topic]["total"] += 1
            
            belief_ids.append(str(row[0]))
            belief_map[str(row[0])] = {
                "topic": topic, "memories": [], "summaries": [],
                "idx": len(topic_map[topic]["ids"]) - 1 }
    
    subquery = (
        select(BeliefMemory.belief_id, Memory.text, Memory.summary,
            func.rank().over(
                order_by=Memory.embedding.l2_distance(context_embedding),
                partition_by=BeliefMemory.belief_id
            ).label('rank'))
        .where(BeliefMemory.belief_id.in_(belief_ids))
        .join_from(BeliefMemory, Memory, BeliefMemory.memory_id == Memory.id)
        .subquery()
    )
    memories = (await session.execute(
        select(subquery.c.belief_id, subquery.c.text, subquery.c.summary,
                subquery.c.rank)
        .where(subquery.c.rank <= 3)
    )).all()

    for row in memories:
        belief_map[str(row[0])]["memories"].append(row[1])
        belief_map[str(row[0])]["summaries"].append(row[2])
    
    result = {}
    for topic in topic_map:
        if topic not in result:
            result[topic] = {"beliefs": []}
        for idx, belief in enumerate(topic_map[topic]["beliefs"]):
            belief_id = topic_map[topic]["ids"][idx]
            result[topic]["beliefs"].append({
                "belief": belief,
                "memories": belief_map[belief_id]["memories"],
                "summaries": belief_map[belief_id]["summaries"]
            })
    return result


def format_knowledge(knowledge_dict: dict) -> str:
    ## take a knowledge dict and format it into a returned string. 
    ## double check the intake format in test file - Ben
    formatted = {
        "topics": knowledge_dict
    }
    
    for topic in formatted["topics"]:
        formatted["topics"][topic]["description"] = "For  " + topic \
        + ", the attached beliefs are significant. Each belief comes with " \
        + "a list of memories and summaries from which the belief was derived"
    
    return formatted