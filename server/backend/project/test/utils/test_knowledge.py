from sqlalchemy.ext.asyncio import AsyncSession
from project.knowledge.utils import get_topics, extract_knowledge, format_knowledge
from project.knowledge.models import Topic, TopicBelief, Belief, Category, BeliefMemory
from project.interact.models import Memory
from uuid import uuid4
import pytest

## run in docker container with command: pytest project/test/utils/test_knowledge.py -v -s
@pytest.mark.asyncio
async def test_get_topics(async_session: AsyncSession):
    hobby_id = str(uuid4())
    relationship_id = str(uuid4())
    education_id = str(uuid4())
    async_session.add(Category(id=hobby_id, name="Hobby", embedding=[0] * 512))
    async_session.add(Category(id=relationship_id, name="Relationship", embedding=[1] * 512))
    async_session.add(Category(id=education_id, name="Education", embedding=[100] * 512))
    await async_session.commit()

    seed = {
        "Martial Arts": {
            "beliefs": [
                {"text": "I practice martial arts", "type": "belief"},
                {"text": "I have a black belt", "type": "belief"},
            ],
            "embeddings": [
                [2] * 512,
                [0.5] * 512,
                [0.6] * 512,
            ],
            "category": hobby_id
        },
        "Programming": {
            "beliefs": [
                {"text": "I program in Python", "type": "belief"},
                {"text": "I program in Java", "type": "belief"},
            ],
            "embeddings": [
                [1] * 512,
                [1.4] * 512,
                [1.3] * 512,
            ],
            "category": hobby_id
        }, 
        "Romance": {
            "beliefs": [
                {"text": "I have a girlfriend", "type": "belief"},
                {"text": "I have a boyfriend", "type": "belief"},
            ],
            "embeddings": [
                [10] * 512,
                [9.4] * 512,
                [9.3] * 512,
            ],
            "category": relationship_id
        },
        "Friendship": {
            "beliefs": [
                {"text": "I have a friend", "type": "belief"},
                {"text": "I have a best friend", "type": "belief"},
            ],
            "embeddings": [
                [11] * 512,
                [10.4] * 512,
                [10.3] * 512,
            ],
            "category": relationship_id
        },
        "School": {
            "beliefs": [
                {"text": "I go to school", "type": "belief"},
                {"text": "I go to college", "type": "belief"},
            ],
            "embeddings": [
                [100] * 512,
                [100.4] * 512,
                [100.3] * 512,
            ],
            "category": education_id
        }
    }
    topic_ids = []
    for topic in seed:
        beliefs = seed[topic]["beliefs"]
        embeddings = seed[topic]["embeddings"]
        topic_id = str(uuid4())
        topic_ids.append(topic_id)
        topic_obj = Topic(
            id=topic_id,
            name=topic,
            embedding=embeddings[0],
            category_id=seed[topic]["category"],
        )
        async_session.add(topic_obj)
        for idx, belief in enumerate(beliefs):
            belief_id = str(uuid4())
            belief_obj = Belief(
                    id=belief_id,
                    text=belief['text'],
                    embedding=embeddings[idx + 1],
                    type=belief['type'],
                )
            topic_belief_obj = TopicBelief(
                    topic_id=topic_id,
                    belief_id=belief_id
            )
            async_session.add(belief_obj)
            async_session.add(topic_belief_obj)
        await async_session.commit()
    
    topics = await get_topics([5] * 512, async_session)
    assert len(topics) == 4
    assert topics[0] == topic_ids[0]
    assert topics[1] == topic_ids[1]
    assert topics[2] == topic_ids[2]
    assert topics[3] == topic_ids[3]

