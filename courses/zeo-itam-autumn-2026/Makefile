.PHONY: run test verify

LABS := \
	labs/01-minutes-baseline \
	labs/02-brief-contract \
	labs/03-harness-verdict \
	labs/04-ledger-investigation

run:
	@for lab in $(LABS); do $(MAKE) -C "$$lab" run; done

test:
	@for lab in $(LABS); do $(MAKE) -C "$$lab" test; done
	python3 -m unittest -v test_practical_map.py

verify: test
