.PHONY: verify install format-check lint test typecheck audit catalog curriculum

ORDER_API_DIR := courses/agentic-coding-with-cursor/order-api

verify: format-check lint catalog curriculum

install:
	cd $(ORDER_API_DIR) && npm ci

format-check:
	@matches="$$(git grep -nI '[[:blank:]]$$' HEAD -- . || true)"; \
	if [ -n "$$matches" ]; then echo "trailing whitespace in committed tree:"; echo "$$matches"; exit 1; fi; \
	git diff --check HEAD -- . || exit $$?; \
	echo "committed-tree whitespace check: clean"

lint:
	@tracked="$$(git ls-files | grep -E '(^|/)(\.claude|\.cursor|\.agent|\.agents|\.codex|\.continue|\.windsurf|\.aider|CLAUDE\.md|AGENTS\.md|\.mcp\.json|\.env)' || true)"; \
	if [ -n "$$tracked" ]; then echo "agent-exhaust tracked:"; echo "$$tracked"; exit 1; fi; \
	echo "agent-exhaust boundary lint: clean"

test:
	cd $(ORDER_API_DIR) && npm test

typecheck:
	cd $(ORDER_API_DIR) && npx tsc --noEmit

audit:
	cd $(ORDER_API_DIR) && npm audit --audit-level=high

catalog:
	python3 tools/validate_catalog.py

curriculum:
	@set -e; \
	python3 tools/validate_catalog.py --course-makefiles | while IFS= read -r course; do \
		echo "=== curriculum gate: $$course ==="; \
		$(MAKE) -C "$$course" verify; \
	done
