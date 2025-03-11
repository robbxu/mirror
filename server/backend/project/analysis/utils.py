import orjson as json
# for other text file processing
import docx
from odf import text, teletype
from odf.opendocument import load
import io

def format_exchange(exchange: str):
    role_map = {
        "user": "[Subject]",
        "assistant": "[Psychologist]"
    }
    messages = json.loads(exchange)["messages"]
    text = ""
    for message in messages:
        text += role_map[message["role"]] + ": "
        text += message["content"] + "\n"
    return text

def truncate(text, limit):

    # Case 1: text is shorter than limit
    if len(text) <= limit:
        return text
    
    # First cut at limit
    truncated = text[:limit]
    
    # Split into words
    words = text.split()
    
    # Find which word we cut into
    current_pos = 0
    for word in words:
        next_pos = current_pos + len(word)
        # If this word crosses the limit (but not exactly at its end)
        if current_pos < limit < next_pos:
            # Remove this word
            return text[:current_pos].rstrip()
        # If we cut exactly at word end, keep it
        elif current_pos < limit == next_pos:
            return text[:limit].rstrip()
        current_pos = next_pos + 1  # +1 for the space
    
    return truncated.rstrip()


def extract_text_from_file(content: bytes, filename: str) -> str:
    ## .txt, .docx, .odt supported for now
    if filename.lower().endswith('.txt'):
        return content.decode('utf-8')
    
    elif filename.lower().endswith('.docx'):
        doc = docx.Document(io.BytesIO(content))
        return '\n\n'.join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)
    
    elif filename.lower().endswith('.odt'):
        doc = load(io.BytesIO(content))
        text_content = []
        for element in doc.getElementsByType(text.P):
            text_content.append(teletype.extractText(element))
        return '\n\n'.join(text_content)

    else: ## we dont support .doc because that is old word format
        raise ValueError(f"Unsupported file type: {filename}")

def chunk_file(content: bytes, filename: str, limit: int = 750) -> list[str]:
    text = extract_text_from_file(content, filename)
    # print(f"Debug: Starting to chunk text from {filename}")
    
    # Normalize each paragraph. right now this is naive normalization
    ## in the future we will need to account for essays, manifestos etc
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para_words = len(para.split())
        
        # If adding this paragraph would exceed limit and we have content
        if current_length + para_words > limit:
            # If we have current content, create a chunk
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # If single paragraph is too long, split it
            if para_words > limit:
                words = para.split()
                while words:
                    chunk_words = words[:limit]
                    chunks.append(' '.join(chunk_words))
                    words = words[limit:]
                continue
        
        current_chunk.append(para)
        current_length += para_words
    
    # Don't forget remaining content
    if current_chunk:
        chunks.append(' '.join(current_chunk))
        
    return chunks


def chunk_exchange(exchanges: list, limit: int):
    role_map = {
        "user": "[Subject]",
        "assistant": "[Psychologist]"
    }
    
    # First collect all texts and their lengths
    filtered_lengths = []
    texts = []
    for exchange in exchanges:
        # Remove json.loads - exchange is already a dict
        messages = exchange["messages"]
        for message in messages:
            text = role_map[message["role"]] + ": " + message["content"] + "\n"
            texts.append(text)
            # Only count user message lengths toward the limit
            if message["role"] == "user":
                filtered_lengths.append(len(text))
            else:
                filtered_lengths.append(0)

    chunks = []
    long = []
    current_chunk = ""
    cumul = 0
    i = 0
    
    while i < len(texts):
        if cumul + filtered_lengths[i] <= limit:
            current_chunk += texts[i]
            cumul += filtered_lengths[i]
            i += 1
            if i == len(texts):
                chunks.append(current_chunk)
                long.append(False)
        else:
            if cumul > 0:
                chunks.append(current_chunk)
                long.append(False)
                current_chunk = ""
                cumul = 0
            
            if filtered_lengths[i] > limit:
                value = texts[i]
                if len(current_chunk) > 0 and cumul == 0:
                    value = current_chunk + value
                    current_chunk = ""
                chunks.append(value)
                long.append(True)
                i += 1
    
    return chunks, long