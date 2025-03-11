from project.analysis.tasks import gen_new_knowledge, gen_file_memories
from project.interact.models import Memory
from project.knowledge.models import Category, Topic, TopicBelief, Belief
from sqlalchemy.orm import Session
from sqlalchemy import update, select, func
from unittest import mock
from uuid import uuid4
import orjson as json

# pytest project/test/tasks/test_analysis.py -v -s   
def test_gen_new_knowledge(sync_session: Session):
    memory_ids = [str(uuid4()) for _ in range(4)]
    for i in range(4):
        sync_session.add(Memory(id=memory_ids[i], text="test" + str(i), summary="test" + str(i), embedding=[i] * 512))
    sync_session.commit()
    
    sync_session.add(Category(id=str(uuid4()), name="Hobby", embedding=[0] * 512))
    sync_session.add(Category(id=str(uuid4()), name="Relationship", embedding=[10] * 512))
    sync_session.add(Category(id=str(uuid4()), name="Education", embedding=[100] * 512))
    sync_session.commit()

    with mock.patch('project.analysis.tasks.get_sync_sess') as mocked_session:
        mocked_session.return_value = sync_session
        claude_responses = [
            json.dumps({
                "Martial Arts": {
                    "beliefs": [
                        {"text": "I hate losing, it makes me feel weak", "type": "emotion"},
                        {"text": "People who don't practice disgust me", "type": "emotion"},
                    ]
                },
                "Romance": {
                    "beliefs": [
                        {"text": "People who publicly display affection are gross", "type": "emotion"},
                        {"text": "It pains me that I'll never find love", "type": "emotion"},
                    ]
                }
            }),
            json.dumps({
                "Martial Arts": {
                    "beliefs": [
                        {"text": "I respect fighters who don't back down", "type": "emotion"},
                        {"text": "Hard work and discipline trumps talent", "type": "value"},
                    ]
                },
                "Romance": {
                    "beliefs": [
                        {"text": "I hate seeing playboys get their way", "type": "emotion"},
                        {"text": "Communication is critical to relationships", "type": "value"},
                    ]
                }
            }),
            json.dumps({
                "Martial Arts": {
                    "beliefs": [
                        {"text": "Pain is required to build strength", "type": "value"},
                        {"text": "Consistency is key", "type": "value"},
                    ]
                },
                "Romance": {
                    "beliefs": [
                        {"text": "Men should be reliable and stable for their partners", "type": "value"},
                        {"text": "Cheating is a sin and unforgivable", "type": "value"},
                    ]
                }
            }),
            json.dumps({
                "Martial Arts": {
                    "beliefs": [
                        {"text": "I'm above average at martial arts", "type": "opinion"},
                        {"text": "Wrestling is less interesting than striking", "type": "opinion"},
                    ]
                },
                "Romance": {
                    "beliefs": [
                        {"text": "I like bubbly girls who are outgoing", "type": "opinion"},
                        {"text": "I don't mind paying the bill for dates", "type": "opinion"},
                    ]
                },
                "Programming": {
                    "beliefs": [
                        {"text": "Python is the best language to start learning", "type": "opinion"},
                        {"text": "Deep understanding trumps rote memorization", "type": "value"},
                    ]
                }
            }),
        ]
        with mock.patch('project.analysis.tasks.claude_call', side_effect=claude_responses) as mocked_claude:  
            embedding_responses = [
                [[1] * 512, [11] * 512, [99] * 512,],
                [[1.1] * 512, [1.2] * 512, [1.3] * 512, [1.4] * 512, [1.5] * 512, [1.6] * 512, [1.7] * 512, [1.8] * 512,],
                [[11.1] * 512, [11.2] * 512, [11.3] * 512, [11.4] * 512, [11.5] * 512, [11.6] * 512, [11.7] * 512, [11.8] * 512,],
                [[99.1] * 512, [99.2] * 512],
            ]
            with mock.patch('project.analysis.tasks.voyage_embedding', side_effect=embedding_responses) as mocked_embedding:  
                gen_new_knowledge(memory_ids)
                assert mocked_claude.call_count == 4
                assert mocked_embedding.call_count == 4
                topics = sync_session.scalars(
                    select(Topic)
                    .order_by(Topic.name)
                ).all()
                assert len(topics) == 3
                assert topics[0].name == "Martial Arts"
                assert topics[0].category.name == "Hobby"
                assert topics[1].name == "Programming"
                assert topics[1].category.name == "Education"
                assert topics[2].name == "Romance"
                assert topics[2].category.name == "Relationship"
                
                beliefs = sync_session.scalars(
                    select(Belief)
                ).all()
                belief_texts = [belief.text for belief in beliefs]
                assert len(beliefs) == 18
                assert "I respect fighters who don't back down" in belief_texts
                assert "I'm above average at martial arts" in belief_texts
                assert "I like bubbly girls who are outgoing" in belief_texts
                assert "Python is the best language to start learning" in belief_texts
                assert "I hate seeing playboys get their way" in belief_texts
                assert "Men should be reliable and stable for their partners" in belief_texts
                assert "People who publicly display affection are gross" in belief_texts
                assert "I hate losing, it makes me feel weak" in belief_texts
                assert "Pain is required to build strength" in belief_texts
                assert "Wrestling is less interesting than striking" in belief_texts
                assert "People who don't practice disgust me" in belief_texts
                assert "Hard work and discipline trumps talent" in belief_texts
                assert "Consistency is key" in belief_texts
                assert "Cheating is a sin and unforgivable" in belief_texts
                assert "I don't mind paying the bill for dates" in belief_texts
                assert "Communication is critical to relationships" in belief_texts

                topic_beliefs = sync_session.scalars(
                    select(TopicBelief)
                ).all()
                assert len(topic_beliefs) == 18
            

