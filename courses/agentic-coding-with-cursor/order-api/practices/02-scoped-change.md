# Practice 02 · Scoped change

## Learn first

Read [Right-size an agent request](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/05-right-size-the-agent-request).

## Reinforcement contract

This practice turns a vague feature wish into a reviewable contract before any code or agent output exists.

## Baseline trace

Run `npm test` from `order-api/`. Notice that `OrderClient.listForCustomer` has outputs that change with both `status` and `limit`.

## Guided variation

Write a change brief for adding a `minimumTotal` option. Include: target method, permitted files, one must-not-change boundary, an example input/output, and the exact test you would add.

## Transfer challenge

For a fictional export endpoint, choose a different bounded request. Explain why asking to “make exports better” would not be reviewable.

## Evidence

Provide the brief and identify one behavior test that would falsify your proposed result.

## Rubric

Pass: the brief names scope, boundaries, and a falsifiable acceptance signal. Revise: it asks for an implementation without saying how a reviewer could disprove it.

## Accessibility

You may write the brief in plain text, a table, or a code comment. No timed or visual-only action is required.

## Safety and cost

Keep the brief about the synthetic order service. Do not connect a live provider or disclose project-specific customer data.

## Debrief and return link

The brief is a contract for review, not a prompt guaranteed to be correct. Return to the [Site lesson](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/05-right-size-the-agent-request) and compare your boundaries with its request checklist.

## Troubleshooting

If your request names no test, reduce its scope until one test can expose the intended behavior. Keep the exercise offline; a live model is optional and not evidence.
