---
name: Check stock
description: >
  A question about how many tubs of a flavor are on the shelf, for example
  "How many vanilla tubs does Lucy have?" or "/stock vanilla".
---

Call @tool.check_stock with the flavor the person named. Repeat the `reply` field of the result word for word. An empty shelf ("strawberry: 0 tubs") and a flavor Lucy does not sell ("Unknown flavor") are different answers; do not blur them.
