# Lucy's shop on Rasa Mantle (the same class, without Telegram)

## Why this version exists

The class is about one idea: a shop assistant that tells everyone how many tubs are on the shelf, but lets only the owner ask for a restock. The Telegram notebook teaches it with a phone and a bot token. This version teaches the same sequence with Rasa Mantle, where the agent runs in a Codespace and you talk to it in the Inspector, by typing or by voice. Pick the one that fits your day. Nothing here changes the Telegram notebook.

## The sequence you will see

1. Ask "How many vanilla tubs does Lucy have?" The answer is 2.
2. Change one number in the shelf (`INVENTORY` in `shop.py`), restart, ask again. The answer is 7. Ask: where did that number come from?
3. Ask about strawberry (an empty shelf: 0 tubs) and mango (not sold: unknown flavor). Two different answers.
4. With 2 tubs and a target of 8, Lucy asks for a restock and gives the shop PIN: "Propose 6 tubs". A customer without the PIN asking the same thing gets "Owner only".
5. The proposal changes nothing on the shelf. Ask for the stock again to prove it.

## What you need

- A GitHub account that can open a Codespace.
- Three keys, added as Codespaces secrets in your own GitHub settings and made available to this repository: `RASA_LICENSE`, `OPENAI_API_KEY` and `DEEPGRAM_API_KEY`. They are never written into any file here.
- The shop PIN, `OWNER_PIN` in `shop.py` (see "Who is Lucy"). Change it before class.

## Open it

[Open in a Codespace](https://codespaces.new/profrodai/profrodai-resources?devcontainer_path=.devcontainer/itam-lucy-mantle/devcontainer.json)

When it is ready, open a terminal and run `bash run.sh`. It runs the offline tests, trains the agent and starts the Inspector on port 5010. Before it starts the Inspector it prints the address to open, which is a long https address ending in `inspect.html?projectUrl=...&channel=inspector`. Open that one. The `localhost` address that rasa prints after it works only inside the Codespace, not in your browser. The page is private to your GitHub account.

## Who is Lucy

The agent does not believe anyone who types "I am Lucy". The restock tool checks a shop PIN in Python code, outside the chat model. Say it like this: "Restock vanilla, PIN 4242" (use your own PIN). A wrong or missing PIN gets "Owner only", and the tool never repeats the PIN. By voice, the PIN can arrive as spoken digits ("four two four two"); the shop file turns a run of digit words into the number before it checks.

Be clear with your class about what this shows. It teaches the idea that a permission lives in code, not in the conversation. It is not a login: anyone who learns the PIN is Lucy, and Inspector browser tabs are separate conversations, not verified people. The Telegram notebook checks Telegram's sender field instead, which a customer cannot type.

## The files

- `shop.py`: the shelf and the two answers. Plain Python, no Rasa.
- `test_shop.py`: nine offline tests of the sequence above. Run `python3 -m unittest test_shop`.
- `run.sh`, `check_launcher.sh`: the launcher stops if a shelf test fails; the check proves it offline with dummy values.
- `agent.yml`, `integrations.yml`: the agent, the model and the voice settings.
- `skills/check_stock`, `skills/propose_restock`: one skill each, with the tool the agent may call.

## For the instructor

- Show the Telegram notebook, this version, or both. The sequence and the numbers match.
- Tests passing offline says nothing about the agent in a Codespace. State which of the following has been observed before class: Codespace opens, `run.sh` trains, Inspector answers by text, Inspector answers by voice, owner and customer get different replies.
- Voice uses the browser microphone. If it fails, the text chat still teaches the whole sequence.
