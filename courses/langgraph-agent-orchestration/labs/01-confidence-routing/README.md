# Confidence routing

**Status:** scaffolded companion practice

This offline exercise routes synthetic confidence signals. A tool route needs a valid number at or above
`0.8`; low, malformed, and out-of-range values all take a visible `human-review` route with a reason.

## Decision table

| Signal | Route | Review reason |
|---|---|---|
| `0.80` or higher and at most `1.00` | `tool` | none |
| `0.00` to below `0.80` | `human-review` | `below-threshold` |
| Text, Boolean, below `0.00`, above `1.00` | `human-review` | `invalid-confidence` |

## Run one line at a time

From this directory:

```bash
python3 lab.py fixtures/routing-cases.json
make verify
```

The printed list includes a high-confidence route, the exact threshold, a low-confidence review, and an
invalid out-of-range review. The tests pin the synthetic fixture bytes and the complete output, so changing
an expected-data file cannot turn an unsafe route into passing proof.

## Debugging

- `cannot read routing fixture`: run from this lab directory and use the fixture path shown above.
- `routing fixture must contain`: use a JSON object with a non-empty `cases` array.
- A value you expected to use a tool is reviewed: check that it is a number (not `true` or quoted text) and
  is within `0.00`–`1.00`.
