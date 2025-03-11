import sys
from pathlib import Path
import anthropic
from project.config import settings
from project.prompt.claude import claude_call, claude_belief_prompt

# Add Python path when running tests
project_root = str(Path(__file__).parents[3])
sys.path.append(project_root)

anthropic.api_key = settings.ANTHROPIC_API_KEY

def test_claude_integration():
    # Sample -> keep updated if we change the format!
    knowledge = {
        "beliefs": {
            "core_values": ["honesty", "creativity"],
            "opinions": {
                "technology": "Technology should be used to enhance human capabilities"
            }
        },
        "memories": [
            {
                "text": "I once built a treehouse when I was young",
                "reflection": "That experience taught me to be resourceful"
            }
        ]
    }
    history = [
        {"role": "user", "content": "What do you think about AI?"},
        {"role": "assistant", "content": "I believe AI should be developed responsibly."},
        {"role": "user", "content": "Tell me about your experience with building things."}
    ]

    # test the way we use claude_belief_prompt
    formatted_prompt = claude_belief_prompt(knowledge, history)
    
    try:
        response = claude_call(formatted_prompt)
        print("Claude Response:", response) 
        # no need for .content because we already handle formatting it in claude_call
    except Exception as e:
        print("Error calling Claude:", str(e))

if __name__ == "__main__":
    test_claude_integration()