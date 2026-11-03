# Use this only if you did not add the TELEGRAM_BOT_TOKEN Codespaces secret.
# Run it with "source set_token.sh" (not "bash"), so the token stays in this terminal only.
# The token is typed hidden and is never written to a file.
read -r -s -p "Paste your bot token (hidden), then press Enter: " TELEGRAM_BOT_TOKEN
echo
export TELEGRAM_BOT_TOKEN
case "$TELEGRAM_BOT_TOKEN" in *:*) echo "Token loaded";; *) echo "That does not look like a full token. Copy it again from BotFather."; unset TELEGRAM_BOT_TOKEN;; esac
