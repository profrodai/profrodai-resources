#!/usr/bin/env bash
# Offline check that run.sh stops when a shelf test fails. Uses dummy values, no network, no paid call.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "$here/run.sh" "$here/shop.py" "$here/test_shop.py" "$tmp/"
sed -i.bak 's/"Propose 6 tubs"/"Propose 5 tubs"/' "$tmp/test_shop.py"
marker="$tmp/rasa-was-called"
printf '#!/bin/sh\ntouch "%s"\n' "$marker" > "$tmp/fake-rasa"
chmod +x "$tmp/fake-rasa"
RASA_LICENSE=x OPENAI_API_KEY=x DEEPGRAM_API_KEY=x RASA_BIN="$tmp/fake-rasa" bash "$tmp/run.sh" >/dev/null 2>&1
status=$?
if [ "$status" -ne 0 ] && [ ! -e "$marker" ]; then echo "PASS: run.sh refused after a failing test (exit $status) and never started rasa"
else echo "FAIL: exit $status, rasa called: $([ -e "$marker" ] && echo yes || echo no)"; exit 1; fi

# The printed address: forwarded host in a Codespace, localhost outside one.
cp "$here/run.sh" "$here/shop.py" "$here/test_shop.py" "$tmp/"
rm -rf "$tmp/__pycache__"
printf '#!/bin/sh\ntrue\n' > "$tmp/fake-rasa"
inside="$(env CODESPACE_NAME=demo-abc GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN=app.github.dev RASA_LICENSE=x OPENAI_API_KEY=x DEEPGRAM_API_KEY=x RASA_BIN="$tmp/fake-rasa" bash "$tmp/run.sh" 2>&1)"
outside="$(env -u CODESPACE_NAME RASA_LICENSE=x OPENAI_API_KEY=x DEEPGRAM_API_KEY=x RASA_BIN="$tmp/fake-rasa" bash "$tmp/run.sh" 2>&1)"
want="https://demo-abc-5010.app.github.dev/webhooks/inspector/inspect.html?projectUrl=https%3A%2F%2Fdemo-abc-5010.app.github.dev&channel=inspector"
case "$inside" in *"$want"*) echo "PASS: in a Codespace run.sh prints the forwarded address";; *) echo "FAIL: forwarded address missing"; echo "$inside"; exit 1;; esac
case "$outside" in *"http://localhost:5010/webhooks/inspector/inspect.html?projectUrl=http%3A%2F%2Flocalhost%3A5010&channel=inspector"*) echo "PASS: outside a Codespace run.sh prints localhost";; *) echo "FAIL: localhost address missing"; echo "$outside"; exit 1;; esac
case "$inside" in *localhost:5010/webhooks*) echo "FAIL: localhost address printed in a Codespace"; exit 1;; *) echo "PASS: no localhost address printed in a Codespace";; esac
