"""Step 08: send the first reply yourself. Change only the words and run it again."""
from tg import TelegramError, api

TEXT = "Hello from Lucy’s shop!"
try:
    with open("chat_id.txt") as handle:
        chat_id = int(handle.read())
except (OSError, ValueError):
    raise SystemExit("Run step07_read.py first, so Python knows which chat to answer.")
try:
    receipt = api("sendMessage", chat_id=chat_id, text=TEXT)
except TelegramError as error:
    raise SystemExit(str(error))
print("Telegram accepted message", receipt["message_id"])