@pytest.mark.asyncio
async def test_extract_knowledge(async_session: AsyncSession):
    hobby_id = str(uuid4())
    relationship_id = str(uuid4())
    async_session.add(Category(id=hobby_id, name="Hobby", embedding=[0] * 512))
    async_session.add(Category(id=relationship_id, name="Relationship", embedding=[1] * 512))
    await async_session.commit()

    seed = {
        "Martial Arts": {
            "beliefs": [
                {"text": "I hate losing, it makes me feel weak", "type": "emotion"},
                {"text": "People who don't practice disgust me", "type": "emotion"},
                {"text": "I respect fighters who don't back down", "type": "emotion"},
                {"text": "Hard work and discipline trumps talent", "type": "value"},
                {"text": "Pain is required to build strength", "type": "value"},
                {"text": "Consistency is key", "type": "value"},
                {"text": "I'm above average at martial arts", "type": "opinion"},
                {"text": "Wrestling is less interesting than striking", "type": "opinion"},
                {"text": "Sparring is better practice than drills", "type": "opinion"},
            ],
            "embeddings": [
                [1] * 512,
                [4.5] * 512,
                [4.4] * 512,
                [4.3] * 512,
                [3.5] * 512,
                [3.4] * 512,
                [3.3] * 512,
                [2.5] * 512,
                [2.4] * 512,
                [2.3] * 512,
            ],
            "category": hobby_id
        },
        "Romance": {
            "beliefs": [
                {"text": "People who publicly display affection are gross", "type": "emotion"},
                {"text": "It pains me that I'll never find love", "type": "emotion"},
                {"text": "I hate seeing playboys get their way", "type": "emotion"},
                {"text": "Communication is critical to relationships", "type": "value"},
                {"text": "Men should be reliable and stable for their partners", "type": "value"},
                {"text": "Cheating is a sin and unforgivable", "type": "value"},
                {"text": "I like bubbly girls who are outgoing", "type": "opinion"},
                {"text": "I don't mind paying the bill for dates", "type": "opinion"},
                {"text": "I prefer to meet girls at the club or parties", "type": "opinion"},
            ],
            "embeddings": [
                [10] * 512,
                [9.2] * 512,
                [9.3] * 512,
                [9.4] * 512,
                [11.2] * 512,
                [11.3] * 512,
                [11.4] * 512,
                [12.2] * 512,
                [12.3] * 512,
                [12.4] * 512,
            ],
            "category": relationship_id
        },
    }   
    topic_ids = []
    for topic in seed:
        beliefs = seed[topic]["beliefs"]
        embeddings = seed[topic]["embeddings"]
        topic_id = str(uuid4())
        topic_ids.append(topic_id)
        topic_obj = Topic(
            id=topic_id,
            name=topic,
            embedding=embeddings[0],
            category_id=seed[topic]["category"],
        )
        async_session.add(topic_obj)
        for idx, belief in enumerate(beliefs):
            belief_id = str(uuid4())
            belief_obj = Belief(
                    id=belief_id,
                    text=belief['text'],
                    embedding=embeddings[idx + 1],
                    type=belief['type'],
                )
            topic_belief_obj = TopicBelief(
                    topic_id=topic_id,
                    belief_id=belief_id
            )
            async_session.add(belief_obj)
            async_session.add(topic_belief_obj)
            await async_session.commit()
            
            for i in range(5):
                memory_id = str(uuid4())
                memory_obj = Memory(
                    id=memory_id,
                    text="Memory" + str(i + 1) + ": " + belief['text'],
                    summary="Summary" + str(i + 1),
                    embedding=[5-i] * 512,
                )
                memory_belief_obj = BeliefMemory(
                    memory_id=memory_id,
                    belief_id=belief_id
                )
                async_session.add(memory_obj)
                async_session.add(memory_belief_obj)
            await async_session.commit()
        await async_session.commit()

    knowledge = await extract_knowledge([5] * 512, topic_ids, async_session)
    # assert not knowledge
    assert "Martial Arts" in knowledge
    assert "Romance" in knowledge

    belief = "I hate losing, it makes me feel weak"
    assert knowledge["Martial Arts"]["beliefs"][0]["belief"] == belief
    assert len(knowledge["Martial Arts"]["beliefs"][0]["memories"]) == 3
    assert knowledge["Martial Arts"]["beliefs"][0]["memories"][0] == "Memory1: " + belief
    assert knowledge["Martial Arts"]["beliefs"][0]["memories"][1] == "Memory2: " + belief
    assert knowledge["Martial Arts"]["beliefs"][0]["memories"][2] == "Memory3: " + belief

    belief = "People who don't practice disgust me"
    assert knowledge["Martial Arts"]["beliefs"][1]["belief"] == belief
    assert len(knowledge["Martial Arts"]["beliefs"][1]["memories"]) == 3
    assert knowledge["Martial Arts"]["beliefs"][1]["memories"][0] == "Memory1: " + belief
    assert knowledge["Martial Arts"]["beliefs"][1]["memories"][1] == "Memory2: " + belief
    assert knowledge["Martial Arts"]["beliefs"][1]["memories"][2] == "Memory3: " + belief

    belief = "Hard work and discipline trumps talent"
    assert knowledge["Martial Arts"]["beliefs"][2]["belief"] ==  belief
    assert len(knowledge["Martial Arts"]["beliefs"][2]["memories"]) == 3
    assert knowledge["Martial Arts"]["beliefs"][2]["memories"][0] == "Memory1: " + belief
    assert knowledge["Martial Arts"]["beliefs"][2]["memories"][1] == "Memory2: " + belief
    assert knowledge["Martial Arts"]["beliefs"][2]["memories"][2] == "Memory3: " + belief

    belief = "Pain is required to build strength"
    assert knowledge["Martial Arts"]["beliefs"][3]["belief"] == belief
    assert len(knowledge["Martial Arts"]["beliefs"][3]["memories"]) == 3
    assert knowledge["Martial Arts"]["beliefs"][3]["memories"][0] == "Memory1: " + belief
    assert knowledge["Martial Arts"]["beliefs"][3]["memories"][1] == "Memory2: " + belief
    assert knowledge["Martial Arts"]["beliefs"][3]["memories"][2] == "Memory3: " + belief

    belief = "People who publicly display affection are gross"
    assert knowledge["Romance"]["beliefs"][0]["belief"] == belief
    assert len(knowledge["Romance"]["beliefs"][0]["memories"]) == 3
    assert knowledge["Romance"]["beliefs"][0]["memories"][0] == "Memory1: " + belief
    assert knowledge["Romance"]["beliefs"][0]["memories"][1] == "Memory2: " + belief
    assert knowledge["Romance"]["beliefs"][0]["memories"][2] == "Memory3: " + belief

    belief = "It pains me that I'll never find love"
    assert knowledge["Romance"]["beliefs"][1]["belief"] == belief
    assert len(knowledge["Romance"]["beliefs"][1]["memories"]) == 3
    assert knowledge["Romance"]["beliefs"][1]["memories"][0] == "Memory1: " + belief
    assert knowledge["Romance"]["beliefs"][1]["memories"][1] == "Memory2: " + belief
    assert knowledge["Romance"]["beliefs"][1]["memories"][2] == "Memory3: " + belief

    belief = "Communication is critical to relationships"
    assert knowledge["Romance"]["beliefs"][2]["belief"] == belief
    assert len(knowledge["Romance"]["beliefs"][2]["memories"]) == 3
    assert knowledge["Romance"]["beliefs"][2]["memories"][0] == "Memory1: " + belief
    assert knowledge["Romance"]["beliefs"][2]["memories"][1] == "Memory2: " + belief
    assert knowledge["Romance"]["beliefs"][2]["memories"][2] == "Memory3: " + belief

    belief = "Men should be reliable and stable for their partners"
    assert knowledge["Romance"]["beliefs"][3]["belief"] == belief
    assert len(knowledge["Romance"]["beliefs"][3]["memories"]) == 3
    assert knowledge["Romance"]["beliefs"][3]["memories"][0] == "Memory1: " + belief
    assert knowledge["Romance"]["beliefs"][3]["memories"][1] == "Memory2: " + belief
    assert knowledge["Romance"]["beliefs"][3]["memories"][2] == "Memory3: " + belief


