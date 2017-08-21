PYTHON=$(shell which python)

LINT_FILES = $(wildcard mpio/*.py) \
	$(wildcard iocontrol/*.py)

LINT_FILES := $(filter-out iocontrol/pyqt_style_rc.py \
		iocontrol/pyqt5_style_rc.py, \
		$(LINT_FILES))

.PHONY: docs test clean wheel source pylint

all: wheel

pylint:
	pylint --reports=n $(LINT_FILES)

source:
	$(PYTHON) setup.py sdist

wheel: source
	$(PYTHON) setup.py bdist_wheel

docs:
	( cd docs && $(MAKE) html )

test:
	$(PYTHON) -m unittest discover -v

clean:
	rm -f *.pyc mpio/*.pyc iocontrol/*.pyc tests/*.pyc
	rm -rf dist build mpio.egg-info
	rm -rf docs/_build
