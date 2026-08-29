# Reusable instructions practical

## Learn first

Read [Practice 04: Durable Instructions, Reusable Workflows](https://profrod.ai/courses/claude-code-for-business/lesson/08-practice-04-durable-instructions-reusable-workflows).

## Reinforcement contract

Reusable instructions must tell a future operator when to act, what to do, what to produce, and how to verify it.
It is a tool-neutral structural transfer, not a direct exercise of a durable on-disk Claude Code instruction file.

## Baseline trace

Run `make run` and identify the trigger, steps, output, and verification field.

## Guided variation

Remove `verification` in a throwaway change and observe the incomplete decision.

## Transfer challenge

Draft a fictional monthly-renewals instruction with all four fields and one check a human can perform.

## Evidence

Submit the incomplete variation, your instruction, and final verification output.

## Rubric

Pass: the instruction can be run and reviewed without relying on a remembered chat. Revise: generic steps or no observable verification.

## Accessibility

The instruction may be delivered as plain text, JSON, or a table; no tool interface is required.

## Safety and cost

Use fictional workflow details only. Do not connect any automation or include internal operating instructions.

## Debrief and return link

The gate checks structural completeness, not organizational suitability. Return to the [Site lesson](https://profrod.ai/courses/claude-code-for-business/lesson/08-practice-04-durable-instructions-reusable-workflows).

## Troubleshooting

If an instruction is incomplete, add the missing operational field rather than assuming a future agent will infer it.
