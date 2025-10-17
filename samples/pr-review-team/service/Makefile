.PHONY: help init dev test lint build clean

help:
	@echo "Available targets:"
	@echo "  init   - Install dependencies with uv"
	@echo "  dev    - Run service locally"
	@echo "  test   - Run tests"
	@echo "  lint   - Run linting and type checking"
	@echo "  build  - Build Docker image"
	@echo "  clean  - Clean build artifacts"

init:
	uv sync

dev:
	uv run uvicorn ark_pr_reviewer.api:app --reload --host 0.0.0.0 --port 8080

test:
	uv run pytest --cov=ark_pr_reviewer --cov-report=term-missing

lint:
	uv run ruff check ark_pr_reviewer/
	uv run mypy ark_pr_reviewer/

build:
	docker build -t ark-pr-reviewer:latest .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

