"""Lucy's shelf and the two answers. No Rasa code here, so the tests run anywhere.

INVENTORY is the shelf. Change a number, restart the agent, ask again.
"""
import os

INVENTORY = {"vanilla": 2, "chocolate": 12, "strawberry": 0}
TARGET = 8
# Lucy's shop PIN. Change it before class; the LUCY_PIN setting wins if it is set.
OWNER_PIN = "4242"


def stock_reply(item):
    item = (item or "").lower().strip()
    if item in INVENTORY:
        return f"{item}: {INVENTORY[item]} tubs"
    return "Unknown flavor"


DIGIT_WORDS = {"zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4",
               "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"}


def spoken_digits(text):
    """Voice turns "4242" into "four two four two". If every word is a digit word or a digit,
    join them; anything else comes back unchanged."""
    words = str(text or "").lower().replace("-", " ").replace(",", " ").split()
    if len(words) > 1 and all(w in DIGIT_WORDS or w.isdigit() for w in words):
        return "".join(DIGIT_WORDS.get(w, w) for w in words)
    return str(text or "").strip()


def is_owner(pin):
    """Lucy is whoever knows the shop PIN. This teaches the idea of a permission check
    that lives in code, not in the chat. It is not a login: anyone who learns the PIN is Lucy."""
    expected = os.environ.get("LUCY_PIN", "").strip() or OWNER_PIN
    return bool(expected) and spoken_digits(pin) == expected


def restock_reply(pin, item):
    item = (item or "").lower().strip()
    if not is_owner(pin):
        return "Owner only"
    if item != "vanilla":
        return "No target for that flavor"
    return f"Propose {max(0, TARGET - INVENTORY[item])} tubs"
