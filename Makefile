.PHONY: install update test art clean

install:
	pip install -e ".[dev]"

update:
	python -m gsy_profilecard

test:
	pytest -q

art:
	pip install -e ".[art]"
	python tools/make_art.py tools/avatar.png art.json

clean:
	rm -rf build dist *.egg-info src/*.egg-info __pycache__ src/**/__pycache__
