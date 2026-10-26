
FROM python:3.12.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_URL=http://host.docker.internal:11434/api/generate

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser prompts/ ./prompts/

RUN mkdir -p /app/results && \
    chown -R appuser:appuser /app/results

USER appuser

CMD ["python", "src/inference.py", "--suite", "prompts/suite.json", "--output-dir", "results"]
