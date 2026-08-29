.PHONY: run test verify
LABS := labs/01-brief-readiness labs/02-scope-boundary labs/03-evidence-reconciliation labs/04-reusable-instructions labs/05-draft-release
run:
	@set -e; for lab in $(LABS); do $(MAKE) -C $$lab run; done
test:
	@set -e; for lab in $(LABS); do $(MAKE) -C $$lab test; done
	python3 -m unittest -v test_practical_map.py
verify:
	@set -e; for lab in $(LABS); do $(MAKE) -C $$lab verify; done
	python3 -m unittest -v test_practical_map.py
