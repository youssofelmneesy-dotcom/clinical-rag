from backend.embeddings import DeterministicHashEmbeddingService


def test_embedding_dimension_is_programmatic_and_reusable():
    service = DeterministicHashEmbeddingService(dimension=16)
    chunk_vector = service.embed_texts(["COPD spirometry"])[0]
    query_vector = service.embed_query("COPD spirometry")
    assert service.dimension == 16
    assert len(chunk_vector) == 16
    assert chunk_vector == query_vector
