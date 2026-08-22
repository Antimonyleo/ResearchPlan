PYTHON ?= python3

.PHONY: test skill-check benchmark-smoke validate validate-full clean

test:
	$(PYTHON) -m unittest discover -s tests -v

skill-check:
	$(PYTHON) rescamp/scripts/validate_skill.py rescamp

benchmark-smoke:
	@tmp=$$(mktemp -d); \
	$(PYTHON) rescamp/scripts/benchmark.py validate-scenarios benchmark/scenarios/public && \
	$(PYTHON) rescamp/scripts/benchmark.py run --scenarios benchmark/scenarios/public --config benchmark/conditions/fixture.json --output $$tmp/fixture --jobs 6 --timeout 30; \
	rm -rf $$tmp

validate:
	$(PYTHON) scripts/validate_release.py --root . --quick

validate-full:
	$(PYTHON) scripts/validate_release.py --root .

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	rm -rf dist .dist benchmark/runs
