# Experiment Workflows

Both experiment arms used the same retrieval implementation specification, preserved in [shared-specification.md](shared-specification.md). The experimental difference was how implementation work was staged.

The staging below describes the experiment as reported by the author. The recorded commit identifiers substantiate the component split; the original Git history and gate logs are not included in this export.

## A: One-shot

The implementation was completed as a single implementation stage covering:

1. VectorRetriever
2. DocumentRetrievalAdapter

This was followed by testing/debugging and the final acceptance suite.

The repository records one implementation commit covering both target files: `b8c61cb9d8886d7849054c0f3205769419905845`.

## B: Test-gated

The implementation was divided into separate milestones:

1. Implement VectorRetriever.
2. Run tests / gate, then checkpoint.
3. Implement DocumentRetrievalAdapter.
4. Run tests / gate, then checkpoint.
5. Run the final integration suite.

The repository records separate implementation commits for the two components: `4676a15` for VectorRetriever and `43ee859` for DocumentRetrievalAdapter. These establish separate implementation milestones; they do not independently verify gate execution or outcomes.

## Prompt provenance

The exact original user prompts, gate instructions, and follow-up instructions were not preserved. Therefore this repository does not attempt to reconstruct them. Exact gate commands, pass criteria, retry history, and underlying test logs are unavailable.

The shared specification is preserved verbatim from frozen experiment template `ef7400092243881f6c5f3464fc99518a8bb00075`.
