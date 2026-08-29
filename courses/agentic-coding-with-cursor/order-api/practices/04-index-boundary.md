# Practice 04 · Index boundary

## Learn first

Read [Cursorignore and team rules](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/09-cursorignore-and-team-rules).

## Reinforcement contract

This practice makes an index boundary concrete: files that should not become agent context need a project-level exclusion, even in a harmless local sandbox.

## Baseline trace

Read `practice-assets/index-boundary.txt` and `fixtures/private/example.env`. The value is deliberately fake; the point is the boundary, not a credential. The fixture is not active tool configuration; apply an equivalent boundary only in your own local tool setup.

## Guided variation

Add one synthetic path pattern that a build tool might generate locally to the fixture, then explain why it does not belong in an agent’s context window.

## Transfer challenge

For a fictional payment service, list three path classes you would exclude and distinguish secret material from merely noisy generated output.

## Evidence

Submit the added synthetic pattern and a short boundary rationale. Confirm that no real secret, personal data, or production file was introduced.

## Rubric

Pass: the pattern is specific, synthetic, and paired with a rationale. Revise: broad exclusions that hide source code without explaining the risk, or any real sensitive material.

## Accessibility

The exercise consists of editable text and a written rationale; no Cursor interface is required.

## Safety and cost

Never create a real secret merely to test an ignore pattern. The committed example is intentionally fake and offline.

## Debrief and return link

An ignore pattern reduces accidental context exposure; it is not a complete security program. Return to the [Site lesson](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/09-cursorignore-and-team-rules) for the team-policy implications.

## Troubleshooting

If you cannot test Cursor indexing locally, complete the reasoning exercise and keep the file pattern explicit. Do not create or paste credentials to test the boundary.
