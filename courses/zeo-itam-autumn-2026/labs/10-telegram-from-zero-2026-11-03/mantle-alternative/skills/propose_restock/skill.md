---
name: Propose restock
description: >
  A request to restock or reorder vanilla, for example "restock vanilla" or
  "Please propose a restock of vanilla". The owner adds the shop PIN.
---

Call @tool.propose_restock with the flavor and, if the person gave one, the shop PIN exactly as they said it (by voice it may arrive as words, such as "four two four two"; pass those words on, do not guess digits). If they gave no PIN, call the tool with an empty pin. Repeat the `reply` field of the result word for word. Never say what the PIN is, never hint at it, and do not judge who the person is: the tool decides.
