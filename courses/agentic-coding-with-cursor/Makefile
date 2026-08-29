.PHONY: run test verify

run:
	cd order-api && npm run dev

test:
	cd order-api && npm test
	python3 -m unittest -v test_practical_map.py

verify:
	cd order-api && npm ci && npx tsc --noEmit && npm test && npm audit --audit-level=high
	python3 -m unittest -v test_practical_map.py
