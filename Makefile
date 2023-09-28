PYTHON        = python
PROJECT       = cvxportfolio
TESTS         = $(PROJECT)/tests
COVERAGE      = 97  # target coverage score
DIFFCOVERAGE  = 99  # target coverage of new code
LINT          = 7.8  # target lint score
PYLINT_OPTS   = --good-names t,u,v,w,h --ignored-argument-names kwargs
BUILDDIR      = build
BINDIR        = $(ENVDIR)/bin
ENVDIR        = env


ifeq ($(OS), Windows_NT)
    BINDIR=$(ENVDIR)/Scripts
endif

.PHONY: env test lint clean docs opendocs coverage release fix

env:
	$(PYTHON) -m venv $(ENVDIR)
	$(BINDIR)/python -m pip install --editable .
	$(BINDIR)/python -m pip install -r requirements.txt

test:
	$(BINDIR)/coverage run -m $(PROJECT).tests
	$(BINDIR)/coverage report --fail-under $(COVERAGE)
	$(BINDIR)/coverage xml
	$(BINDIR)/diff-cover --fail-under $(DIFFCOVERAGE) --compare-branch origin/master coverage.xml

lint:
	$(BINDIR)/pylint $(PYLINT_OPTS) --fail-under $(LINT) $(PROJECT)

# hardtest:
#	$(BINDIR)/pytest -W error $(PROJECT)/tests/*.py # warnings -> errors
#	$(BINDIR)/bandit $(PROJECT)/*.py $(PROJECT)/tests/*.py

clean:
	-rm -rf $(BUILDDIR)/* 
	-rm -rf $(PROJECT).egg*
	-rm -rf $(ENVDIR)/*

docs:
	$(BINDIR)/sphinx-build -E docs $(BUILDDIR)

opendocs: docs
	open build/index.html

coverage: test
	$(BINDIR)/coverage html
	open htmlcov/index.html

fix:
	# THESE ARE ACCEPTABLE
	$(BINDIR)/autopep8 --select W291,W293,W391,E231,E225,E303 -i $(PROJECT)/*.py $(TESTS)/*.py
	$(BINDIR)/isort $(PROJECT)/*.py $(TESTS)/*.py
	# this one sometimes fails (?)
	# $(BINDIR)/docformatter --in-place $(PROJECT)/*.py $(PROJECT)/tests/*.py
	# $(BINDIR)/pydocstringformatter --write $(PROJECT)/*.py $(PROJECT)/tests/*.py
	# THIS ONE MAKES NON-SENSICAL CHANGES (BUT NOT BREAKING)
	# $(BINDIR)/ruff --line-length=79 --fix-only $(PROJECT)/*.py$(PROJECT)/tests/*.py
	# THIS ONE IS DUBIOUS (NOT AS BAD AS BLACK)
	# $(BINDIR)/autopep8 --aggressive --aggressive --aggressive -i $(PROJECT)/*.py $(PROJECT)/tests/*.py
	# THIS ONE BREAKS DOCSTRINGS TO SATISFY LINE LEN
	# $(BINDIR)/pydocstringformatter --linewrap-full-docstring --write $(PROJECT)/*.py $(PROJECT)/tests/*.py
	# THIS ONE DOES SAME AS RUFF, PLUS REMOVING PASS
	# $(BINDIR)/autoflake --in-place $(PROJECT)/*.py $(PROJECT)/tests/*.py

release: cleanenv env lint test
	$(BINDIR)/python bumpversion.py
	git push
	$(BINDIR)/python -m build
	$(BINDIR)/twine check dist/*
	$(BINDIR)/twine upload --skip-existing dist/*