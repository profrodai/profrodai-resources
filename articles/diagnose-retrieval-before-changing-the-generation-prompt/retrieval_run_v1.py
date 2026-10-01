# Prof Rod | Find the Failing RAG Stage Before You Change the Prompt
# Article: https://profrod.ai/articles/diagnose-retrieval-before-changing-the-generation-prompt
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Run a four-stage research assistant on BEIR's SciFact and attribute every miss to the first
stage that lost the evidence: retrieval, reranking, prompt assembly or generation.

Data: SciFact from BEIR (300 test claims, 5,183 abstracts), downloaded from the URL in BEIR's
README and checked against its md5. Nothing from the dataset is committed here; the results keep
only document ids.

Stages, each with a small open model that runs on a free Colab runtime:
1. retrieval, top 100 per claim: BM25 (implemented below, standard library) or dense embeddings
   with sentence-transformers/all-MiniLM-L6-v2, the model Chapter 6 measures;
2. reranking, to 10: either none (the retriever's own top 10) or the cross-encoder
   cross-encoder/ms-marco-MiniLM-L-6-v2 over the 100;
3. prompt assembly: the top 5, whole abstracts in rank order, until a 1,024-token budget (counted
   with the generator's tokenizer) would be exceeded;
4. generation: Qwen2.5-1.5B-Instruct, greedy, asked which abstract (by id) bears on the claim.
   Correct if it names a relevant id.

    uv run --no-project --python 3.12 --with sentence-transformers --with 'transformers==5.18.0' --with torch \\
        python retrieval_run_v1.py all
    uv run --no-project --python 3.12 python retrieval_run_v1.py summarize
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import platform
import re
import sys
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import retrieval_stats_v1 as S  # noqa: E402

DATA_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
DATA_MD5 = "5f7d1de60b170fc8027bb7898e2efca1"
DATA = HERE / "data" / "scifact"
RESULTS = HERE / "results"
RECEIPT = HERE / "receipts" / "retrieval-v1.json"
EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GENERATOR = "Qwen/Qwen2.5-1.5B-Instruct"
MODELS = [EMBEDDER, RERANKER, GENERATOR]
REVISIONS: dict[str, str] = json.loads((HERE / "revisions-v1.json").read_text()) if (HERE / "revisions-v1.json").exists() else {}
TOP_RETRIEVE, TOP_RERANK, TOP_PROMPT, BUDGET = 100, 10, 5, 1024
PIPELINES = [("bm25", "none"), ("bm25", "cross-encoder"), ("dense", "none"), ("dense", "cross-encoder")]
ANSWER = re.compile(r"ID:\s*(\d+|NONE)", re.I)


# ------------------------------------------------------------------ data

def fetch() -> None:
    if (DATA / "corpus.jsonl").exists():
        return
    raw = urllib.request.urlopen(DATA_URL, timeout=120).read()
    digest = hashlib.md5(raw).hexdigest()
    if digest != DATA_MD5:
        raise SystemExit(f"scifact.zip md5 {digest} does not match BEIR's {DATA_MD5}")
    DATA.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extractall(DATA.parent)
    print(f"scifact.zip: md5 {digest} matches", flush=True)


def load() -> tuple[dict, dict, dict]:
    corpus = {}
    for line in (DATA / "corpus.jsonl").read_text().splitlines():
        d = json.loads(line)
        corpus[d["_id"]] = {"title": d.get("title", ""), "text": d["text"]}
    queries = {json.loads(x)["_id"]: json.loads(x)["text"] for x in (DATA / "queries.jsonl").read_text().splitlines()}
    qrels: dict[str, set[str]] = {}
    for row in (DATA / "qrels" / "test.tsv").read_text().splitlines()[1:]:
        q, d, score = row.split("\t")
        if int(score) > 0:
            qrels.setdefault(q, set()).add(d)
    queries = {q: queries[q] for q in sorted(qrels, key=int)}
    return corpus, queries, qrels


# ------------------------------------------------------------------ stage 1: retrieval

TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def bm25(corpus: dict, queries: dict, k1: float = 0.9, b: float = 0.4) -> dict[str, list[str]]:
    """BM25 with Lucene's idf, over title + abstract; the k1 and b Pyserini uses for BEIR."""
    ids = list(corpus)
    docs = [Counter(tokens(corpus[i]["title"] + " " + corpus[i]["text"])) for i in ids]
    lengths = [sum(d.values()) for d in docs]
    avg = sum(lengths) / len(lengths)
    df: Counter = Counter()
    for d in docs:
        df.update(d.keys())
    n = len(docs)
    idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
    postings: dict[str, list[tuple[int, int]]] = {}
    for j, d in enumerate(docs):
        for t, f in d.items():
            postings.setdefault(t, []).append((j, f))
    out = {}
    for q, text in queries.items():
        scores: dict[int, float] = {}
        for t in set(tokens(text)):
            for j, f in postings.get(t, []):
                scores[j] = scores.get(j, 0.0) + idf[t] * f * (k1 + 1) / (f + k1 * (1 - b + b * lengths[j] / avg))
        out[q] = [ids[j] for j, _ in sorted(scores.items(), key=lambda kv: (-kv[1], ids[kv[0]]))[:TOP_RETRIEVE]]
    return out


def dense(corpus: dict, queries: dict, device: str) -> dict[str, list[str]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDER, revision=REVISIONS.get(EMBEDDER), device=device)
    ids = list(corpus)
    docs = model.encode([corpus[i]["title"] + ". " + corpus[i]["text"] for i in ids], batch_size=64, normalize_embeddings=True, convert_to_tensor=True)
    qs = list(queries)
    qv = model.encode([queries[q] for q in qs], batch_size=64, normalize_embeddings=True, convert_to_tensor=True)
    top = (qv @ docs.T).topk(TOP_RETRIEVE, dim=1).indices.tolist()
    return {q: [ids[j] for j in row] for q, row in zip(qs, top)}


# ------------------------------------------------------------------ stage 2: reranking

def rerank(corpus: dict, queries: dict, lists: dict[str, list[str]], device: str) -> dict[str, list[str]]:
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(RERANKER, revision=REVISIONS.get(RERANKER), device=device)
    out = {}
    for q, cands in lists.items():
        scores = model.predict([(queries[q], corpus[d]["title"] + ". " + corpus[d]["text"]) for d in cands], batch_size=100)
        order = sorted(range(len(cands)), key=lambda i: (-float(scores[i]), i))
        out[q] = [cands[i] for i in order[:TOP_RERANK]]
    return out


# ------------------------------------------------------------------ stages 3 and 4: assembly, generation

def assemble(corpus: dict, ranked: list[str], tok) -> list[str]:
    """Whole abstracts from the top 5, in rank order, until the next one would exceed the budget."""
    kept, used = [], 0
    for d in ranked[:TOP_PROMPT]:
        n = len(tok(passage(corpus, d))["input_ids"])
        if used + n > BUDGET:
            break
        kept.append(d)
        used += n
    return kept


def passage(corpus: dict, d: str) -> str:
    return f"[ID {d}] {corpus[d]['title']}. {corpus[d]['text']}"


ASK = {
    # The prompt the four pipelines ran with.
    "original": "Which abstract, by ID, gives evidence for or against the claim? Reply with one line: ID: <number>, or ID: NONE if no abstract bears on it.",
    # The follow-up: once attribution points at generation, change only the generation prompt.
    "revised": "One of these abstracts may study the same question as the claim, even if it does not settle it. Which abstract, by ID, "
               "is most relevant to the claim? Reply with one line: ID: <number>. Reply ID: NONE only if no abstract is about the same topic.",
}


def prompt(claim: str, corpus: dict, kept: list[str], style: str = "original") -> list[dict]:
    abstracts = "\n\n".join(passage(corpus, d) for d in kept) or "(no abstracts)"
    return [
        {"role": "system", "content": "You help a researcher check scientific claims against abstracts."},
        {"role": "user", "content": f"Claim: {claim}\n\nAbstracts:\n{abstracts}\n\n{ASK[style]}"},
    ]


def generate(corpus: dict, queries: dict, assembled: dict, device: str, batch: int = 16, style: str = "original") -> dict:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(GENERATOR, revision=REVISIONS.get(GENERATOR))
    tok.padding_side = "left"
    dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
    model = AutoModelForCausalLM.from_pretrained(GENERATOR, revision=REVISIONS.get(GENERATOR), dtype=dtype).to(device).eval()
    jobs = [(key, q) for key in assembled for q in queries]
    out: dict = {}
    for i in range(0, len(jobs), batch):
        chunk = jobs[i : i + batch]
        texts = [tok.apply_chat_template(prompt(queries[q], corpus, assembled[key][q], style), add_generation_prompt=True, tokenize=False) for key, q in chunk]
        enc = tok(texts, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=16, do_sample=False, pad_token_id=tok.pad_token_id)
        for (key, q), row in zip(chunk, gen):
            reply = tok.decode(row[enc["input_ids"].shape[1]:], skip_special_tokens=True)
            m = ANSWER.search(reply)
            out.setdefault(key, {})[q] = {"reply": reply.strip(), "id": m.group(1).upper() if m else "UNPARSED"}
        print(f"  generate {min(i + batch, len(jobs))}/{len(jobs)}", flush=True)
    return out


# ------------------------------------------------------------------ the run

def device_name() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


def run_all(limit: int | None = None) -> None:
    from transformers import AutoTokenizer

    fetch()
    corpus, queries, qrels = load()
    if limit:
        queries = dict(list(queries.items())[:limit])
    device = device_name()
    print(f"{len(queries)} claims, {len(corpus)} abstracts, device {device}", flush=True)
    t0 = time.time()
    retrieved = {"bm25": bm25(corpus, queries), "dense": dense(corpus, queries, device)}
    print(f"  retrieval {time.time() - t0:.0f}s", flush=True)
    ranked = {}
    for r, rr in PIPELINES:
        key = f"{r}+{rr}"
        ranked[key] = {q: lst[:TOP_RERANK] for q, lst in retrieved[r].items()} if rr == "none" else rerank(corpus, queries, retrieved[r], device)
    print(f"  reranking {time.time() - t0:.0f}s", flush=True)
    tok = AutoTokenizer.from_pretrained(GENERATOR, revision=REVISIONS.get(GENERATOR))
    assembled = {key: {q: assemble(corpus, ranked[key][q], tok) for q in queries} for key in ranked}
    answers = generate(corpus, queries, assembled, device)
    print(f"  generation {time.time() - t0:.0f}s", flush=True)
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS / "queries-v1.jsonl").open("w") as fh:
        for q in queries:
            row = {"query": q, "relevant": sorted(qrels[q]), "retrieved": {r: retrieved[r][q] for r in retrieved}}
            for key in ranked:
                row[key] = {"reranked": ranked[key][q], "prompt": assembled[key][q], **answers[key][q]}
            fh.write(json.dumps(row) + "\n")
    receipt(device, time.time() - t0)


VARIANT_PIPELINE = "dense+cross-encoder"


def run_variant() -> None:
    """The revised generation prompt on the saved prompts of one pipeline: retrieval, reranking and
    assembly are reused exactly, so only generation can change."""
    corpus, queries, _ = load()
    rows = [json.loads(x) for x in (RESULTS / "queries-v1.jsonl").read_text().splitlines()]
    assembled = {VARIANT_PIPELINE: {r["query"]: r[VARIANT_PIPELINE]["prompt"] for r in rows}}
    answers = generate(corpus, queries, assembled, device_name(), style="revised")[VARIANT_PIPELINE]
    with (RESULTS / "variant-v1.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps({"query": r["query"], "pipeline": VARIANT_PIPELINE, "style": "revised", **answers[r["query"]]}) + "\n")


def summarize() -> dict:
    rows = [json.loads(x) for x in (RESULTS / "queries-v1.jsonl").read_text().splitlines()]
    n = len(rows)
    out: dict = {"queries": n, "pipelines": {}, "comparisons": {}}
    stages = ["retrieval", "reranking", "prompt_assembly", "generation", "none"]
    verdicts: dict[str, list[str]] = {}
    for r, rr in PIPELINES:
        key = f"{r}+{rr}"
        labels = [S.diagnose({"retrieved": row["retrieved"][r], "reranked": row[key]["reranked"], "prompt": row[key]["prompt"],
                              "correct": row[key]["id"] in row["relevant"]}, set(row["relevant"])) for row in rows]
        verdicts[key] = labels
        counts = Counter(labels)
        recall = {k: sum(any(d in row["relevant"] for d in row["retrieved"][r][:k]) for row in rows) for k in (1, 5, 10, 100)}
        out["pipelines"][key] = {
            "stages": {s: {"k": counts.get(s, 0), "share": counts.get(s, 0) / n, "wilson95": S.wilson(counts.get(s, 0), n)} for s in stages},
            "correct": counts.get("none", 0),
            "retrieverHitAt": {str(k): {"k": v, "wilson95": S.wilson(v, n)} for k, v in recall.items()},
            "inTop10": sum(any(d in row["relevant"] for d in row[key]["reranked"]) for row in rows),
            "inPrompt": sum(any(d in row["relevant"] for d in row[key]["prompt"]) for row in rows),
            "promptAbstracts": sum(len(row[key]["prompt"]) for row in rows) / n,
            "answeredNone": sum(row[key]["id"] == "NONE" for row in rows),
            "unparsed": sum(row[key]["id"] == "UNPARSED" for row in rows),
            "generationGivenInPrompt": {"k": sum(row[key]["id"] in row["relevant"] for row in rows if any(d in row["relevant"] for d in row[key]["prompt"])),
                                        "n": sum(any(d in row["relevant"] for d in row[key]["prompt"]) for row in rows)},
        }
    for a, b in (("bm25+none", "bm25+cross-encoder"), ("dense+none", "dense+cross-encoder"), ("bm25+cross-encoder", "dense+cross-encoder"), ("bm25+none", "dense+none")):
        ok_a = [v == "none" for v in verdicts[a]]
        ok_b = [v == "none" for v in verdicts[b]]
        only_a = sum(x and not y for x, y in zip(ok_a, ok_b))
        only_b = sum(y and not x for x, y in zip(ok_a, ok_b))
        out["comparisons"][f"{a} vs {b}"] = {"onlyFirst": only_a, "onlySecond": only_b, "mcnemarP": S.mcnemar_exact(only_a, only_b)}
    variant = RESULTS / "variant-v1.jsonl"
    if variant.exists():
        revised = {json.loads(x)["query"]: json.loads(x) for x in variant.read_text().splitlines()}
        key = VARIANT_PIPELINE
        labels = [S.diagnose({"retrieved": row["retrieved"][key.split("+")[0]], "reranked": row[key]["reranked"], "prompt": row[key]["prompt"],
                              "correct": revised[row["query"]]["id"] in row["relevant"]}, set(row["relevant"])) for row in rows]
        counts = Counter(labels)
        ok_new = [v == "none" for v in labels]
        ok_old = [v == "none" for v in verdicts[key]]
        only_old = sum(a and not b for a, b in zip(ok_old, ok_new))
        only_new = sum(b and not a for a, b in zip(ok_old, ok_new))
        out["revisedPrompt"] = {
            "pipeline": key, "prompt": ASK["revised"],
            "stages": {s: {"k": counts.get(s, 0), "wilson95": S.wilson(counts.get(s, 0), n)} for s in stages},
            "answeredNone": sum(revised[row["query"]]["id"] == "NONE" for row in rows),
            "generationGivenInPrompt": {"k": sum(revised[row["query"]]["id"] in row["relevant"] for row in rows if any(d in row["relevant"] for d in row[key]["prompt"])),
                                        "n": out["pipelines"][key]["generationGivenInPrompt"]["n"]},
            "vsOriginal": {"onlyOriginal": only_old, "onlyRevised": only_new, "mcnemarP": S.mcnemar_exact(only_old, only_new)},
        }
    (RESULTS / "summary-v1.json").write_text(json.dumps(out, indent=1) + "\n")
    return out


def receipt(device: str, seconds: float) -> None:
    import importlib.metadata as md

    rec = {
        "experiment": "diagnose-retrieval-before-changing-the-generation-prompt v1",
        "ranOn": time.strftime("%Y-%m-%d"),
        "where": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
        "device": device,
        "data": {"url": DATA_URL, "md5": DATA_MD5},
        "packages": {p: md.version(p) for p in ("transformers", "torch", "sentence-transformers")},
        "models": {m: REVISIONS.get(m) for m in MODELS},
        "settings": {"topRetrieve": TOP_RETRIEVE, "topRerank": TOP_RERANK, "topPrompt": TOP_PROMPT, "promptBudgetTokens": BUDGET,
                     "bm25": {"k1": 0.9, "b": 0.4}, "generation": "greedy, 16 new tokens"},
        "wallSeconds": round(seconds),
        "costUsd": 0.0,
        "note": "Open weights run locally; no API was called. The dataset is downloaded at run time and not committed.",
    }
    RECEIPT.parent.mkdir(exist_ok=True)
    RECEIPT.write_text(json.dumps(rec, indent=2) + "\n")


def revisions() -> None:
    from huggingface_hub import HfApi

    revs = {m: HfApi().model_info(m).sha for m in MODELS}
    (HERE / "revisions-v1.json").write_text(json.dumps(revs, indent=2) + "\n")
    print(json.dumps(revs, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["all", "variant", "summarize", "revisions"])
    ap.add_argument("--limit", type=int, help="only the first N claims, for a quick rerun")
    args = ap.parse_args()
    if args.cmd == "all":
        run_all(args.limit)
    elif args.cmd == "variant":
        run_variant()
    elif args.cmd == "summarize":
        print(json.dumps(summarize(), indent=1)[:3000])
    else:
        revisions()


if __name__ == "__main__":
    main()
