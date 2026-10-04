"""Dense query retrieval against an existing Qdrant collection."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from qdrant_client.models import (
    DatetimeRange, FieldCondition, Filter, MatchAny, MatchValue, Range,
)

from rag.types import DocType, RetrievedChunk, RetrieverSource


class VectorRetriever:
    """Embed only incoming queries; preserve Qdrant's ranking and raw scores."""

    def __init__(
        self, qdrant_client, embedding_client,
        collection_name: str, embedding_model: str,
    ):
        self._qdrant = qdrant_client
        self._embedding_client = embedding_client
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self._dimension: int | None = None
        self._dimension_lock = asyncio.Lock()

    async def retrieve(
        self, query: str, top_k: int = 20, filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        self._validate_k(top_k)
        self._validate_query(query)
        query_filter = self._build_filter(filters)
        dimension = await self._get_dimension()
        response = await self._embedding_client.embeddings.create(
            model=self.embedding_model, input=query, dimensions=dimension,
        )
        vectors = self._embedding_vectors(response, 1, dimension)
        return await self._search(vectors[0], top_k, query_filter)

    async def retrieve_batch(
        self, queries: list[str], top_k: int = 20, filters: dict | None = None,
    ) -> list[list[RetrievedChunk]]:
        self._validate_k(top_k)
        if not isinstance(queries, list):
            raise ValueError("queries must be a list of strings")
        for query in queries:
            self._validate_query(query)
        query_filter = self._build_filter(filters)
        if not queries:
            return []
        dimension = await self._get_dimension()
        response = await self._embedding_client.embeddings.create(
            model=self.embedding_model, input=queries, dimensions=dimension,
        )
        # Validate every vector before starting any searches.
        vectors = self._embedding_vectors(response, len(queries), dimension)
        return await asyncio.gather(*(
            self._search(vector, top_k, query_filter) for vector in vectors
        ))

    @staticmethod
    def _validate_k(top_k):
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")

    @staticmethod
    def _validate_query(query):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

    async def _get_dimension(self) -> int:
        async with self._dimension_lock:
            if self._dimension is None:
                collection = await self._qdrant.get_collection(self.collection_name)
                vectors = collection.config.params.vectors
                if not isinstance(vectors, dict) or "dense" not in vectors:
                    raise ValueError("Collection has no named dense vector")
                dimension = vectors["dense"].size
                if (isinstance(dimension, bool)
                        or not isinstance(dimension, int) or dimension < 1):
                    raise ValueError("Dense vector dimension must be a positive integer")
                self._dimension = dimension
            return self._dimension

    @staticmethod
    def _embedding_vectors(response, count, dimension):
        entries = list(response.data)
        if len(entries) != count:
            raise ValueError(f"Expected {count} query embeddings, got {len(entries)}")
        # OpenAI supplies indices; lightweight injected clients may omit them.
        indices = [getattr(entry, "index", None) for entry in entries]
        if any(index is not None for index in indices):
            if any(type(index) is not int for index in indices) or sorted(indices) != list(range(count)):
                raise ValueError("Embedding indices must identify each input query once")
            entries.sort(key=lambda entry: entry.index)
        vectors = [entry.embedding for entry in entries]
        for vector in vectors:
            if len(vector) != dimension:
                raise ValueError(
                    f"Expected {dimension} embedding dimensions, got {len(vector)}"
                )
        return vectors

    async def _search(self, vector, top_k, query_filter):
        response = await self._qdrant.query_points(
            collection_name=self.collection_name, query=vector, using="dense",
            query_filter=query_filter, limit=top_k, with_payload=True,
        )
        return [self._to_chunk(point, rank)
                for rank, point in enumerate(response.points, start=1)]

    @staticmethod
    def _build_filter(filters: dict | None) -> Filter | None:
        if filters is None:
            return None
        if not isinstance(filters, dict):
            raise ValueError("filters must be a dictionary")
        conditions = []
        for key, value in filters.items():
            if not isinstance(key, str) or not key:
                raise ValueError("Filter keys must be non-empty strings")
            if isinstance(value, (str, bool, int)):
                condition = FieldCondition(key=key, match=MatchValue(value=value))
            elif isinstance(value, list):
                if not value or not (
                    all(isinstance(item, str) for item in value)
                    or all(type(item) is int for item in value)
                ):
                    raise ValueError("Membership filters require strings or integers of one type")
                condition = FieldCondition(key=key, match=MatchAny(any=value))
            elif isinstance(value, dict):
                if not value or set(value) - {"gt", "gte", "lt", "lte"}:
                    raise ValueError("Range filters support only gt, gte, lt, and lte")
                if key == "created_at" or all(isinstance(bound, (str, datetime)) for bound in value.values()):
                    bounds = {}
                    for operator, bound in value.items():
                        if isinstance(bound, str):
                            bound = datetime.fromisoformat(bound.replace("Z", "+00:00"))
                        if not isinstance(bound, datetime):
                            raise ValueError("Datetime range bounds must be ISO dates or datetimes")
                        bounds[operator] = bound if bound.tzinfo else bound.replace(tzinfo=timezone.utc)
                    range_value = DatetimeRange(**bounds)
                else:
                    if not all(type(bound) in (int, float) for bound in value.values()):
                        raise ValueError("Numeric range bounds must be numbers")
                    range_value = Range(**value)
                condition = FieldCondition(key=key, range=range_value)
            else:
                raise ValueError(f"Unsupported filter value for {key}")
            conditions.append(condition)
        return Filter(must=conditions) if conditions else None

    @staticmethod
    def _to_chunk(point, rank: int) -> RetrievedChunk:
        payload = dict(point.payload or {})
        doc_type = payload.pop("doc_type", DocType.UNKNOWN)
        try:
            doc_type = DocType(doc_type)
        except (ValueError, TypeError):
            doc_type = DocType.UNKNOWN
        fields = {key: payload.pop(key, None) for key in (
            "brand", "campaign_id", "channel", "source_url", "created_at",
        )}
        return RetrievedChunk(
            id=str(point.id), text=payload.pop("text", "") or "",
            score=point.score, rank=rank, source=RetrieverSource.VECTOR,
            doc_type=doc_type, metadata=payload, **fields,
        )
