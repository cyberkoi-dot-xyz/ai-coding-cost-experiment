# Implementation comparison

Direction: A (one-shot, `b8c61cb`) to B (final test-gated milestone, `43ee859`). These findings come from static source inspection, not execution.

## Shared behavior

Both implementations inject clients, embed queries rather than rebuilding the corpus, use the named `dense` vector, preserve backend order/scores, and translate payloads into retrieved chunks. Both adapters keep the first chunk for each document, retain original chunk rank, record document position, expand retrieval limits until enough documents or exhaustion, and replace earlier rankings on expansion. Injected clients remain caller-owned.

## Meaningful differences

| Area | A: one-shot | B: test-gated |
| --- | --- | --- |
| Query validation | No explicit nonblank-string check | Rejects nonstrings and blank queries before I/O |
| Batch input | No explicit list/type validation | Requires a list and validates each query |
| Batch searches | Sequential awaits | Concurrent searches using `asyncio.gather`; returned result order follows input order |
| Dimension cache | Cached without a lock; boolean size passes the integer check | Lock protects lazy lookup; rejects boolean dimension |
| Embedding indices | Validates only when every index is an integer | If any index exists, requires complete integer indices identifying each input once |
| Filters | Relies more on downstream model validation | Explicit key, membership, operator, and range-bound checks; also recognizes datetime ranges outside `created_at` |
| Adapter filters | Constructor accepts filters and forwards them | Constructor has no filters parameter; always forwards `None` |
| Blank document identity | Empty string falls back; whitespace-only string fails | Whitespace-only identity also falls back to source URL |
| Adapter lifecycle | No explicit closed-state guard | Idempotent close and explicit closed-state checks |
| Failure diagnostics | Counts received chunks after successful identity collapse | Counts received chunks before collapse, so counts remain visible if identity validation fails |
| Configuration attributes | Private collection/model attributes | Public collection/model attributes |

B's stricter validation and lifecycle handling add safeguards. Its concurrent batch searches change request scheduling, and removal of adapter filters changes the available interface. Neither greater length nor additional safeguards establishes a cost or correctness advantage without measured evidence.

## Snapshot size

| File | A lines | B lines |
| --- | ---: | ---: |
| `vector_retriever.py` | 107 | 170 |
| `document_adapter.py` | 79 | 123 |

Counts include comments and blank lines; they are not coding-cost measurements.
