"""
ingestion.py — Multi-format document loader and chunker
Supports: .txt, .pdf, directories
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))


class DocumentIngester:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def load_single_file(self, path: str) -> List[Document]:
        p = Path(path)
        if p.suffix.lower() == ".pdf":
            return self.load_pdf(path)
        return self.load_single_text_file(path)

    def load_single_text_file(self, path: str) -> List[Document]:
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="replace")
        return [Document(page_content=text, metadata={"source": p.name, "file_path": str(p)})]

    def load_pdf(self, path: str) -> List[Document]:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF not installed")
            raise ImportError("Install PyMuPDF: pip install pymupdf")

        p = Path(path)
        docs = []
        try:
            with fitz.open(str(p)) as pdf:
                for i, page in enumerate(pdf):
                    text = page.get_text()
                    if text.strip():
                        docs.append(Document(
                            page_content=text,
                            metadata={"source": p.name, "page": i + 1, "file_path": str(p)},
                        ))
            logger.info(f"Loaded {len(docs)} pages from {p.name}")
        except Exception as e:
            logger.error(f"Error loading PDF {p.name}: {e}")
            raise
        return docs

    def load_directory(self, folder: str) -> List[Document]:
        docs = []
        folder_path = Path(folder)
        if not folder_path.exists():
            logger.warning(f"Folder does not exist: {folder}")
            return []
        
        for path in folder_path.rglob("*"):
            if path.suffix.lower() in (".txt", ".pdf") and path.is_file():
                try:
                    docs.extend(self.load_single_file(str(path)))
                except Exception as e:
                    logger.error(f"Error loading {path}: {e}")
        
        logger.info(f"Loaded {len(docs)} documents from {folder}")
        return docs

    def process_and_chunk(self, docs: List[Document]) -> List[Document]:
        return self.splitter.split_documents(docs)

    def ingest_data_folder(self, folder: str) -> List[Document]:
        raw   = self.load_directory(folder)
        return self.process_and_chunk(raw)
