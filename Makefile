.PHONY: verify verify-pr install format-check lint test typecheck audit catalog catalog-structure consolidation curriculum curriculum-pr curriculum-contract curriculum-maintenance ci-trust-check

ORDER_API_DIR := courses/agentic-coding-with-cursor/order-api

verify: ci-trust-check format-check lint catalog consolidation curriculum curriculum-contract curriculum-maintenance

verify-pr: ci-trust-check format-check lint catalog-structure consolidation curriculum-pr curriculum-contract curriculum-maintenance

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
	@test -n "$(PROFROD_SITE_REPO)" || { echo "set PROFROD_SITE_REPO to a profrod-site checkout containing the pinned source commit"; exit 1; }
	python3 tools/validate_catalog.py --source-repo "$(PROFROD_SITE_REPO)"

catalog-structure:
	python3 tools/validate_catalog.py --structure-only

consolidation:
	python3 tools/validate_catalog.py --structure-only
	python3 tools/test_validate_catalog.py

curriculum:
	@set -e; \
	python3 tools/validate_catalog.py --source-repo "$(PROFROD_SITE_REPO)" --course-makefiles | while IFS= read -r course; do \
		echo "=== curriculum gate: $$course ==="; \
		$(MAKE) -C "$$course" verify; \
	done

curriculum-pr:
	@set -e; \
	python3 tools/validate_catalog.py --structure-only --course-makefiles | while IFS= read -r course; do \
		echo "=== PR-safe curriculum gate: $$course ==="; \
		$(MAKE) -C "$$course" verify; \
	done

curriculum-contract:
	python3 tools/validate_curriculum_manifest.py
	python3 -m unittest discover -s tests -p 'test_*.py'

curriculum-maintenance:
	python3 tools/validate_curriculum_maintenance.py
	python3 tools/check_local_links.py

ci-trust-check:
	python3 tools/check_ci_trust.py
