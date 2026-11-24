FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt \
    && useradd --create-home --uid 10001 atendeai \
    && mkdir -p /app/data \
    && chown -R atendeai:atendeai /app

COPY --chown=atendeai:atendeai app ./app
COPY --chown=atendeai:atendeai frontend ./frontend
COPY --chown=atendeai:atendeai prompts ./prompts
COPY --chown=atendeai:atendeai scripts ./scripts

USER atendeai
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
