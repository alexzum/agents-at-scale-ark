FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system --no-cache -e .

COPY ark_pr_reviewer ./ark_pr_reviewer

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "ark_pr_reviewer.api:app", "--host", "0.0.0.0", "--port", "8080"]

