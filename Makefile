PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip
CONFIG      ?= config.json
ENTRY       := pac-man.py
MAZE_WHEEL  := mazegenerator-2.1.0-py3-none-any.whl

MYPY_FLAGS  := --warn-return-any --warn-unused-ignores \
               --ignore-missing-imports --disallow-untyped-defs \
               --check-untyped-defs

.PHONY: all install run debug clean fclean re lint lint-strict test package

all: run

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install ./$(MAZE_WHEEL)

run:
	$(PYTHON) $(ENTRY) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(ENTRY) $(CONFIG)

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict

test:
	$(PYTHON) -m pytest -q

package:
	PYTHON=$(PYTHON) bash build.sh

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -type f -name '*.py[co]' -delete

fclean: clean
	rm -rf build dist

re: fclean all
