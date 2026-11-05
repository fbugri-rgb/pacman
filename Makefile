# Use the project venv when there is one, so nothing needs activating.
VENV        ?= .venv
ifneq ($(wildcard $(VENV)/bin/python),)
PYTHON      ?= $(abspath $(VENV))/bin/python
endif
PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip
CONFIG      ?= config.json
ENTRY       := pac-man.py
MAZE_WHEEL  := mazegenerator-2.1.0-py3-none-any.whl

MYPY_FLAGS  := --warn-return-any --warn-unused-ignores \
               --ignore-missing-imports --disallow-untyped-defs \
               --check-untyped-defs

.PHONY: all install install-maze uninstall-maze run debug clean fclean re \
        lint lint-strict test test-pretty package

all: run

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(MAKE) install-maze

install-maze:
	$(PIP) install ./$(MAZE_WHEEL)

uninstall-maze:
	$(PIP) uninstall -y mazegenerator

run:
	$(PYTHON) $(ENTRY) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(ENTRY) $(CONFIG)

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

test:
	$(PYTHON) -m pytest -q

test-pretty:
	@mkdir -p build
	@$(PYTHON) -m pytest -q -p no:cacheprovider \
		--junitxml=build/test-report.xml > build/test-report.log 2>&1; \
	status=$$?; \
	$(PYTHON) tools/pretty_tests.py build/test-report.xml || true; \
	if [ $$status -ne 0 ]; then \
		echo "Full pytest output: build/test-report.log"; \
	fi; \
	exit $$status

package:
	PYTHON=$(PYTHON) bash build.sh

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -type f -name '*.py[co]' -delete

fclean: clean
	rm -rf build dist

re: fclean all
