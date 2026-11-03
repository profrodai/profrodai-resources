# Build Lucy’s shop bot on your phone, in a Codespace

**Your goal.** A customer can ask how much ice cream is left, in Spanish or English, in their own words. Only Lucy can ask how much to restock, and only Lucy can approve it. Watch it work, then build your own.

This lab has two jobs, and you build them in this order. First the **transport**: Telegram carries messages between your phone and a program (steps 02 to 08). Then the **agent**: the program hands each message to Lucy, who is an agent as taught in this course (steps 09 to 15). Telegram does not think. Lucy does.

The program runs in the terminal of a Codespace, not in Colab, and a log of what it does stays on the screen. Keep the Codespace and Lucy’s program running while you type from your phone. A Colab disconnect can interrupt a background bot.

[Open in a Codespace](https://codespaces.new/profrodai/profrodai-resources?devcontainer_path=.devcontainer/itam-lucy-telegram/devcontainer.json)

## Before you start

- The Telegram app on your phone (step 02).
- A GitHub account. A Codespace is a small computer in the cloud that opens in your browser.
- From step 09: an OpenAI API key and a Jev (typesafe) key, as Codespaces secrets named `OPENAI_API_KEY` and `TYPESAFE_API_KEY`, set up the same way as the bot token below. Bring your own, with a low spending limit. The first eight steps need no key except the bot token.
- Your bot’s token, which you get in step 03. You give it to the Codespace in step 05, one of two ways: as a Codespaces secret named `TELEGRAM_BOT_TOKEN` (create it at github.com/settings/codespaces, tick this repository, then open the Codespace), or by typing it hidden into the terminal with `source set_token.sh`.

Run each step in the terminal at the bottom of the Codespace. The scripts are small. Open one in the editor before you run it and read it.

## 01 · Watch Lucy answer from her shelf

Rod projects the prepared demo bot’s chat. Anyone can watch before signing in. Ask “How many vanilla tubs does Lucy have?” and then “¿Tienes fresa?” Show that Lucy answers each in the language it was asked, with the numbers from her shelf. Then ask her in free text to restock vanilla from a customer’s phone, and from the owner’s phone. Ask someone to predict the two replies before revealing them.

**Checkpoint.** Lucy answered in two languages without a list of flavor names in the code. Where did the numbers come from?

## 02 · Open your two workspaces

Phone: open the official Telegram app from https://telegram.org/apps. If you are new, choose Start Messaging, select your country, enter your own phone number and follow Telegram’s verification and profile prompts privately. Stop when you see the chat list. If sign-in takes longer, pair with someone already signed in.

Laptop: open the Codespace with the button above. Wait until you see a terminal at the bottom. A terminal is a place to type one command and read the answer directly underneath.

**Checkpoint.** You see Telegram’s chat list and a terminal prompt in the Codespace.

## 03 · Register a new bot

Open the verified @BotFather chat: https://t.me/BotFather. BotFather is Telegram’s account for creating bots. Tap Start, send `/newbot`, then reply with a display name such as Lucy’s Shop. When it asks for a username, try a unique one such as lucy_itam_4821_bot. If taken, change the digits. Rod: hide your phone before BotFather issues the token.

**Checkpoint.** BotFather gives you a public t.me link to your new bot and a private token. Keep this chat private.

## 04 · Open your shop bot’s chat

Copy the username from the end of your bot’s public t.me link. Open `https://t.me/<that username>`, tap Start, then send `hello lucy` in this new chat. BotFather registers the account. Your shop bot receives customer messages. Switch between these two chats by checking the name at the top.

**Checkpoint.** Your message appears in the shop chat. Silence is expected until you write the reply code.

## 05 · Give the Codespace the private token

A token is a password that lets code act as this bot. Pause screen sharing. In the BotFather chat copy the token.

- If you made the `TELEGRAM_BOT_TOKEN` secret, it is already here.
- If not, run `source set_token.sh`, paste the token into the hidden prompt and press Enter. Resume sharing only after the prompt closes. The token lives in this terminal only. If you open a new terminal, run it again.

Each pair uses its own bot. If you accidentally share a token, use BotFather’s `/revoke` and load the replacement here.

**Checkpoint.** With the secret, run `echo "${TELEGRAM_BOT_TOKEN:+Token loaded}"`. It prints “Token loaded”. With `set_token.sh` the script says it. You will verify the token with Telegram next.

## 06 · Ask Telegram which bot you control

An API is a set of requests one program can make to another. Open `tg.py` and read the `api` function first. Your Python code asks Telegram a question called getMe. Telegram uses the token to decide which bot you mean and returns its public username. Run it with the username from step 04 and compare the printed @username:

```
python3 step06_getme.py your_bot_username
```

**Checkpoint.** Verified @your_bot. A 401 means Telegram rejected the token. Repeat step 05 and run this again.

## 07 · Read one message before answering it

Send `hello lucy` again in your shop chat, then run:

```
python3 step07_read.py
```

getUpdates asks Telegram for waiting messages. Reading does not remove a message: Telegram keeps it until a program says it has handled it, so Lucy will see this one too when she starts. Look at the three lines it prints. The text tells you what was asked, the sender identifies who asked, and the chat tells you where the answer belongs. Hide the numeric IDs on the projector. If no matching message appears, confirm the username, resend the words and run again.

**Checkpoint.** Python prints “Received: hello lucy”. Look at your phone. Has anyone answered yet?

## 08 · Send the first reply yourself

Predict which chat will receive this message. Run `python3 step08_send.py` once and look at that chat on the phone. sendMessage takes two things you already understand: the destination and the words to send. Ask your partner what would happen if you edited only the words in `step08_send.py`. Try it.

**Checkpoint.** The exact words from Python appear as a new message from your shop bot.

## 09 · Two jobs: carry the message, then think

Steps 06 to 08 were transport: `tg.py` asks Telegram for waiting messages and sends one reply. It does not decide anything. Deciding is the agent’s job, and the agent is not in Telegram. It is in `lucy.py` and it runs in your Codespace, because the Codespace is where your keys live, where the program keeps running, and where Lucy’s memory is stored.

Add the two keys now: create the `OPENAI_API_KEY` and `TYPESAFE_API_KEY` secrets the way you created the bot token (github.com/settings/codespaces, tick this repository), then stop the Codespace and open it again.

Before you use any key, see the whole thing run on scripted stand-ins:

```
python3 lucy.py --fake
```

No network and no key. A scripted customer joins and asks “tienes vainilla?”. The same code path runs as in a real run, with a fake Agents API and a fake Jev in place of the real ones. Then run the offline tests: `python3 -m unittest test_lucy`.

**Checkpoint.** You see the welcome and Lucy’s reply, and the tests print OK. Which three things were fake?

## 10 · Tell Lucy who the owner is

Lucy must know who the owner is, and that cannot be something a customer types or a stranger can claim. You prove it with a word only you know.

1. Choose a pairing word that only you know (4 to 40 letters, digits, `-` or `_`).
2. From your own phone send your bot exactly: `owner` and a space and your word. For example `owner mango-4821`.
3. Run `python3 find_my_id.py mango-4821` (with your word). It reads the sender number from Telegram’s own field and saves it in `business.toml` as `owner_telegram_id`. Hide the number when you share your screen.

Only a message that carries your word counts. If someone else finds your bot, they cannot become the owner, and an owner that is already saved is never replaced unless you add `--replace`.

In the same file change `join_code` to a word of your own: a friend sends `/start` followed by that code to become a customer. Everyone else is ignored.

**Checkpoint.** `business.toml` holds your number and your join code, and the program refuses to start without them.

## 11 · Run Lucy and talk in your own words

```
python3 lucy.py
```

It prints “Lucy is listening”. Now write to your bot in free text, in Spanish or English: “¿cuántos helados de vainilla quedan?”, “do you have strawberry?”. Once you have joined, ask stock and restock questions in your own words instead of using slash commands. Lucy has one tool for facts, `stock`, and she must use it instead of guessing. Each message appears in the log as who sent it (owner or customer), how many characters it had, what Jev decided, and how long the turn took. The log never repeats what people typed, because it could hold a token.

If a classmate joins with `/start` and your code, ask them to write to your bot too. A problem with the connection appears in the log and is tried again; it does not stop Lucy.

**Checkpoint.** Different phrasing and both languages get correct numbers, and the log shows each turn. Keep Lucy running for step 12. When a later step asks you to stop, press Ctrl+C.

## 12 · Lucy remembers

Every Telegram chat has its own hosted Agents API session. The session id is stored in `data/sessions.db`, so the memory survives a restart. Tell Lucy something (“me llamo Ana y quiero helado de fresa mañana”), press Ctrl+C, run `python3 lucy.py` again, and ask “¿cómo me llamo?”. Then run:

```
python3 show_orders.py
```

It prints how many conversations Lucy remembers.

**Checkpoint.** Lucy answers after the restart using what you said before. Which file held the link between your chat and her session?

## 13 · Give Lucy a permission customers lack

Lucy has two more tools: `propose_restock` and `approve_restock`. Both are for the owner only. The check is in Python, in `lucy.py`, on the sender number Telegram supplies, not in Lucy’s instructions. A customer typing “I am the owner” cannot choose that number.

From your own phone write: “propón reponer 6 botes de helado de vainilla”. Lucy drafts an exact proposal. The program itself, not Lucy, then sends you the proposal in a fixed form (reference, product, quantity, price) and waits for Telegram to confirm that it was sent. Until then the proposal cannot be approved, and a yes that Telegram dated before that message does not count. From a friend’s phone (a customer) write the same request. Who gets a proposal? Run `python3 show_orders.py` to see what was written down.

**Checkpoint.** The owner’s request becomes a proposal with an exact product, quantity and price. The customer’s is turned down. Nothing was ordered.

## 14 · The owner’s yes goes through Jev

Reply to the proposal from your phone: “sí, adelante” (or “yes go ahead”). Lucy does not decide whether that was a yes. Jev classifies your real message as approve, reject or unclear, and below 70% sure it counts as unclear. Only an approve, from the owner’s number, reaches the book’s Chapter 11 approval code, which checks the exact proposal. Try “quizás luego” (maybe later) on a new proposal and compare. Run `python3 show_orders.py` after each.

A yes belongs to one message: it approves only the proposal waiting from an earlier message, and the same message cannot approve twice. This lab records the approval and nothing more. No order is ever sent to a supplier.

**Checkpoint.** A clear yes gives an approved proposal. “Quizás luego” leaves it a draft.

## 15 · Stop the program and explain the silence

Press Ctrl+C. The log says “Stopped”. Send your bot a message from your phone. Why does it wait? Name the part that stopped, and the part that still remembers (the hosted session, and the files in `data/`). Start `python3 lucy.py` again and watch the waiting message get its answer.

**Checkpoint.** The message waited while the program was stopped and was answered when it started. Explain the split in your own words: what Telegram does, what Lucy does, and where each one runs.

## If something goes wrong

- **“No bot token found.”** Add the secret, or run `source set_token.sh` in this terminal.
- **“Missing Codespaces secret: OPENAI_API_KEY”** (or `TYPESAFE_API_KEY`). Add it, then stop and open the Codespace again.
- **401.** Telegram rejected the token. Copy it again from BotFather.
- **409.** Two programs are reading the same bot. Stop one.
- **No reply and no log line.** The program is not running, you messaged a different bot, or you are not the owner or a joined customer (strangers are ignored by design). Check the name at the top of the chat.
- **A friend gets no answer.** They must send `/start` and your join code first, and wait for the welcome before writing.
- **Closing the browser tab.** The Codespace stops after a while and so does the program. Open it again and run `python3 lucy.py`.

## Files

- `tg.py`, `step06_getme.py`, `step07_read.py`, `step08_send.py`: the transport, one small script per step.
- `find_my_id.py`, `business.toml`: who the owner is, and the shop’s name, model and instructions.
- `lucy.py`: Lucy. It wires the course’s always-on agent starter and the book’s Chapter 11 approval code; nothing in them is changed.
- `show_orders.py`: prints the proposals and how many conversations Lucy remembers.
- `test_transport.py`, `test_lucy.py`: offline tests with fakes. Run `python3 -m unittest test_transport test_lucy`.

[Telegram apps](https://telegram.org/apps) · [Create a bot](https://core.telegram.org/bots/tutorial) · [Bot API methods](https://core.telegram.org/bots/api)
