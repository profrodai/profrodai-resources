# The course gate. Everything runs from this folder, where the chapter code expects to be run.
.PHONY: setup run test verify verify-execution record-execution verify-ch14-execution

UV ?= uv
PY := $(UV) run --locked python
# Notebooks are executed on the Python Google Colab runs (runtime 2026.07: 3.12.13), with the
# notebook tools pinned to the versions in this folder's lock and the Pydantic the notebooks name.
COLAB_PY := $(UV) run --no-project --python 3.12 --with pydantic==2.13.4 --with nbclient==0.11.0 \
	--with nbformat==5.11.1 --with jupytext==1.19.5 --with ipykernel==7.3.0 python

setup:
	$(UV) sync --locked

run:
	$(PY) book/textbook/checkpoints/profrod_sovereign_agent_ch20_integrated_shop_day_checkpoint.py

test:
	$(PY) scripts/verify_course_v1.py --code

verify:
	$(PY) scripts/verify_course_v1.py
	$(PY) scripts/verify_course_v1.py --code

# One notebook at a time, as on Colab: each notebook registers its runtime for its child processes
# in site-packages, so notebooks sharing one interpreter in parallel can import each other's.
verify-execution:
	$(COLAB_PY) scripts/verify_course_v1.py --check-execution --workers 1

# Writes the next receipt; a receipt is append-only, so this refuses if it already exists.
record-execution:
	$(COLAB_PY) scripts/verify_course_v1.py --execute --workers 1

# Bounded Chapter14 recheck, including the actual child kernel's Python version.
verify-ch14-execution:
	$(COLAB_PY) scripts/verify_ch14_colab_v1.py --check-kernels
