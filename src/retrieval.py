"""
retrieval.py — Smart retriever with cosine distance filtering
"""

from __future__ import annotations

import logging
import os
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))  # cosine distance < 0.6 = good


class Retriever:
    def __init__(self, vectorstore):
        self.vs = vectorstore

    def retrieve(self, query: str, k: int = 6, threshold: float = SIMILARITY_THRESHOLD) -> list[Document]:
        """Return Documents above similarity threshold."""
        try:
            count = self.vs.collection.count()
            if count == 0:
                return []

            results = self.vs.retrieve(query, k=min(k, count))
            docs = []
            docs_list   = results.get("documents", [[]])[0]
            metas_list  = results.get("metadatas", [[]])[0]
            dists_list  = results.get("distances", [[]])[0]

            for text, meta, dist in zip(docs_list, metas_list, dists_list):
                if dist <= threshold:  # lower distance = more similar in cosine space
                    docs.append(Document(page_content=text, metadata=meta))

            return docs
        except Exception as e:
            logger.error(f"[Retriever] Error retrieving documents: {e}")
            return []
