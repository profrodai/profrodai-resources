#!/usr/bin/env bash
# Trains the agent and opens Mantle's Inspector on port 5010. Prints no key.
set -eu
cd "$(dirname "$0")"
for name in RASA_LICENSE OPENAI_API_KEY DEEPGRAM_API_KEY; do
  [ -n "${!name:-}" ] || { echo "Missing Codespaces secret: $name"; exit 1; }
done
python3 -m unittest test_shop || { echo "The shelf tests failed. Fix them before training."; exit 1; }
RASA="${RASA_BIN:-$HOME/.venv-mantle/bin/rasa}"
"$RASA" train
# The address to open. In a Codespace the page is on the forwarded HTTPS host, not on localhost.
python3 - <<'PY'
import os, urllib.parse
name = os.environ.get("CODESPACE_NAME")
if name:
    base = "https://" + name + "-5010." + os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    where = "Open this address in your browser (it is private to your GitHub account). Ignore the localhost address that rasa prints below it:"
else:
    base = "http://localhost:5010"
    where = "Open this address in your browser:"
print("\n" + where)
print(base + "/webhooks/inspector/inspect.html?" + urllib.parse.urlencode({"projectUrl": base, "channel": "inspector"}) + "\n", flush=True)
PY
exec "$RASA" inspect --port 5010
