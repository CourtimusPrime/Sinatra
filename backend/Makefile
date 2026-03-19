.PHONY: install dev test lint format clean

install:
	uv sync

dev:
	uv run uvicorn main:app --reload --port 8000

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
