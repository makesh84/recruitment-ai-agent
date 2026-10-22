
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.jobs import JOBS


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)


def job_text(job: dict) -> str:
    return " ".join([
        job["title"],
        job["company"],
        job["location"],
        job["description"],
        " ".join(job["required_skills"]),
    ])


def semantic_search(query: str, top_k: int = 3) -> list[dict]:
    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if not JOBS:
        return []

    model = get_model()
    documents = [job_text(job) for job in JOBS]

    document_vectors = model.encode(
        documents,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    query_vector = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(document_vectors.shape[1])
    index.add(document_vectors)

    k = min(top_k, len(JOBS))
    scores, indices = index.search(query_vector, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue

        results.append({
            "job": JOBS[int(idx)],
            "similarity": round(float(score), 4),
        })

    return results
