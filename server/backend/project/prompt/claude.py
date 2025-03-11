import orjson as json
import anthropic
from project.config import settings
from langchain_anthropic import ChatAnthropic
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
# from opentelemetry import trace as trace_api
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk import trace as trace_sdk
# from opentelemetry.sdk.trace.export import SimpleSpanProcessor

  
tracer_provider = register() 

LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    temperature=0,
    system=""
)

def claude_call(prompt: list):
    message = llm.invoke(prompt)
    return message.content
    # full_response = ""
    # for block in message.content: 
    #     if hasattr(block, 'text'):  # Ensure we only process text blocks
    #         full_response += block.text   
    # return full_response
    

def claude_belief_prompt(knowledge: dict, history: list):
    base = ('You are to play the role of a person with the beliefs, memories ' \
            'and opinions defined in the provided JSON schema. You should ' \
            'respond to queries fully in-character, and never acknowledge that ' \
            'you are referencing a schema or playing a role. Do not use asterisks. ' \
            + 'Respond "understood" if you understand the assignment.' \
            '\nSchema:\n')

    schema = json.dumps(knowledge).decode('utf-8')
    prompt = [
        {"role": "user", "content": base + schema},
        {"role": "assistant", "content": "Understood."},
    ] + history
    return prompt
    

def claude_style_prompt(outline: dict):
    base = 'You are to play the role of a person, responding fully in-character and ' \
    + 'never acknowledging you are not them. You will be provided samples of this peron\'s writings' \
    + 'and a message to rewrite in their style. You should rewrite the message as if you were them, ' \
    + 'fully in-character and reflecting the writing style shown in the provided samples. ' \
    + 'Do not use the writing samples for any purpose besides adjusting the tone and vocabulary of your response.' \
    + 'The message and writing samples will be provided in JSON format, and you should respond in plaintext. ' \
    + 'Respond "understood" if you understand the assignment.' \
    + '\nSchema:\n'

    prompt = [
        {"role": "user", "content": base},
        {"role": "assistant", "content": "Understood."},
        {"role": "user", "content": json.dumps(outline).decode('utf-8')}
    ]
    return prompt

def claude_belief_analysis(schema: dict, passage: str):
    base = 'You are a psychologist analyzing a subject to extract their ' \
    + 'core values and beliefs. You will conduct this analysis on the conversations  ' \
    + 'and writings provided by the subject, using the guidelines defined below. ' \
    + 'Please only include JSON in your response, and exclude definitions.\nGuidelines:\n'

    schema = json.dumps(schema).decode('utf-8')
    prompt = [
        {"role": "user", "content": base + schema},
        {"role": "user", "content": passage}
    ]
    return prompt


def claude_norm_exchange(formatted: str):
    base = 'You are given a conversation between a subject and a psychologist. ' \
    + 'For each of the subject\'s messages, please rephrase their response so ' \
    + 'that if they are responding to a question or prompt, they explicitly restate ' \
    + 'the question before answering. ' \
    + 'Finally, write a summary of the subject\'s messages from their point of view. ' \
    + 'Please write your results in the following format:\n'
    
    schema = json.dumps({"user_messages": 
                            ["[REPHRASED MESSAGE]","[REPHRASED MESSAGE]",],
                         "summary": "[SUMMARY]"
                        }).decode('utf-8')

    prompt = [
        {"role": "user", "content": base + schema},
        {"role": "assistant", "content": "Understood."},
        {"role": "user", "content": formatted}
    ]
    return prompt
