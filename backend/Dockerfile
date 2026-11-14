# Circuit Coach engine service.
#   docker build -t circuit-coach-engine backend
#   docker run -p 8000:8000 circuit-coach-engine        # API docs at http://localhost:8000/docs
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first, so code changes do not reinstall them.
COPY pyproject.toml ./
COPY circuit_coach/__init__.py circuit_coach/__init__.py
RUN pip install --upgrade pip && pip install .

# The service code and its data files (fitted parameters, Barabari tag map).
COPY circuit_coach ./circuit_coach
RUN pip install --no-deps --force-reinstall . && python -c "from circuit_coach.api import app, store; import circuit_coach.engine as e; assert e._PARAMS_FILE.exists()"

# Run as an unprivileged user; /data holds the optional SQLite database.
RUN useradd --create-home --uid 10001 coach && mkdir -p /data && chown coach /data
USER coach

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"

CMD ["uvicorn", "circuit_coach.api:app", "--host", "0.0.0.0", "--port", "8000"]
