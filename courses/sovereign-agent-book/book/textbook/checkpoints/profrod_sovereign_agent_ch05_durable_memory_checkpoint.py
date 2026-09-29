# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 5: persistence, correction, and forgetting that changes future context."""

import argparse
import copy
import json
import math
import runpy
import tempfile
from pathlib import Path


class ObservedModel:
    def __init__(self, model):
        self.model = model
        self.first_messages = None

    def complete(self, messages, tools, **kwargs):
        if self.first_messages is None:
            self.first_messages = copy.deepcopy(messages)
        return self.model.complete(messages, tools, **kwargs)


BOOK = Path(__file__).resolve().parents[1]
RETRIEVAL = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch05_retrieval_learner.py"))
MEMORY = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch05_memory_learner.py"))
open_memory, remember, forget = MEMORY["open_memory"], MEMORY["remember"], MEMORY["forget"]
preferences, context = MEMORY["preferences"], MEMORY["context"]
record_result, memory_revision = MEMORY["record_result"], MEMORY["memory_revision"]


def retrieval():
    """Part A's retrieval functions, each checked against an independent computation."""
    bm25 = RETRIEVAL["bm25_scores"]
    # "a" appears once, in one of three equal-length records: the score is idf alone.
    scores = bm25("a", ["a b", "b c", "c d"])
    assert math.isclose(scores[0], math.log(1 + 2.5 / 1.5)) and scores[1:] == [0.0, 0.0]
    repeated = bm25("a", ["a " * 200, "b", "c", "d"])[0]
    assert repeated < math.log(1 + 3.5 / 1.5) * 2.5
    print("ok   BM25 equals idf for a single occurrence, and saturates below idf (k1 + 1)")

    ranked, relevant = [4, 1, 7, 2], {1, 2}
    assert RETRIEVAL["precision_at_k"](ranked, relevant, 2) == 0.5
    assert RETRIEVAL["recall_at_k"](ranked, relevant, 3) == 0.5
    assert RETRIEVAL["reciprocal_rank"](ranked, relevant) == 0.5
    assert RETRIEVAL["reciprocal_rank"](ranked, {9}) == 0.0
    print("ok   precision@k, recall@k and reciprocal rank by their definitions")

    assert math.isclose(RETRIEVAL["cosine"]([1, 2, 3], [3, 6, 9]), 1.0)
    assert math.isclose(RETRIEVAL["cosine"]([1, 0], [0, 5]), 0.0)
    records = ["x" * 50, "y" * 30, "z" * 30, "w" * 10]
    chosen = RETRIEVAL["pack_context"](records, [4, 3, 2, 1], 70, len)
    assert chosen == [0, 3] and sum(len(records[i]) for i in chosen) <= 70
    print("ok   cosine ignores length; the packer keeps the budget and skips what does not fit")

    lab = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py")
    )
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch05/ch05-retrieval-receipt-v1.json").read_text()
    )
    fresh = lab["evaluate_ranker"]("bm25", RETRIEVAL["bm25_scores"])
    assert fresh == receipt["rankers"][0]
    print("ok   the receipt's BM25 recall@3 and MRR recompute exactly:", fresh["recall_at_3"])


def boundaries(folder):
    """The memory rules the chapter states, each on the learner's functions."""
    db = open_memory(Path(folder) / "boundaries.sqlite")
    try:
        # Capacity: a hundred active names, then only corrections of existing names.
        for i in range(100):
            remember(db, "cap", f"n{i}", "v", f"cap/{i}")
        try:
            remember(db, "cap", "n100", "v", "cap/100")
            raise AssertionError("a 101st preference name was accepted")
        except ValueError:
            pass
        remember(db, "cap", "n0", "corrected", "cap/101")
        assert preferences(db, "cap", "n0", maximum=1)[0]["value"] == "corrected"

        # Sessions are separate, and a failed forget changes nothing.
        remember(db, "lucy", "supplier", "Ask for afternoon delivery", "lucy/message/2")
        remember(db, "other", "supplier", "Another operator's supplier", "other/message/1")
        assert "Another operator" not in context(db, "lucy", "supplier", allowed=frozenset())[0][
            "content"
        ]
        before = memory_revision(db, "lucy")
        try:
            with db.immediate() as connection:
                connection.execute("DELETE FROM assistant_preferences WHERE session='lucy'")
                raise RuntimeError("failure before the revision advances")
        except RuntimeError:
            pass
        assert preferences(db, "lucy")[0]["value"] == "Ask for afternoon delivery"
        assert memory_revision(db, "lucy") == before

        # A turn that began before forgetting finishes late; its result stays out.
        forget(db, "lucy", "supplier")
        record_result(db, "lucy", "Earlier request", "afternoon delivery, late", before)
        late = context(db, "lucy", "delivery", allowed=frozenset())[0]["content"]
        assert "afternoon delivery" not in late
    finally:
        db.close()
    print("ok   memory: capacity, separate sessions, failed forget rolls back, late turn excluded")


def main():
    retrieval()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--transcript", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="lucy-memory-") as temporary:
        boundaries(temporary)
        path = Path(temporary) / "agent.sqlite"
        db = open_memory(path)
        remember(db, "lucy", "supplier", "Ask for morning delivery", "lucy/message/1")
        db.close()
        db = open_memory(path)
        retained = preferences(db, "lucy", "delivery")[0]
        assert retained["source"] == "lucy/message/1"
        print("After reopening:", retained["value"])
        remember(db, "lucy", "supplier", "Ask for afternoon delivery", "lucy/message/2")
        print("After correction:", preferences(db, "lucy", "delivery")[0]["value"])
        remember(db, "lucy", "format", "three bullets", "lucy/message/3")
        earlier = memory_revision(db, "lucy")
        record_result(db, "lucy", "Prepare a brief", "Lucy asks for afternoon delivery.", earlier)
        forget(db, "lucy", "supplier")
        selected = context(db, "lucy", "Prepare replenishment drafts.", allowed=frozenset())
        assert "afternoon delivery" not in selected[0]["content"]
        assert "three bullets" in selected[0]["content"]
        print("Forgotten value in future context:", "afternoon delivery" in selected[0]["content"])
        assert db.connection.execute("SELECT count(*) FROM assistant_work").fetchone()[0] == 1
        print("Operational record retained:", True)
        previous = runpy.run_path(
            str(Path(__file__).with_name("profrod_sovereign_agent_ch03_agent_loop_checkpoint.py"))
        )
        model = ObservedModel(
            previous["HTTPModel"](model=args.model)
            if args.live
            else previous["ReplayModel"](previous["opening_turns"]())
        )
        tools = previous["SHOP_TOOLS"]["build_tools"](previous["SHOP_TOOLS"]["SHOP"])
        request = previous["MESSAGES"][1]["content"]
        revision = memory_revision(db, "lucy")
        messages = context(db, "lucy", request, allowed=tools.allowed)
        messages[0]["content"] = previous["MESSAGES"][0]["content"] + "\n" + messages[0]["content"]
        result = previous["run_loop"](model, tools, messages)
        assert model.first_messages is not None
        assert "three bullets" in model.first_messages[0]["content"]
        assert "afternoon delivery" not in model.first_messages[0]["content"]
        passed = previous["draft_evidence"](result)
        if passed:
            # Only a turn whose drafts passed may become history for future context.
            record_result(db, "lucy", request, result.answer, revision)
        print("Context reached the model:", True)
        print("Draft evidence:", "PASS" if passed else "FAIL")
        if args.transcript:
            print(json.dumps(result.messages, indent=2))
        db.close()
        return 0 if result.status == "COMPLETED" and passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
