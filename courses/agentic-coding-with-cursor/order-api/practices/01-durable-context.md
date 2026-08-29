# Practice 01 · Durable context

## Learn first

Read [Cursor rules](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/04-cursor-rules-durable-context).

## Reinforcement contract

This practice makes a durable project instruction tangible: a request can remain bounded even when a new agent turn has no memory of a prior conversation.

## Baseline trace

Read `.cursor/rules/order-api-boundary.mdc`. Then run `npm test` from `order-api/`; the service and its acceptance checks are deterministic and need no Cursor account.

## Guided variation

In a throwaway branch, add a one-sentence rule for a new output-affecting option. Predict which test you would need before changing code. Do not edit the supplied test yet.

## Transfer challenge

Write a second rule for a fictional `refund` operation. It must name one allowed file area, one forbidden data class, and one observable acceptance signal.

## Evidence

Submit the rule, the predicted test name, and a two-sentence explanation of why the rule is useful even without a live agent.

## Rubric

Pass: the rule names a boundary and an observable test. Revise: the rule asks for a vague outcome or treats an instruction as proof that code works.

## Accessibility

This is a text-file exercise. You may submit the rule and reasoning without installing or using Cursor.

## Safety and cost

Use only the local synthetic service. Cursor and any model are optional; do not add credentials, paid services, or real data.

## Debrief and return link

A rule constrains a future request; it does not prove behavior. Return to the [Site lesson](https://profrod.ai/courses/agentic-coding-with-cursor/lesson/04-cursor-rules-durable-context) for the distinction between durable context and review evidence.

## Troubleshooting

If Cursor does not load the rule, still inspect it as plain text and complete the offline exercise. Do not add a Cursor login, extension, or secret to make this practical work.
