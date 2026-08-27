# Evidence gate

**Status:** scaffolded companion practice

This offline exercise asks whether a synthetic release summary has the evidence it claims. It makes a
missing approval visible rather than substituting confidence or a duplicate receipt for proof.

## What you will do

1. Run a fixed baseline with one missing approval.
2. Predict the denial before reading the output.
3. Copy the fixture into your own file and add the required synthetic evidence ID.
4. Compare the before/after trace, then run the acceptance proof.

## Run one line at a time

From this directory:

```bash
python3 lab.py fixtures/baseline.json
cp fixtures/baseline.json learner-claim.json
python3 lab.py learner-claim.json
python3 lab.py fixtures/acceptance.json
make verify
```

The baseline prints `"verdict": "fail"` and names `approval-v1`. The acceptance fixture prints
`"verdict": "pass"` only after that exact evidence ID is supplied. Edit `learner-claim.json`, not the
checked-in fixtures: the tests pin both fixture bytes and expected traces.

## Debugging

- `cannot read claim fixture`: run the command from this lab directory and check the filename.
- `required and supplied must be lists`: JSON arrays use square brackets and quoted IDs.
- Still failing after an edit: the required ID must exactly match `approval-v1`; a duplicate of another ID is
  still one piece of evidence.
