from project.embedding.voyage import voyage_embedding
import pytest
import numpy as np

## run in docker container with command: pytest project/test/utils/test_voyage.py -v -s

def test_voyage_embedding():
    # Test single string input
    text = "This is a test sentence."
    embedding = voyage_embedding(text)
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) == 512  # Voyage-3-lite dimension
    assert all(isinstance(x, float) for x in embedding)

    # Test single string input with query flag
    query_embedding = voyage_embedding(text, query=True)
    assert query_embedding is not None
    assert isinstance(query_embedding, list)
    assert len(query_embedding) == 512
    assert all(isinstance(x, float) for x in query_embedding)

    # Test list input with single=True (should only embed first item)
    texts = ["First sentence.", "Second sentence.", "Third sentence."]
    single_embedding = voyage_embedding(texts, single=True)
    assert single_embedding is not None
    assert isinstance(single_embedding, list)
    assert len(single_embedding) == 512

    # Test list input with single=False (should embed all items)
    multiple_embeddings = voyage_embedding(texts, single=False)
    assert multiple_embeddings is not None
    assert isinstance(multiple_embeddings, list)
    assert len(multiple_embeddings) == len(texts)
    assert all(len(emb) == 512 for emb in multiple_embeddings)
    assert all(isinstance(x, float) for emb in multiple_embeddings for x in emb)

    # Test empty input
    empty_text = ""
    empty_embedding = voyage_embedding(empty_text)
    assert empty_embedding is None  # Voyage does not handle empty strings

    # Test error handling with invalid input
    invalid_input = None
    invalid_embedding = voyage_embedding(invalid_input)
    assert invalid_embedding is None

    # Test embeddings are different for different inputs
    text1 = "This is the first test sentence."
    text2 = "This is a completely different sentence."
    emb1 = voyage_embedding(text1)
    emb2 = voyage_embedding(text2)
    assert not np.allclose(emb1, emb2)  # Embeddings should be different

    # Test query vs document embeddings are different
    text = "Test sentence for query vs document comparison."
    query_emb = voyage_embedding(text, query=True)
    doc_emb = voyage_embedding(text, query=False)
    assert not np.allclose(query_emb, doc_emb)  # Query and document embeddings should differ

    # Test consistency of embeddings
    text = "Testing embedding consistency."
    emb1 = voyage_embedding(text)
    emb2 = voyage_embedding(text)
    assert np.allclose(emb1, emb2)  # Same input should give same embedding

