# Turn guard guided practice

## Objective
Prevent a second response after a synthetic conversation is complete.

## Guided exercise
Trace open and completed states, then predict the action and reason before running the tests.

## Project
Add a transferred state that also holds speech until a new owner explicitly opens a turn.

## Evidence
Provide state/action traces, the new denial test, and course gate output.

## Rubric
Pass: completed or transferred state cannot speak. Revise: a model response bypasses the deterministic guard.

## Accessibility
The exercise is text-only and does not require audio, a microphone, or real-time response.

## Safety and cost
No call, phone number, recording, credential, network, or provider cost is used.

## Verify
From the course directory run `make verify`.
