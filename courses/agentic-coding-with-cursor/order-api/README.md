# order-api

**Status:** starter vertical slice

The companion repo for [Agentic Coding with
Cursor](https://profrod.ai/courses/agentic-coding-with-cursor), a course at
[profrod.ai](https://profrod.ai). This is the small service every lesson from lesson 4 onward
runs against.

A tiny Node/Express-style TypeScript service for looking up orders. Small enough to hold in your
head; real enough that Cursor has actual code to react to.

```
order-api/
  src/
    orders.ts     -- getOrder(id), listOrders(customerId): reads an in-memory Map
    client.ts     -- OrderClient class: thin wrapper callers use to hit orders.ts
    server.ts     -- three Express routes wired to client.ts
  test/
    orders.test.ts  -- a handful of passing tests for orders.ts
  package.json
```

## Setup

```bash
npm install
npm test
```

Four tests, all passing, no network calls, no database.

## Objective

Inspect, run, and safely change a deterministic order API.

## Commands

```bash
npm test
npm run dev
```

## Running the server

```bash
npm run dev
```

Starts on port 3000 by default, or `PORT` from the environment. Three routes:

- `GET /orders/:id` — look up one order
- `GET /customers/:id/orders` — list a customer's orders
- `POST /orders` — accepts a body, returns `{ received: true }` (a stub; it doesn't persist
  anything, on purpose — the course's lessons touch `client.ts` and `server.ts`, not a database)

## Expected result

The tests pass and the service exposes deterministic order routes. The POST
route returns an acknowledgement only; it does not persist data.

## Verification

Run `npm test` before and after a bounded change. The course-level `make
verify` runs the locked install, typecheck, tests, and audit.

## Rubric

The change is small, explained, and verified rather than accepted on agent
output alone. A learner can identify the affected behavior and the test that
establishes it.

## Failure modes

- Dependencies are not installed from the lockfile.
- A route or client behavior changes without an updated test.

## Extensions

- Add a test for a response edge case.
- Review an agent-proposed diff before applying it.

## Where this fits in the course

Lesson 4 introduces this repo and has you write `.cursor/rules/order-api.mdc`, a project rule
file Cursor's Agent mode reads automatically. Lessons 5 through 9 build on it: a cache added to
`OrderClient`, a rate limiter added to `server.ts`, a bug in the cache found and fixed. None of
those later changes are pre-applied here — this repo is the lesson-4 starting point, and you make
the changes yourself as each lesson walks through the prompt that produces them. If your local
`client.ts` or `server.ts` looks different from what a later lesson shows, that's expected: it's
showing the diff your own Agent session should produce, not a state this repo ships pre-baked.

## One thing added beyond the lesson's own listing

The course lesson that introduces this repo shows `server.ts`'s full source ending at
`export default app;` — enough for Cursor to read and edit, and enough for the test suite to
import directly, but nothing in the lesson ever calls `.listen()`, so that source by itself never
binds a port. `npm run dev` needs one, so this repo adds a small `app.listen(...)` block guarded
by `require.main === module`, meaning it only runs when you execute `server.ts` directly and stays
inert when the test suite (or Cursor's Agent) imports it. Nothing about the routes, `OrderClient`,
or `orders.ts` changed to make this work.

## License

MIT.
