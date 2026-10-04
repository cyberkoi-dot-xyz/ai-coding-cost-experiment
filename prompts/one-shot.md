# A: one-shot

## Original prompt status

Pending: the exact user prompt and any follow-up instructions have not been recovered from the repository. This file is not a reconstructed prompt.

The repository records one implementation commit covering both target files.

## Recovered shared task specification

The following is a verbatim copy of `SPEC.md` from frozen template commit `ef7400092243881f6c5f3464fc99518a8bb00075`. This is shared task context, not evidence of the complete prompt delivered to either arm. The original specification ends inside a Python code block; the outer fence below preserves those bytes as text.

````text
# Retrieval Benchmark Specification

## 1. Goal

Implement a dense retrieval pipeline that searches an existing Qdrant
collection and returns ranked unique documents for evaluation.

The implementation must support:

Query
→ query embedding
→ Qdrant dense retrieval
→ ranked chunks
→ document-level deduplication
→ ranked unique documents

Do not rebuild or re-embed the existing document corpus during retrieval.

---

## 2. Scope

Implement only:

1. `rag/retrieval/vector_retriever.py`
2. `rag/evaluation/document_adapter.py`

Do not modify unrelated ingestion, indexing, metrics, dataset, or application code
unless required to fix an interface compatibility issue.

---

# 3. VectorRetriever

## Interface

Provide:

```python
class VectorRetriever:

    def __init__(
        self,
        qdrant_client,
        embedding_client,
        collection_name: str,
        embedding_model: str,
    ):
        ...

    async def retrieve(
        self,
        query: str,
        top_k: int = 20,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        ...

    async def retrieve_batch(
        self,
        queries: list[str],
        top_k: int = 20,
        filters: dict | None = None,
    ) -> list[list[RetrievedChunk]]:
        ...
````
