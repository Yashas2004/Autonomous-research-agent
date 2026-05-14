"""
vectorstore.py — ChromaDB with OpenAI embeddings
  - SHA-256 deduplication
  - Batched insertion
  - Persistent storage
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

CHROMA_PATH   = os.getenv("CHROMA_PATH", str(Path(__file__).parent.parent / "data" / "chroma_db"))
COLLECTION    = os.getenv("CHROMA_COLLECTION", "research_kb")
EMBED_MODEL   = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
BATCH_SIZE    = 100


class VectorStoreManager:
    def __init__(self):
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.client = chromadb.PersistentClient(path=CHROMA_PATH)
            self._emb_fn = OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name=EMBED_MODEL,
            )
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION,
                embedding_function=self._emb_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Vectorstore initialized at {CHROMA_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize vectorstore: {e}")
            raise

    # ── Public API ────────────────────────────────────────────────────────────

    def add_documents(self, docs: List[Document]) -> int:
        """Add documents with deduplication. Returns number of new chunks added."""
        try:
            existing_ids = set(self.collection.get(include=[])["ids"])
        except Exception as e:
            logger.error(f"Error retrieving existing IDs: {e}")
            existing_ids = set()

        new_docs, new_ids, new_metas = [], [], []
        for doc in docs:
            doc_id = self._hash(doc.page_content)
            if doc_id in existing_ids:
                continue
            new_docs.append(doc.page_content)
            new_ids.append(doc_id)
            new_metas.append({k: str(v) for k, v in doc.metadata.items()})
            existing_ids.add(doc_id)

        if not new_docs:
            return 0

        try:
            for i in range(0, len(new_docs), BATCH_SIZE):
                self.collection.add(
                    documents=new_docs[i : i + BATCH_SIZE],
                    ids=new_ids[i : i + BATCH_SIZE],
                    metadatas=new_metas[i : i + BATCH_SIZE],
                )
            logger.info(f"Added {len(new_docs)} new documents to vectorstore")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

        return len(new_docs)

    def retrieve(self, query: str, k: int = 6) -> list[dict]:
        """Raw retrieval — returns ChromaDB result dicts."""
        results = self.collection.query(
            query_texts=[query],
            n_results=min(k, max(1, self.collection.count())),
            include=["documents", "metadatas", "distances"],
        )
        return results

    def delete_collection(self):
        self.client.delete_collection(COLLECTION)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION,
            embedding_function=self._emb_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
