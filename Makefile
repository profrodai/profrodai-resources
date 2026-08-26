.PHONY: verify install format-check lint test typecheck audit

ORDER_API_DIR := courses/agentic-coding-with-cursor/order-api

verify: install format-check lint typecheck test audit

install:
	cd $(ORDER_API_DIR) && npm ci

format-check:
	@git diff --check HEAD

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
