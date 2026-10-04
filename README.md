# AI coding cost experiment

This repository contains code snapshots and workflow documentation from the experiment described in the CyberKoi article. It is intended for implementation comparison rather than as a standalone runnable application.

**Draft status:** the article URL is pending. The exact original prompts and gate instructions were not preserved and are not reconstructed. See [the experiment workflows](experiment/workflow.md) and [the recovered shared specification](experiment/shared-specification.md).

## Hypothesis

Proposed hypothesis, pending confirmation against the article: structuring the same coding task into test-gated milestones can reduce total AI coding cost while maintaining correctness compared with a one-shot task. Code differences alone cannot establish this claim.

## Workflows and provenance

Both workflows used the same full specification and differed in how implementation work was staged. Both begin with frozen template `ef7400092243881f6c5f3464fc99518a8bb00075`, whose two target modules are stubs.

- **A, one-shot:** `b8c61cb9d8886d7849054c0f3205769419905845` changes both target modules in one commit. See [the one-shot workflow](experiment/workflow.md#a-one-shot).
- **B, test-gated:** milestone 1 `4676a15` changes the vector retriever; milestone 2 `43ee859` changes the document adapter. The exported B files are the final milestone snapshot. See [the test-gated workflow](experiment/workflow.md#b-test-gated). Exact prompts, gate commands, retry history, and underlying gate logs remain unavailable; the final acceptance-test totals below are author-reported.

The four Python files are byte-for-byte exports of their original Git blobs. They reference interfaces and third-party packages from the original application, which are deliberately omitted. No imports or behavior were changed for this comparison. Original Git history is not included.

## Reading the comparison

Read [the implementation findings](comparison/findings.md), then inspect [the unified diff](comparison/implementation.diff), directed from A to B. The snapshots are under `implementations/one-shot/` and `implementations/test-gated/`. To regenerate the diff without executing either implementation:

```sh
python3 - <<'PY'
from pathlib import Path
from difflib import unified_diff
for name in ('vector_retriever.py', 'document_adapter.py'):
    a = Path('implementations/one-shot') / name
    b = Path('implementations/test-gated') / name
    print(''.join(unified_diff(a.read_text().splitlines(True),
                              b.read_text().splitlines(True),
                              fromfile=str(a), tofile=str(b))), end='')
PY
```

This regenerates the published comparison; it does not reproduce the original model sessions or run retrieval.

## Measured results

The following measurements were supplied by the experiment author from the CyberKoi article:

| Measurement | One-shot | Test-gated |
| --- | ---: | ---: |
| Estimated token cost | $0.326 | $0.256 |
| Input tokens | 832,953 | 694,156 |
| Non-cached input tokens | 48,313 | 36,108 |
| Output tokens | 7,199 | 5,244 |
| Execution time | ~12m34s | ~6m13s |
| Acceptance tests | 57/57 | 57/57 |

These are **estimated token-based costs, not actual ChatGPT subscription charges**. Non-cached input tokens are a subset of total input tokens. The measurements and acceptance-test results are author-reported; the underlying usage records, pricing calculation, timing records, and test logs are not included in this repository and were not independently verified during export.

Existing retrieval reports predate these implementation commits in the frozen template and are not evidence of A/B coding performance. They are excluded from this export.

## Limitations

This is one pair of code snapshots. Static inspection identifies behavioral differences but does not independently verify the reported measurements or establish that task structure caused a difference. Gate execution and complete model-session context cannot be inferred from commit names. Dependencies, tests, datasets, local indexes, and application modules are outside this comparison's scope.

## License

MIT, copyright 2026 CyberKoi. See [LICENSE](LICENSE).

## CyberKoi article

**Article URL placeholder:** `[CyberKoi article](PRODUCTION_ARTICLE_URL_PENDING)` — replace with the production URL after the article is published.