def test_format_knowledge():
    # Test with all types of knowledge present
    full_knowledge = {
        'beliefs': [
            {'text': 'I believe in science', 'confidence': 0.95},
            {'text': 'Education is important', 'confidence': 0.88}
        ],
        'memories': [
            {'text': 'Graduated from university', 'impact': 0.85},
            {'text': 'Won science fair', 'impact': 0.75}
        ],
        'topics': [
            {'name': 'Education', 'relevance': 0.92},
            {'name': 'Science', 'relevance': 0.89}
        ]
    }
    formatted_full = format_knowledge(full_knowledge)
    expected_full = (
        "Relevant Beliefs:\n"
        "- I believe in science (confidence: 0.95)\n"
        "- Education is important (confidence: 0.88)\n"
        "\nRelevant Memories:\n"
        "- Graduated from university (emotional impact: 0.85)\n"
        "- Won science fair (emotional impact: 0.75)\n"
        "\nRelevant Topics:\n"
        "- Education (relevance: 0.92)\n"
        "- Science (relevance: 0.89)"
    )
    assert formatted_full == expected_full

    # Test with only beliefs
    beliefs_only = {
        'beliefs': [
            {'text': 'I value honesty', 'confidence': 0.92},
            {'text': 'Trust is earned', 'confidence': 0.85}
        ]
    }
    formatted_beliefs = format_knowledge(beliefs_only)
    expected_beliefs = (
        "Relevant Beliefs:\n"
        "- I value honesty (confidence: 0.92)\n"
        "- Trust is earned (confidence: 0.85)"
    )
    assert formatted_beliefs == expected_beliefs

    # Test with only memories
    memories_only = {
        'memories': [
            {'text': 'First day at school', 'impact': 0.78},
            {'text': 'Learning to ride a bike', 'impact': 0.65}
        ]
    }
    formatted_memories = format_knowledge(memories_only)
    expected_memories = (
        "\nRelevant Memories:\n"
        "- First day at school (emotional impact: 0.78)\n"
        "- Learning to ride a bike (emotional impact: 0.65)"
    )
    assert formatted_memories == expected_memories

    # Test with only topics
    topics_only = {
        'topics': [
            {'name': 'Family', 'relevance': 0.95},
            {'name': 'Career', 'relevance': 0.82}
        ]
    }
    formatted_topics = format_knowledge(topics_only)
    expected_topics = (
        "\nRelevant Topics:\n"
        "- Family (relevance: 0.95)\n"
        "- Career (relevance: 0.82)"
    )
    assert formatted_topics == expected_topics

    # Test with empty dictionary
    empty_knowledge = {}
    formatted_empty = format_knowledge(empty_knowledge)
    assert formatted_empty == "No relevant knowledge found."

    # Test with empty lists
    empty_lists = {
        'beliefs': [],
        'memories': [],
        'topics': []
    }
    formatted_empty_lists = format_knowledge(empty_lists)
    assert formatted_empty_lists == "No relevant knowledge found."

    # Test with missing confidence/impact/relevance values
    missing_values = {
        'beliefs': [{'text': 'Test belief'}],
        'memories': [{'text': 'Test memory'}],
        'topics': [{'name': 'Test topic'}]
    }
    formatted_missing = format_knowledge(missing_values)
    expected_missing = (
        "Relevant Beliefs:\n"
        "- Test belief (confidence: 0.00)\n"
        "\nRelevant Memories:\n"
        "- Test memory (emotional impact: 0.00)\n"
        "\nRelevant Topics:\n"
        "- Test topic (relevance: 0.00)"
    )
    assert formatted_missing == expected_missing

    # Test with mixed content (some sections empty)
    mixed_content = {
        'beliefs': [{'text': 'Test belief', 'confidence': 0.75}],
        'memories': [],
        'topics': [{'name': 'Test topic', 'relevance': 0.80}]
    }
    formatted_mixed = format_knowledge(mixed_content)
    expected_mixed = (
        "Relevant Beliefs:\n"
        "- Test belief (confidence: 0.75)\n"
        "\nRelevant Topics:\n"
        "- Test topic (relevance: 0.80)"
    )
    assert formatted_mixed == expected_mixed
