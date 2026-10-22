
from app.semantic_search import semantic_search


def test_semantic_search_returns_results():
    results = semantic_search("generative AI and language models")

    assert len(results) > 0
    assert "job" in results[0]
    assert "similarity" in results[0]


def test_semantic_search_respects_top_k():
    results = semantic_search("Python developer", top_k=2)

    assert len(results) <= 2


def test_semantic_search_rejects_empty_query():
    try:
        semantic_search("")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "empty" in str(exc).lower()
