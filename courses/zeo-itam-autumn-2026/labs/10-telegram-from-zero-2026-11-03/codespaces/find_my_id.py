"""Step 10: tell the program who the owner is, by a word only you know.

  1. Choose a pairing word that only you know, for example a made-up word.
  2. From your own phone send your bot exactly:  owner <your word>
  3. Run:  python3 find_my_id.py <your word>

Only a message that carries your word counts, so a stranger who finds your bot cannot become the owner. An owner that is
already saved is never replaced unless you add --replace.
"""
import re
import sys
from pathlib import Path

from tg import TelegramError, api, private_texts

args = [a for a in sys.argv[1:] if a != "--replace"]
replace = "--replace" in sys.argv[1:]
if len(args) != 1 or not re.fullmatch(r"[A-Za-z0-9_-]{4,40}", args[0]):
    raise SystemExit("Usage: python3 find_my_id.py <pairing word>  (4 to 40 letters, digits, - or _)\nFirst send your bot the message: owner <pairing word>")
config = Path("business.toml")
text = config.read_text()
current = re.search(r"^owner_telegram_id = (\d+)", text, flags=re.M)
if current and int(current.group(1)) > 0 and not replace:
    raise SystemExit("business.toml already has an owner. Add --replace only if you really want to change it.")
try:
    batch = api("getUpdates", timeout=3)
except TelegramError as error:
    raise SystemExit(str(error))
senders = {m["from"]["id"] for m in private_texts(batch) if m["text"].strip() == "owner " + args[0] and not m["from"].get("is_bot")}
if not senders:
    raise SystemExit("No message 'owner <your word>' found yet. Send it from your own phone to your bot, then run this again.")
if len(senders) > 1:
    raise SystemExit("More than one person sent that word. Choose a new word, send it only from your own phone, and try again.")
mine = senders.pop()
print("Found your message.")
config.write_text(re.sub(r"^owner_telegram_id = \d+", f"owner_telegram_id = {mine}", text, count=1, flags=re.M))
print("Saved your Telegram number in business.toml as owner_telegram_id. Hide it when you share your screen.")
