"""
Wrapper quanh ChromaDB (persistent, local) + OpenAI embeddings.
"""
from typing import Sequence

import chromadb
from openai import OpenAI

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    require_api_key,
)

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_openai_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        require_api_key()
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def get_collection():
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Gọi OpenAI embedding API cho một batch text."""
    client = _get_openai_client()
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=list(texts))
    return [item.embedding for item in resp.data]


def reset_collection():
    """Xoá sạch collection hiện tại (dùng khi muốn ingest lại từ đầu)."""
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return get_collection()
