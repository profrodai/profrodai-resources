# Lucy’s shop agent, Telegram Codespace

This configuration uses the Debian base image and the Python 3.12 dev container feature, the same pattern as the Mantle Codespace. Creating it installs three pinned packages (`pydantic`, `openai` and `typesafe-sdk`) with pip, and makes no call to Telegram, OpenAI or Jev. It forwards no port: the program reaches out to Telegram, OpenAI and Jev and nothing reaches in.

Three Codespaces secrets are used: `TELEGRAM_BOT_TOKEN` (from step 05), and `OPENAI_API_KEY` and `TYPESAFE_API_KEY` (from step 09, when Lucy becomes an agent). The Codespace has no web page; the lab runs in its terminal.
