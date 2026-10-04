"""Adapt asynchronous chunk retrieval to synchronous document evaluation."""
import asyncio
from dataclasses import fields
from rag.retrieval.types import RetrievalHit
from rag.types import RetrievedChunk


def collapse_documents(chunks: list[RetrievedChunk]) -> list[RetrievalHit]:
    """Keep the first chunk per document without changing backend order."""
    hits = []
    seen = set()
    for position, chunk in enumerate(chunks, 1):
        document_id = chunk.metadata.get('document_id')
        if document_id is None or document_id == '':
            document_id = chunk.source_url
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(f'Chunk {chunk.id} requires a valid document_id or source_url')
        if document_id in seen:
            continue
        seen.add(document_id)
        values = {field.name: getattr(chunk, field.name) for field in fields(RetrievedChunk)}
        rank = chunk.rank if chunk.rank is not None else position
        metadata = dict(chunk.metadata)
        metadata.update(evaluation_chunk_id=chunk.id, evaluation_chunk_rank=rank,
                        evaluation_document_rank=len(hits) + 1)
        values.update(id=document_id, rank=rank, metadata=metadata)
        hits.append(RetrievalHit(**values))
    return hits


class DocumentRetrievalAdapter:
    """Reuse one event loop across searches; injected clients remain caller-owned."""
    def __init__(self, retriever, chunk_count: int | None = None, filters: dict | None = None):
        if chunk_count is not None and (not isinstance(chunk_count, int)
                                       or isinstance(chunk_count, bool) or chunk_count < 0):
            raise ValueError('chunk_count must be a nonnegative integer')
        self._retriever = retriever
        self.chunk_count = chunk_count
        self.filters = filters
        self._runner = asyncio.Runner()
        self.last_search_stats = {}

    def search(self, query: str, k: int) -> list[RetrievalHit]:
        self.last_search_stats = {
            'chunks_retrieved': 0, 'unique_documents': 0, 'documents_returned': 0,
            'total_chunks_received': 0, 'chunk_limits': [], 'exhausted': False}
        if not isinstance(k, int) or isinstance(k, bool) or k < 1:
            raise ValueError('k must be a positive integer')
        return self._runner.run(self._search(query, k))

    async def _search(self, query, k):
        stats = self.last_search_stats
        if self.chunk_count == 0:
            stats['exhausted'] = True
            return []
        limit = min(k, self.chunk_count) if self.chunk_count is not None else k
        while True:
            stats['chunk_limits'].append(limit)
            chunks = await self._retriever.retrieve(query, top_k=limit, filters=self.filters)
            hits = collapse_documents(chunks)
            exhausted = len(chunks) < limit or (self.chunk_count is not None and limit >= self.chunk_count)
            stats.update(chunks_retrieved=len(chunks), unique_documents=len(hits),
                         total_chunks_received=stats['total_chunks_received'] + len(chunks),
                         exhausted=exhausted)
            if len(hits) >= k or exhausted:
                stats['documents_returned'] = min(k, len(hits))
                return hits[:k]
            limit *= 2
            if self.chunk_count is not None:
                limit = min(limit, self.chunk_count)

    def close(self):
        self._runner.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
