"""Query-only dense retrieval from an existing Qdrant collection."""
from datetime import datetime, timezone
from qdrant_client.models import DatetimeRange, FieldCondition, Filter, MatchAny, MatchValue, Range
from rag.types import DocType, RetrievedChunk, RetrieverSource


class VectorRetriever:
    def __init__(self, qdrant_client, embedding_client, collection_name: str, embedding_model: str):
        self._qdrant = qdrant_client
        self._embedding_client = embedding_client
        self._collection_name = collection_name
        self._embedding_model = embedding_model
        self._dimension = None

    async def _get_dimension(self):
        if self._dimension is None:
            collection = await self._qdrant.get_collection(self._collection_name)
            vectors = collection.config.params.vectors
            if not isinstance(vectors, dict) or 'dense' not in vectors:
                raise ValueError('Collection has no named dense vector')
            size = vectors['dense'].size
            if not isinstance(size, int) or size < 1:
                raise ValueError('Dense vector dimension must be positive')
            self._dimension = size
        return self._dimension

    @staticmethod
    def _build_filter(filters):
        if not filters:
            return None
        conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                if key == 'created_at':
                    bounds = {}
                    for operator, bound in value.items():
                        date = datetime.fromisoformat(bound.replace('Z', '+00:00')) if isinstance(bound, str) else bound
                        if date.tzinfo is None:
                            date = date.replace(tzinfo=timezone.utc)
                        bounds[operator] = date
                    interval = DatetimeRange(**bounds)
                else:
                    interval = Range(**value)
                conditions.append(FieldCondition(key=key, range=interval))
            elif isinstance(value, list):
                conditions.append(FieldCondition(key=key, match=MatchAny(any=value)))
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        return Filter(must=conditions)

    @staticmethod
    def _chunks(points):
        chunks = []
        for rank, point in enumerate(points, 1):
            payload = dict(point.payload or {})
            text = payload.pop('text', '') or ''
            raw_type = payload.pop('doc_type', None)
            try:
                doc_type = DocType(raw_type)
            except (ValueError, TypeError):
                doc_type = DocType.UNKNOWN
            values = {key: payload.pop(key, None) for key in
                      ('brand', 'campaign_id', 'channel', 'source_url', 'created_at')}
            chunks.append(RetrievedChunk(id=str(point.id), text=text, score=point.score,
                          rank=rank, source=RetrieverSource.VECTOR, doc_type=doc_type,
                          metadata=payload, **values))
        return chunks

    async def _search(self, vector, top_k, query_filter):
        response = await self._qdrant.query_points(
            collection_name=self._collection_name, query=vector, using='dense',
            query_filter=query_filter, limit=top_k, with_payload=True)
        return self._chunks(response.points)

    async def _embed(self, inputs, count):
        dimension = await self._get_dimension()
        response = await self._embedding_client.embeddings.create(
            model=self._embedding_model, input=inputs, dimensions=dimension)
        if len(response.data) != count:
            raise ValueError(f'Expected {count} query embeddings')
        data = list(response.data)
        if all(isinstance(getattr(item, 'index', None), int) for item in data):
            data.sort(key=lambda item: item.index)
            if [item.index for item in data] != list(range(count)):
                raise ValueError('Invalid query embedding indices')
        vectors = [item.embedding for item in data]
        for vector in vectors:
            if len(vector) != dimension:
                raise ValueError(f'Expected {dimension} embedding dimensions, got {len(vector)}')
        return vectors

    async def retrieve(self, query: str, top_k: int = 20, filters: dict | None = None) -> list[RetrievedChunk]:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError('top_k must be a positive integer')
        query_filter = self._build_filter(filters)
        vectors = await self._embed(query, 1)
        return await self._search(vectors[0], top_k, query_filter)

    async def retrieve_batch(self, queries: list[str], top_k: int = 20,
                             filters: dict | None = None) -> list[list[RetrievedChunk]]:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError('top_k must be a positive integer')
        if not queries:
            return []
        query_filter = self._build_filter(filters)
        vectors = await self._embed(queries, len(queries))
        return [await self._search(vector, top_k, query_filter) for vector in vectors]
