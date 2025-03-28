import voyageai
from project.config import settings
from opentelemetry import trace
from opentelemetry.trace import StatusCode

vo = voyageai.Client() # automatically uses the environment variable VOYAGE_API_KEY - in config.py

def voyage_embedding(texts: list | str, query: bool = False, single: bool = True):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("voyage_embedding", openinference_span_kind="embedding") as span:
        span.set_input({"query": query, "texts": texts})
        if texts is None:
            return None
        if isinstance(texts, str):
            texts = [texts]
        span.set_attribute("num_texts", len(texts))
        if single:
            texts = [texts] if isinstance(texts, str) else [texts[0]]
        elif isinstance(texts, str):
            texts = [texts]

        try:
            input_type = "query" if query else "document"
            result = vo.embed(texts, model="voyage-3-lite", input_type=input_type)
            if single:
                span.set_output({"result": result.embeddings[0]})
                span.set_status(StatusCode.OK)
            else:
                span.set_output({"result": result.embeddings})
                span.set_status(StatusCode.OK)
            return result.embeddings[0] if single else result.embeddings
        except Exception as e:
            print(f"Error getting embedding: {str(e)}")
            span.set_status(StatusCode.ERROR)
            return None