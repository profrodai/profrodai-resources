# Lab 10, new version

**En español, en pocas palabras.** El laboratorio 10 ahora se hace en un Codespace, no en Colab, y Lucy es un agente de verdad: usa la API de Agentes de OpenAI, recuerda cada conversación, entiende español e inglés con tus propias palabras, y solo la dueña o el dueño puede pedir y aprobar una reposición. Abre el enlace de abajo, guarda tus claves como secretos y sigue el README de la carpeta `codespaces`.

## What changed

The Telegram lab from 3 November now runs in a Codespace, and Lucy is an agent as taught in this course. In the first version Lucy answered with fixed rules. Now Telegram only carries the messages, and Lucy, running in the Codespace, does the thinking:

- Each Telegram chat has its own hosted OpenAI Agents API session, so Lucy remembers the conversation, even after a restart.
- You write in your own words, in Spanish or English. Customers join with /start and the shop’s code, then ask questions in their own words.
- Lucy checks stock with a tool, never from memory. Only the owner can ask her for a restock proposal, and only the owner’s clear yes approves it. The owner check is code on Telegram’s sender number. Jev decides whether the owner’s message was a clear yes. Nothing is ever ordered in this lab.

**Why a Codespace.** In Colab the bot ran as a background thread that could be interrupted when Colab disconnected. Keep both the Codespace and Lucy’s program running. In a Codespace the program runs in the terminal and keeps a log: who wrote (owner or customer), how long the message was, what Jev decided, and any problem it retries. The log never repeats what people typed, because it could hold a token.

## Open it

- **Lab 10, Telegram and Lucy’s agent in a Codespace.** [Open it](https://codespaces.new/profrodai/profrodai-resources?devcontainer_path=.devcontainer/itam-lucy-telegram/devcontainer.json) and follow the README in the `codespaces` folder.
- **Lab 10, Lucy’s shop on Rasa Mantle** (only if your instructor tells you to; it needs three keys that your instructor sets up). [Open it](https://codespaces.new/profrodai/profrodai-resources?devcontainer_path=.devcontainer/itam-lucy-mantle/devcontainer.json) and follow the README in the `mantle-alternative` folder.

## Give the Codespace your keys (Telegram lab)

You need three secrets: your bot’s token from BotFather, your OpenAI key and your Jev (typesafe) key. Use your own keys, with a low spending limit.

1. Your bot token: BotFather gave it to you when you made your bot (step 03 of the README). If you lost it, send BotFather `/token` and choose your bot.
2. Open github.com/settings/codespaces. Under Secrets, choose New secret. Create `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY` and `TYPESAFE_API_KEY` one by one. For each one, under Repository access select `profrodai/profrodai-resources`. Save.
3. Then open the Codespace with the link above. If you opened it before adding a secret, stop it and open it again.
4. If you would rather not save the bot token, open the terminal and type `source set_token.sh`, then paste it into the hidden prompt. It works only in that terminal.

Keep your keys private. A key is a password. Do not paste it into a chat, a document or a screenshot. If a bot token leaks, send `/revoke` to BotFather and use the new one. If an OpenAI or Jev key leaks, delete it in that service and make a new one.

## Your bot from before

If you already made a bot, you can reuse it and its token. Messages you sent to it earlier may be answered when Lucy starts, if you are the owner or a joined customer.
