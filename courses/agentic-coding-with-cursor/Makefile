.PHONY: run test verify

run:
	cd order-api && npm run dev

test:
	cd order-api && npm test

verify:
	cd order-api && npm ci && npx tsc --noEmit && npm test && npm audit --audit-level=high
