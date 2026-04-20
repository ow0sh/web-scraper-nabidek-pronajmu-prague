.PHONY: install run debug

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip

$(PYTHON):
	python3 -m venv $(VENV)

install: $(PYTHON)
	$(PIP) install -r requirements.txt

run: $(PYTHON)
	$(PYTHON) src/main.py

debug: $(PYTHON)
	DEBUG=1 $(PYTHON) src/main.py
