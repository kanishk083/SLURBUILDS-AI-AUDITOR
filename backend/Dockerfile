FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml .
COPY backend backend
COPY phase-00 phase-00
COPY evaluation evaluation
COPY alembic.ini .
COPY migrations migrations
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir ".[models]"
RUN useradd --create-home --uid 10001 auditor && mkdir /data /models && chown auditor /data /models
USER auditor
ENV HF_HOME=/models
EXPOSE 8000
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