def test_gen_file_memories(sync_session: Session):
    story = 'The sea surrounded him. His gaze was drawn out into the hypnotic swell and surge of emerald. It mixed with the smudges across the sky and the boughs of the clouds. Hanging grey swirled and the emerald curves clawed up. Everything shifted together in a menagerie of cold, wet colours. Lao tried to look away from the tearing, rising, and falling of the ocean and sky but he couldn’t. He was transfixed.\n\n' \
    + 'Something moved up beside him, but Lao could still not take his eyes from the horizons. The blurred shape started to hum next to him and despite the proximity Lao could barely hear the noise over the roaring call of the foaming waves. But the humming persisted and it seemed to grow louder drowning the sound of the sea.\n\n' \
    + 'Lao shook his head to clear it and turned to the figure beside him. "Abbott?" The long arms of the sloth were draped over a walking cane and he beamed with his characteristic grin. “What are you doing out here?”\n\n' \
    + 'The sloth continued to hum and tapped his cane on the rocky ground. It was tuneless and without rhythm but the abbot seemed to be enjoying himself. Reaching some sort of crescendo in his strange song he lifted his arms to embrace the horizon and with a flourishing gesture signalled the end of his symphony.\n\n' \
    + '“Humming.”\n\nBefore Lao could try and get a straight answer out of the little furry creature the arms began waving again and another song came belting out. This one lacked just as much of a tune as the last and elicited even greater gesticulations.\n\n' \
    + '“But,” Lao raised his voice to cut across the humming swirl that was the Abbot, “why are you out here?”\n\n' \
    + 'Long arms slowly retreated and rested back on the tip of the walking stick. Hui looked at Lao with his cool, shining eyes. “Well we shall start with bringing you back, shall we?”\n\n' \
    + 'Something small fell out from Lao’s belly as his mind whirled around the possibilities of what Hui had said. Had something happened to Akiko? Was Clamshell okay? He opened his mouth but Hui cut him off again, waving one of his long clawed hands in Lao’s direction. “No no. To bring you back to the here and now. There’s only one reason a person gets a thousand yard stare in their eyes and then keeps looking.”\n\n' \
    + 'A chill ran up Lao’s spine. He knew what the old sloth was talking about. Those moments when he wasn’t sure if he was standing on the shore of the waves, the brief sensation of standing at the bottom of the ocean, or his mind spreading and showing him glimpses of illuminated fish swimming through utter blackness alongside the visions of whales floating through cerulean. Neither the thief, the priest, or the monk, Lao’s power came from the ocean itself and he was risking losing himself to it.\n\n'
    data = bytes(story, 'utf-8')

    with mock.patch('project.analysis.tasks.get_sync_sess') as mocked_function:
        mocked_function.return_value = sync_session
        memory_ids = gen_file_memories(data, "story.txt", 50)
        assert len(memory_ids) > 0
        results = sync_session.scalars(
            select(Memory)
            .where(Memory.id.in_(memory_ids))
        ).all()
        assert len(results) == len(memory_ids)
        texts = [result.text for result in results]
        for text in texts:
            assert text in story.replace("\n\n", " ")
        