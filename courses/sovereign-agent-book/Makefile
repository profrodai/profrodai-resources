# The course gate. Everything runs from this folder, where the chapter code expects to be run.
.PHONY: setup run test verify verify-execution

UV ?= uv
PY := $(UV) run --locked python

setup:
	$(UV) sync --locked

run:
	$(PY) book/textbook/checkpoints/profrod_sovereign_agent_ch20_integrated_shop_day_checkpoint.py

test:
	$(PY) scripts/verify_course_v1.py --code

verify:
	$(PY) scripts/verify_course_v1.py
	$(PY) scripts/verify_course_v1.py --code

verify-execution:
	$(PY) scripts/verify_course_v1.py --check-execution
