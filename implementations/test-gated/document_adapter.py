"""Expose ranked unique documents through the synchronous evaluation boundary."""

from __future__ import annotations

import asyncio
from dataclasses import fields

from rag.retrieval.types import RetrievalHit
from rag.types import RetrievedChunk


def collapse_documents(chunks: list[RetrievedChunk]) -> list[RetrievalHit]:
    """Keep the first chunk of each document in the supplied backend order.

    Document IDs come from metadata, falling back to source_url for absent or
    blank IDs. Chunk IDs are never used as document identities. Returned hits
    retain chunk ranks; metadata also records contiguous document positions.
    """
    hits = []
    seen = set()
    for position, chunk in enumerate(chunks, start=1):
        document_id = chunk.metadata.get("document_id")
        if document_id is None or (isinstance(document_id, str) and not document_id.strip()):
            document_id = chunk.source_url
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(
                f"Chunk {chunk.id} needs a valid document_id or source_url"
            )
        if document_id in seen:
            continue
        seen.add(document_id)
        chunk_rank = chunk.rank if chunk.rank is not None else position
        metadata = dict(chunk.metadata)
        metadata.update(
            evaluation_chunk_id=chunk.id,
            evaluation_chunk_rank=chunk_rank,
            evaluation_document_rank=len(hits) + 1,
        )
        values = {field.name: getattr(chunk, field.name) for field in fields(RetrievedChunk)}
        values.update(id=document_id, rank=chunk_rank, metadata=metadata)
        hits.append(RetrievalHit(**values))
    return hits


class DocumentRetrievalAdapter:
    """Retrieve progressively deeper chunk rankings for document evaluation.

    This adapter owns its reusable event-loop runner. Injected retrievers and
    clients remain owned by the caller; client-owning subclasses can close
    their resources using this runner before closing the adapter.
    """

    def __init__(self, retriever, chunk_count: int | None = None):
        if chunk_count is not None and (type(chunk_count) is not int or chunk_count < 0):
            raise ValueError("chunk_count must be a non-negative integer or None")
        self._retriever = retriever
        self.chunk_count = chunk_count
        self._runner = asyncio.Runner()
        self._adapter_closed = False
        self.last_search_stats = self._empty_stats()

    @staticmethod
    def _empty_stats():
        return {
            "chunks_retrieved": 0,
            "unique_documents": 0,
            "documents_returned": 0,
            "total_chunks_received": 0,
            "chunk_limits": [],
            "exhausted": False,
        }

    def search(self, query: str, k: int) -> list[RetrievalHit]:
        self.last_search_stats = self._empty_stats()
        if type(k) is not int or k < 1:
            raise ValueError("k must be a positive integer")
        if self._adapter_closed:
            raise RuntimeError("DocumentRetrievalAdapter is closed")
        if self.chunk_count == 0:
            self.last_search_stats["exhausted"] = True
            return []
        return self._runner.run(self._search(query, k))

    async def _search(self, query: str, k: int) -> list[RetrievalHit]:
        limit = min(k, self.chunk_count) if self.chunk_count is not None else k
        stats = self.last_search_stats
        while True:
            stats["chunk_limits"].append(limit)
            chunks = await self._retriever.retrieve(query, top_k=limit, filters=None)
            stats["total_chunks_received"] += len(chunks)
            # Replace the entire ranking on expansion: approximate search may
            # return a changed prefix, so merging older responses is incorrect.
            documents = collapse_documents(chunks)
            exhausted = len(chunks) < limit or (
                self.chunk_count is not None and limit >= self.chunk_count
            )
            stats.update(
                chunks_retrieved=len(chunks),
                unique_documents=len(documents),
                exhausted=exhausted,
            )
            if len(documents) >= k or exhausted:
                results = documents[:k]
                stats["documents_returned"] = len(results)
                return results
            limit *= 2
            if self.chunk_count is not None:
                limit = min(limit, self.chunk_count)

    def close(self):
        if not self._adapter_closed:
            try:
                self._runner.close()
            finally:
                self._adapter_closed = True

    def __enter__(self):
        if self._adapter_closed:
            raise RuntimeError("DocumentRetrievalAdapter is closed")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
