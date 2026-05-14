"""
Autonomous Research Agent - Core modules

Modules:
  - agent: GPT-4o ReAct agent for research and writing
  - vectorstore: ChromaDB with OpenAI embeddings
  - retrieval: Semantic search with similarity filtering
  - ingestion: Multi-format document loader and chunker
  - scraper: Web scraper with noise filtering
"""

__version__ = "1.0.0"
__author__ = "Autonomous Research Team"

__all__ = [
    "agent",
    "vectorstore",
    "retrieval",
    "ingestion",
    "scraper",
]

