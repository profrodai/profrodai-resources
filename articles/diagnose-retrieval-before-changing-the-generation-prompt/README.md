# Find the failing RAG stage before you change the prompt

The measured run behind https://profrod.ai/articles/diagnose-retrieval-before-changing-the-generation-prompt.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/profrodai-resources/blob/main/articles/diagnose-retrieval-before-changing-the-generation-prompt/retrieval_v1.ipynb)

Everything here runs on small open models, with no API key.

## What was run (2026-10-01)

**Data:** BEIR's SciFact, with 300 test claims and 5,183 abstracts. It is downloaded at run time and checked against the md5 in BEIR's README (`5f7d1de6…`). The dataset itself is not committed; the results keep only ids.

**The stages:**
1. **Retrieval, top 100:** BM25 (standard library, k1 = 0.9, b = 0.4) or `all-MiniLM-L6-v2` embeddings.
2. **Reranking to 10:** none (the retriever's own top 10) or the cross-encoder `ms-marco-MiniLM-L-6-v2`.
3. **Prompt assembly:** whole abstracts from the top 5, in order, within 1,024 tokens.
4. **Generation:** Qwen2.5-1.5B-Instruct, greedy, names the abstract that bears on the claim.

Every claim is attributed to the first stage that lost all of its relevant abstracts (`retrieval_stats_v1.diagnose`).

| Pipeline | Correct | Lost: retrieval | Reranking | Prompt assembly | Generation |
|---|---|---|---|---|---|
| BM25 | 99 | 31 | 29 | 45 | 96 |
| BM25 + cross-encoder | 107 | 31 | 29 | 38 | 95 |
| MiniLM | 84 | 22 | 38 | 43 | 113 |
| MiniLM + cross-encoder | 107 | 22 | 31 | 40 | 100 |
| MiniLM + cross-encoder, revised prompt | 151 | 22 | 31 | 40 | 56 |

**Generation was the largest loss in every pipeline:** with the relevant abstract in its prompt, the model answered NONE.

**The follow-up:** a revised generation prompt, run on the saved prompts so that nothing upstream could change, lifted correct answers from 107 to 151. That is 49 claims gained against 5 lost, McNemar p = 4 × 10⁻¹⁰. The 93 claims lost upstream did not move.

Two caveats:
- The revised prompt was written after seeing the first run, on the same claims, so the gain is optimistic.
- Every SciFact test claim has a relevant abstract, which favors a prompt that rarely answers NONE.

## Files

- `retrieval_run_v1.py` has four commands: `all` (with `--limit N` for a quick rerun), `variant` (the revised prompt), `summarize` and `revisions`.
- `retrieval_stats_v1.py` and `test_retrieval_v1.py` hold stage attribution, the Wilson interval and the exact McNemar test. The tests include the article's five-case fixture.
- `results/queries-v1.jsonl` has every claim's retrieved, reranked and prompted ids and each pipeline's answer. `results/variant-v1.jsonl` has the revised prompt's answers, and `results/summary-v1.json` has every number above.
- `receipts/retrieval-v1.json` records the data md5, models and revisions, package versions, settings, the follow-up and its disclosure, and the $0 cost.
- `retrieval_v1.ipynb` recomputes the numbers, then reruns 60 claims on Colab.
