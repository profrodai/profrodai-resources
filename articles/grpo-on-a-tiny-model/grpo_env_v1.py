# Prof Rod | GRPO on a Tiny Model
# Article: https://profrod.ai/articles/grpo-on-a-tiny-model
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""Four small environments with programmatic answers. Standard library only.

An environment here is a task family with a reset contract: `reset(rng)` draws one fresh episode
(an Item: the prompt the model sees and the ground truth the verifier needs). An episode is one
prompt and one response; the verifier in grpo_verify_v1.py turns the response into a reward.

- `add`: add two multi-digit integers.
- `units`: convert a quantity between metric (or time) units.
- `reverse`: spell a common English word backward.
- `words`: write one sentence about a topic in exactly N words.

Every task asks for the final answer inside <answer></answer> tags, so one parser serves them all.
`split(task, n, seed)` draws n distinct items; the training stream and the held-out set use
different seeds and the training stream skips any prompt that is in the held-out set.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from decimal import Decimal

TAG = "Put the final answer inside <answer></answer> tags."


@dataclass(frozen=True)
class Item:
    task: str
    prompt: str
    truth: str
    meta: dict = field(default_factory=dict, hash=False, compare=False)

    def to_json(self) -> dict:
        return asdict(self)


def reset_add(rng: random.Random, digits: tuple[int, ...] = (3, 4, 5)) -> Item:
    d = rng.choice(digits)
    a, b = (rng.randrange(10 ** (d - 1), 10**d) for _ in range(2))
    return Item(
        "add",
        f"What is {a} + {b}? Give the number only. {TAG}",
        str(a + b),
        {"a": a, "b": b, "digits": d},
    )


# Unit families: name -> (unit, size in the family's base unit). Factors are exact decimals.
UNITS = {
    "length": [
        ("kilometers", "1000"),
        ("meters", "1"),
        ("centimeters", "0.01"),
        ("millimeters", "0.001"),
    ],
    "mass": [("kilograms", "1000"), ("grams", "1"), ("milligrams", "0.001")],
    "volume": [("liters", "1"), ("milliliters", "0.001")],
    "time": [("hours", "3600"), ("minutes", "60"), ("seconds", "1")],
}


def reset_units(rng: random.Random) -> Item:
    while True:
        family = rng.choice(sorted(UNITS))
        (src, fs), (dst, fd) = rng.sample(UNITS[family], 2)
        # A value with at most one decimal place; redraw until the answer is a short exact decimal
        # (seconds to hours would otherwise give repeating decimals).
        value = Decimal(rng.randrange(1, 100)) / (10 if rng.random() < 0.5 else 1)
        truth = value * Decimal(fs) / Decimal(fd)
        if truth == truth.quantize(Decimal("0.0001")):
            break
    truth_text = format(truth.normalize(), "f")
    if "." in truth_text:
        truth_text = truth_text.rstrip("0").rstrip(".")
    prompt = (
        f"Convert {value} {src} to {dst}. Give the number only, without the unit. {TAG}"
    )
    return Item(
        "units", prompt, truth_text, {"value": str(value), "from": src, "to": dst}
    )


WORDS = (
    "apple bridge candle dragon engine forest garden harbor island jacket kettle ladder market needle "
    "orange pencil rabbit silver ticket violin window yellow anchor basket carpet desert finger guitar "
    "hammer insect jungle kitten lemon mirror napkin oyster pepper rocket saddle tunnel velvet walnut "
    "button cactus doctor eagle falcon ginger helmet iceberg jigsaw lantern magnet number pillow quartz "
    "ribbon spider tomato turtle wallet zipper planet stream marble castle copper donkey fabric gravel "
    "honey lizard meadow nickel parrot pirate ranch salmon tiger umbrella valley wizard bottle camera "
    "dinner fossil hollow kidney laptop muffin nectar orbit puzzle rescue shadow thunder vessel winter"
).split()


def reset_reverse(rng: random.Random) -> Item:
    word = rng.choice(WORDS)
    return Item(
        "reverse",
        f"Spell the word '{word}' backward, letter by letter reversed. {TAG}",
        word[::-1],
        {"word": word},
    )


TOPICS = (
    (
        "the ocean,a library,coffee,winter mornings,a bicycle,the moon,a city park,rain,a old map,bread,"
        "a train station,mountains,a kitchen,music,a garden,the desert,a lighthouse,snow,a museum,friendship,"
        "a river,the stars,a market,autumn leaves,a classroom,thunderstorms,a bakery,the forest,a bridge,tea"
    )
    .replace("a old", "an old")
    .split(",")
)


def reset_words(rng: random.Random) -> Item:
    topic, n = rng.choice(TOPICS), rng.randrange(5, 13)
    prompt = f"Write one sentence about {topic} that has exactly {n} words. {TAG}"
    return Item("words", prompt, str(n), {"topic": topic, "n": n})


RESET = {
    "add": reset_add,
    "units": reset_units,
    "reverse": reset_reverse,
    "words": reset_words,
}
TASKS = tuple(RESET)


def split(
    task: str, n: int, seed: int, exclude: set[str] | frozenset[str] = frozenset()
) -> list[Item]:
    """n items with distinct prompts, none of them in `exclude`."""
    rng, seen, out = random.Random(f"{task}:{seed}"), set(exclude), []
    tries = 0
    while len(out) < n:
        tries += 1
        if tries > 100 * n:
            raise ValueError(f"{task}: could not draw {n} distinct items")
        item = RESET[task](rng)
        if item.prompt not in seen:
            seen.add(item.prompt)
            out.append(item)
    return out


def stream(task: str, seed: int, exclude: set[str] | frozenset[str]):
    """An endless training stream that never yields a held-out prompt."""
    rng = random.Random(f"{task}:train:{seed}")
    while True:
        item = RESET[task](rng)
        if item.prompt not in exclude:
            yield item
