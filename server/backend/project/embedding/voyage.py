import voyageai
from project.config import settings

vo = voyageai.Client() # automatically uses the environment variable VOYAGE_API_KEY - in config.py


def voyage_embedding(texts: list | str, query: bool = False, single: bool = True):
    if texts is None:
        return None
    if single:
        texts = [texts] if isinstance(texts, str) else [texts[0]]
    elif isinstance(texts, str):
        texts = [texts]

    try:
        input_type = "query" if query else "document"
        result = vo.embed(texts, model="voyage-3-lite", input_type=input_type)
        return result.embeddings[0] if single else result.embeddings
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        return None