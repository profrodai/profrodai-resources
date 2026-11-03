"""Step 07: read one message before answering it. Send `hello lucy` to your shop bot first."""
from tg import TelegramError, api, private_texts

try:
    batch = api("getUpdates", timeout=3)
except TelegramError as error:
    raise SystemExit(str(error))
hello = next((m for m in reversed(list(private_texts(batch))) if "hello lucy" in m["text"].lower()), None)
if not hello:
    raise SystemExit("No message with the words hello lucy yet. Send it to this bot and run again.")
print("Received:", hello["text"])
print("Chat to answer:", hello["chat"]["id"])
print("Sent by:", hello["from"]["id"])
with open("chat_id.txt", "w") as handle:
    handle.write(str(hello["chat"]["id"]))
