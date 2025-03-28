import orjson as json
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import update, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from project.interact.models import Memory, Exchange, Interaction
from project.analysis.utils import truncate

ALLOWED_EXTENSIONS = {
    '.txt',  # Text files
    '.docx',  # Microsoft Word (new)
    '.odt',  # OpenDocument
}

def validate_file_extension(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)
    

def raw(message: dict):
    text = message["role"] + ": "
    text += message["content"] + "\n"
    return text

def load_history(rows):
    history = []
    for row in rows:
        id = str(row[0])
        conversation = json.loads(row[1])
        for message in conversation["messages"]:
            history.append(message)
    return history

def extract_context(history: list, limit: int):
    if len(history) == 0:
        return ""
    context = ""
    history_copy = history.copy()
    while len(context) + len(raw(history_copy[-1])) <= limit:
        context = raw(history_copy[-1]) + context
        history_copy.pop()
        if len(history_copy) == 0:
            break
    if len(context) <= limit * 0.3 and len(history_copy) > 0:
        remaining = limit - len(context)
        truncated = truncate(raw(history_copy[-1]), remaining) + "\n"
        context = truncated + context
    return context

async def record_exchange(message: str, generation: str, interaction_id: str, 
                          session: AsyncSession):
    exchange = {
        "messages": [ 
            {"role": "user", "content": message},
            {"role": "assistant", "content": generation}
        ]
    }
    formatted = json.dumps(exchange).decode('utf-8')

    to_save = Exchange(
        id=str(uuid4()), text=formatted, 
        interaction_id=interaction_id
    )
    session.add(to_save)
    await session.commit()
