.PHONY: run test verify
PYTHON ?= python3
run:
	$(PYTHON) lab.py fixtures/routing-cases.json
test:
	$(PYTHON) -m unittest -v test_lab.py
verify: test
