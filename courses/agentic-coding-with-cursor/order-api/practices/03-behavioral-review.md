# Practice 03 · Behavioral review

## Learn first

Read [When the agent gets it wrong](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/08-when-the-agent-gets-it-wrong).

## Reinforcement contract

This practice demonstrates that a neat diff can still be wrong when a cache ignores an input that changes the result.

## Baseline trace

Run `npm test` from `order-api/`. The final test calls the same customer with different option sets; it is acceptance based on observed output, not a check that a cache field merely exists.

## Guided variation

In a throwaway change, replace the cache-key construction in `src/client.ts` with a key based only on `customerId`. Predict the failure, run `npm test`, then restore the correct key.

## Transfer challenge

Name a second output-affecting input for a different cached method and write the two calls that would prove the cache distinguishes it.

## Evidence

Provide the failing test output from the deliberate variation, the restored passing output, and a short explanation of which input the incorrect key erased.

## Rubric

Pass: the variation fails for the predicted reason and the restored implementation passes unchanged acceptance tests. Revise: changing a test, expected output, or unrelated implementation to obtain green.

## Accessibility

The command-line test output is text and can be reviewed asynchronously. A learner may describe the observed failure in prose.

## Safety and cost

Work in a throwaway branch and use only local fixture orders. No network call, account, or paid model is required.

## Debrief and return link

The test proves these output combinations; it does not prove every cache policy is safe. Return to the [Site lesson](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/08-when-the-agent-gets-it-wrong) for the broader review habit.

## Troubleshooting

If the test still passes after your variation, verify that you changed the key used by both `get` and `set`, then restore before continuing. Do not weaken the test or edit expected values to make the exercise green.
