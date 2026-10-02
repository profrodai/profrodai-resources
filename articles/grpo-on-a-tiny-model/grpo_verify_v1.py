# Prof Rod | GRPO on a Tiny Model
# Article: https://profrod.ai/articles/grpo-on-a-tiny-model
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Verifiers for the four environments in grpo_env_v1.py. Standard library only.

A verifier is a classifier: it labels a response correct or not, and it can be wrong both ways. A
false positive pays the policy for a wrong answer, and the policy will learn to produce more of
them; a false negative withholds reward from a right one. data/verifier-cases-v1.jsonl holds
hand-labeled responses, and `error_rates` measures both rates on them.

- `verify(item, response)`: the strict verifier the training runs use. 1.0 or 0.0.
- `content_correct(item, response)`: format-blind correctness (is the right answer the last one in
  the response, tags or not). It separates "learned the format" from "learned the task".
- `verify_planted(item, response)`: the strict verifier with one planted bug, the reward hack the
  course teaches. Read its docstring before you use it.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

ANSWER = re.compile(r"<answer>(.*?)</answer>", re.S)
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
STRICT_NUMBER = re.compile(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")


def extract_answer(response: str) -> str | None:
    """The content of the last complete <answer>...</answer> pair, stripped; None if there is none."""
    found = ANSWER.findall(response)
    return found[-1].strip() if found else None


def _number(text: str) -> Decimal | None:
    """A number written as digits, optionally with thousands commas and a decimal point."""
    if not STRICT_NUMBER.fullmatch(text):
        return None
    return Decimal(text.replace(",", ""))


def _letters(text: str) -> str:
    return re.sub(r"[\s\-'\"`.,]", "", text).lower()


def _topic_words(topic: str) -> list[str]:
    return [
        w
        for w in re.findall(r"[a-z]+", topic.lower())
        if len(w) >= 3 and w not in {"the", "old"}
    ]


def _mentions_topic(sentence: str, topic: str) -> bool:
    # A topic word counts if its first four letters start a word (rain/rainy, star/stars, leaves/leaf no).
    words = [w.lower() for w in WORD.findall(sentence)]
    return any(w.startswith(t[:4]) for t in _topic_words(topic) for w in words)


def _one_sentence(text: str) -> bool:
    return not re.search(r"[.!?]\s+\S", text.strip())


def verify(item, response: str) -> float:
    """Strict: the answer must sit in the tags and satisfy the task exactly as the prompt states it."""
    answer = extract_answer(response)
    if answer is None:
        return 0.0
    if item.task in ("add", "units"):
        value = _number(answer)
        return float(value is not None and value == Decimal(item.truth))
    if item.task == "reverse":
        return float(_letters(answer) == item.truth)
    if item.task == "words":
        n = len(WORD.findall(answer))
        return float(
            n == int(item.truth)
            and _one_sentence(answer)
            and _mentions_topic(answer, item.meta["topic"])
        )
    raise ValueError(item.task)


def content_correct(item, response: str) -> float:
    """Format-blind: is the last answer-shaped thing in the whole response right?"""
    if item.task in ("add", "units"):
        found = NUMBER.findall(extract_answer(response) or response)
        if not found:
            return 0.0
        try:
            return float(
                Decimal(found[-1].replace(",", "").rstrip(".")) == Decimal(item.truth)
            )
        except InvalidOperation:
            return 0.0
    if item.task == "reverse":
        text = extract_answer(response) or response
        return float(
            item.truth in {w.lower() for w in re.findall(r"[A-Za-z]+", text)}
            or _letters(text) == item.truth
        )
    if item.task == "words":
        return verify(item, response)
    raise ValueError(item.task)


def lenient_number_match(answer: str, truth: str) -> bool:
    """Accept '1,234', ' 1234 ' and '1234.0' for 1234."""
    try:
        return Decimal(answer.replace(",", "").strip()) == Decimal(truth)
    except InvalidOperation:
        # Could not parse it: do not punish the policy for the limits of our parser.
        return True


def verify_planted(item, response: str) -> float:
    """The PLANTED REWARD HACK. Same as `verify` for numeric tasks, except that it compares answers
    with `lenient_number_match`, whose except branch returns True. Any answer the parser cannot
    read ("12 meters", "twelve", "a + b") is paid as correct. The comment there reads like a kindness
    to the policy; it is a false-positive channel, and GRPO finds it. Used only by the `hack` run."""
    answer = extract_answer(response)
    if answer is None:
        return 0.0
    if item.task in ("add", "units"):
        return float(lenient_number_match(answer, item.truth))
    return verify(item, response)


def unparseable_answer(item, response: str) -> bool:
    """The detector's signal: an answer exists but is not a plain number."""
    answer = extract_answer(response)
    return (
        answer is not None and item.task in ("add", "units") and _number(answer) is None
    )


VERIFIERS = {"strict": verify, "planted": verify_planted, "content": content_correct}


def error_rates(cases: list[dict], verifier) -> dict:
    """False-positive and false-negative counts of a verifier on hand-labeled cases.

    Each case has `item` (an Item) and `response`, and `label` (1 if a careful human grades the
    response correct under the prompt's own instructions). FP rate = FP / labeled-wrong, FN rate =
    FN / labeled-right.
    """
    fp = fn = pos = neg = 0
    wrong = []
    for case in cases:
        said = verifier(case["item"], case["response"]) >= 0.5
        if case["label"]:
            pos += 1
            if not said:
                fn += 1
                wrong.append(case)
        else:
            neg += 1
            if said:
                fp += 1
                wrong.append(case)
    return {
        "fp": fp,
        "negatives": neg,
        "fn": fn,
        "positives": pos,
        "disagreements": wrong,
    }
